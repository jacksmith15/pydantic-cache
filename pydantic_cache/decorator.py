import inspect
import json
from collections.abc import Callable
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from typing import ParamSpec, TypeVar

from pydantic import PydanticSchemaGenerationError, TypeAdapter
from pydantic_core import to_jsonable_python

from pydantic_cache.backend import Backend, DiskBackend


class PydanticCacheError(Exception):
    pass


Params = ParamSpec("Params")
Return = TypeVar("Return")


def cache(backend: Backend) -> Callable[[Callable[Params, Return]], Callable[Params, Return]]:
    def decorator(function: Callable[Params, Return]) -> Callable[Params, Return]:
        function_signature = inspect.signature(function)
        if function_signature.return_annotation is inspect._empty:
            raise PydanticCacheError("Decorated function must have a return type annotation")

        try:
            result_adapter = TypeAdapter(function_signature.return_annotation)
        except PydanticSchemaGenerationError as exc:
            raise PydanticCacheError(
                f"Function return type {function_signature.return_annotation} does not support serialization with "
                "Pydantic"
            ) from exc

        def get_key(*args: Params.args, **kwargs: Params.kwargs) -> str:
            return sha256(
                json.dumps(
                    function_signature.bind(*args, **kwargs).arguments,
                    default=to_jsonable_python,
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest()

        def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
            key = get_key(*args, **kwargs)
            if backend.exists(key):
                return result_adapter.validate_python(json.loads(backend.get(key)))
            result = function(*args, **kwargs)
            backend.write(key, json.dumps(result, default=to_jsonable_python))
            return result

        return wrapper

    return decorator


def disk_cache(path: Path, ttl: timedelta) -> Callable[[Callable[Params, Return]], Callable[Params, Return]]:
    backend = DiskBackend(path, ttl)
    return cache(backend)
