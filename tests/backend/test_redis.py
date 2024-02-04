from datetime import timedelta

from fakeredis import FakeRedis

from pydantic_cache import cache
from pydantic_cache.backend import RedisBackend


class TestRedisBackend:
    @staticmethod
    def should_cache_results_in_redis():
        # GIVEN a function which caches results to redis:
        side_effect = 0
        redis = FakeRedis()

        @cache(backend=RedisBackend(redis, ttl=timedelta(days=1)))
        def my_function(value: str) -> list[str]:
            nonlocal side_effect
            side_effect += 1
            return list(value)

        # WHEN I invoke the function twice
        assert my_function("foo") == ["f", "o", "o"]
        assert my_function("foo") == ["f", "o", "o"]

        # THEN the side effect should only trigger once
        assert side_effect == 1
