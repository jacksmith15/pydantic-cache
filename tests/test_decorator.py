import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel

from pydantic_cache import DiskBackend, PydanticCacheError, cache, disk_cache


class TestDiskCache:
    @staticmethod
    def should_cache_primitive_results_to_disk(tmp_path: Path) -> None:
        # GIVEN a function which caches results to disk
        side_effect = 0

        @disk_cache(path=tmp_path, ttl=timedelta(days=1))
        def my_function(a: int, b: list[str], c: dict | None = None) -> dict:
            nonlocal side_effect
            side_effect += 1
            return {"a": a * 2, "b": list(reversed(b)), "c": c}

        # AND the function has already been invoked
        result = my_function(3, ["1", "2", "3"], c={"foo": "bar"})
        assert result == {"a": 6, "b": ["3", "2", "1"], "c": {"foo": "bar"}}

        # WHEN I invoke the function with the same arguments
        cached_result = my_function(3, ["1", "2", "3"], c={"foo": "bar"})

        # THEN the result is the same
        assert result == cached_result

        # BUT the side effect did not trigger
        assert side_effect == 1

        # AND the function provides a different result with different arguments
        assert my_function(4, ["1", "2"], c={"qux": "mux"}) == {"a": 8, "b": ["2", "1"], "c": {"qux": "mux"}}

    @staticmethod
    def should_cache_datetimes(tmp_path: Path) -> None:
        # GIVEN a function with datetimes in the argument and return value
        side_effect = 0

        @disk_cache(path=tmp_path, ttl=timedelta(days=1))
        def my_function(timestamp: datetime) -> datetime:
            nonlocal side_effect
            side_effect += 1
            return timestamp + timedelta(days=1)

        # WHEN I invoke the function twice with the same argument
        timestamp = datetime.now()
        expected = timestamp + timedelta(days=1)

        # THEN the result should be serialized/deserialized as expected
        assert my_function(timestamp) == expected
        assert my_function(timestamp) == expected

        # AND the side effect should only trigger once
        assert side_effect == 1

    @staticmethod
    def should_cache_models(tmp_path: Path) -> None:
        # GIVEN a function with pydantic models in the argument and return value
        side_effect = 0

        class ChildModel(BaseModel):
            value: int

        class ParentModel(BaseModel):
            children: list[ChildModel]

        @disk_cache(path=tmp_path, ttl=timedelta(days=1))
        def my_function(a: ChildModel, b: ChildModel) -> ParentModel:
            nonlocal side_effect
            side_effect += 1
            return ParentModel(children=[a, b])

        # WHEN I invoke the function twice with the same arguments
        args = [ChildModel(value=1), ChildModel(value=2)]
        expected = ParentModel(children=args)

        # THEN the result should serialized/deserialized as expected
        assert my_function(*args) == expected
        assert my_function(*args) == expected

        # AND the side effect should only trigger once
        assert side_effect == 1

    @staticmethod
    def should_respect_ttl(tmp_path: Path) -> None:
        # GIVEN a function with a short ttl
        side_effect = 0

        @disk_cache(path=tmp_path, ttl=timedelta(microseconds=1))
        def my_function(value: int) -> int:
            nonlocal side_effect
            side_effect += 1
            return value * 2

        # WHEN I invoke the function twice, with longer interval than the TTL
        assert my_function(2) == 4
        time.sleep(0.001)
        assert my_function(2) == 4

        # THEN the side effect should be triggered twice
        assert side_effect == 2

    @staticmethod
    def should_support_no_arguments(tmp_path: Path) -> None:
        # GIVEN a function with no arguments
        side_effect = 0

        @disk_cache(path=tmp_path, ttl=timedelta(days=1))
        def my_function() -> bool:
            nonlocal side_effect
            side_effect += 1
            return True

        # WHEN I invoke the function twice
        assert my_function() is True
        assert my_function() is True

        # THEN the side_effect should only be triggered once
        assert side_effect == 1

    @staticmethod
    def should_fail_gracefully_on_missing_type_annotation(tmp_path: Path) -> None:
        with pytest.raises(PydanticCacheError) as exc_info:

            @disk_cache(tmp_path, ttl=timedelta(days=1))
            def my_function():
                return True

        assert str(exc_info.value) == "Decorated function must have a return type annotation"

    @staticmethod
    def should_fail_gracefully_on_unsupported_type_annotation(tmp_path: Path) -> None:
        class CustomType:
            pass

        with pytest.raises(PydanticCacheError) as exc_info:

            @disk_cache(tmp_path, ttl=timedelta(days=1))
            def my_function() -> CustomType:
                return CustomType()

        assert "does not support serialization with Pydantic" in str(exc_info.value)


class TestCache:
    @staticmethod
    def should_allow_deferring_backend_resolution(tmp_path: Path) -> None:
        # GIVEN a function with deferred cache backend resolution
        side_effect = 0

        @cache(backend=lambda: DiskBackend(tmp_path, ttl=timedelta(days=1)))
        def my_function(value: int) -> int:
            nonlocal side_effect
            side_effect += 1
            return value * 2

        # WHEN I invoke the function twice
        assert my_function(3) == 6
        assert my_function(3) == 6

        # THEN the side effect should only be triggered once
        assert side_effect == 1
