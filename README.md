# Pydantic Cache

Cache results of Python functions, with support for serialization of rich data types powered by [Pydantic](https://docs.pydantic.dev/latest/).

Supports caching to disk or Redis by default, but additional caching backends can easily be added.

## Examples

### Basic usage

You can use any [data types which can be serialized by Pydantic](https://docs.pydantic.dev/latest/concepts/types/), both in the function signature (cache key) and the returned values:

```python
from datetime import datetime, timedelta
from pydantic import BaseModel
from pydantic_cache import disk_cache

class MyModel(BaseModel):
    a: int
    b: datetime
    d: set[datetime]


@disk_cache(path="~/.cache/my-function", ttl=timedelta(days=1))
def my_function(date: datetime) -> list[MyModel]:
    return []  # Some expensive computation
```

In the above example, subsequent calls to the function with the same argument will fetch the results from the cache on disk. Serialization and deserialization are handled based on the function's type annotations.

### Redis support

The library includes support for caching results to/from redis. This depends on [redis](https://pypi.org/project/redis/), which can be installed via `pip install pydantic-cache[redis]`.

```python
from datetime import timedelta
from pydantic_cache import cache
from pydantic_cache.backend import RedisBackend
from redis import Redis

redis = Redis(...)

@cache(RedisBackend(redis, ttl=timedelta(days=1)))
def my_function() -> dict:
    return {}
```

### Custom cache backends

You can implement custom cache backends by sub-classing `Backend`:

```python
from pydantic_cache import Backend, cache


class MemoryBackend(Backend):
    def __init__(self) -> None:
        # Optional initial set-up of the backend.
        self._cache: dict[str, str] = {}

    def get(self, key: str) -> str:
        # Implement cache retrieval here.
        # Cache misses should raise a KeyError.
        return self._cache[key]

    def write(self, key: str, value: str) -> None:
        # Write to the cache here.
        self._cache[key] = value


@cache(backend=MemoryBackend)
def my_function() -> dict:
    return {}
```

> [!NOTE]
> Cache backends only interact with serialized data, so the `str` types above will apply for all backends.

### Deferred backend resolution

Some backends may rely on reading configurations or creating connections to external services, which is best avoided at import time. To support this, the `cache` decorator optionally accepts a callable which returns the backend, instead of the backend itself.

```python
from datetime import timedelta
from pathlib import Path
from pydantic_cache import DiskBackend, cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cache_ttl: timedelta
    cache_path: Path


def get_cache_backend() -> DiskBackend:
    settings = Settings()
    return DiskBackend(settings.cache_path, ttl=settings.cache_ttl)


@cache(backend=get_cache_backend)
def my_function() -> dict:
    return {}
```

### `asyncio` support

Asynchronous functions are supported by default, however using a synchronous backend will naturally result in blocking calls:

```python
import asyncio
from pydantic_cache import DiskBackend, cache

@cache(backend=DiskBackend(...))
async def my_function() -> dict:
    return await asyncio.sleep(0, {})
```

To avoid blocking IO calls in the cache backend, you can implement an asynchronous backend as a subclass of `AsyncBackend`. See the following example using `aioredis`:

```python
import asyncio
import aioredis
from pydantic_cache import AsyncBackend, cache


class AioRedisBackend(AsyncBackend):
    def __init__(self, redis: aioredis.Client) -> None:
        self.redis = redis

    async def get(self, key: str) -> str:
        result = await self.redis.get(key)
        if result is None:
            raise KeyError(key)
        return result

    async def write(self, key: str, value: str) -> None:
        await self.redis.set(key, value)


@cache(backend=AioRedisBackend(...))
async def my_function() -> dict:
    return await asyncio.sleep(0, {})
```

## Installation

This project is not currently packaged and so must be installed manually.

Clone the project with the following command:

```
git clone https://github.com/jacksmith15/pydantic-cache.git
```

## Development

Install dependencies:

```shell
pyenv shell 3.10.x
pre-commit install  # Configure commit hooks
poetry install  # Install Python dependencies
```

Run tests:

```shell
poetry run inv verify
```

# License

This project is distributed under the MIT license.
