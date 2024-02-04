import typing
from datetime import timedelta

if typing.TYPE_CHECKING:
    from redis import Redis  # pragma: no cover

from pydantic_cache.backend.base import Backend


class RedisBackend(Backend):
    def __init__(self, redis: "Redis", ttl: timedelta):
        self.redis = redis
        self.ttl = ttl

    def get(self, key: str) -> str:
        result = self.redis.get(key)
        if result is None:
            raise KeyError(key)
        return result

    def write(self, key: str, value: str) -> None:
        self.redis.set(key, value, ex=self.ttl)
