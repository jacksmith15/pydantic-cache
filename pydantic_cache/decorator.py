import asyncio
import inspect
import json
from collections.abc import Callable
from datetime import timedelta
from functools import wraps
from hashlib import sha256
from pathlib import Path
from typing import ParamSpec, TypeVar

from pydantic import PydanticSchemaGenerationError, TypeAdapter
from pydantic_core import to_jsonable_python

from pydantic_cache.backend import AsyncBackend, Backend, DiskBackend


class PydanticCacheError(Exception):
    pass


Params = ParamSpec("Params")
Return = TypeVar("Return")


def cache(
    backend: Backend | AsyncBackend | Callable[[], Backend | AsyncBackend]
) -> Callable[[Callable[Params, Return]], Callable[Params, Return]]:
    def get_backend() -> Backend | AsyncBackend | AsyncBackend:
        if isinstance(backend, (Backend, AsyncBackend)) or not callable(backend):
            return backend
        return backend()

    def decorator(function: Callable[Params, Return]) -> Callable[Params, Return]:
        if isinstance(backend, AsyncBackend) and not asyncio.iscoroutinefunction(function):
            raise PydanticCacheError("Can't use an async cache backend on a synchronous function.")
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

        if asyncio.iscoroutinefunction(function):

            @wraps(function)
            async def wrapper(*args, **kwargs):
                backend = get_backend()
                key = get_key(*args, **kwargs)
                if isinstance(backend, AsyncBackend):
                    try:
                        return result_adapter.validate_python(json.loads(await backend.get(key)))
                    except KeyError:
                        result = await function(*args, **kwargs)
                        await backend.write(key, json.dumps(result, default=to_jsonable_python))
                        return result
                try:
                    return result_adapter.validate_python(json.loads(backend.get(key)))
                except KeyError:
                    result = await function(*args, **kwargs)
                    backend.write(key, json.dumps(result, default=to_jsonable_python))
                    return result

        else:

            @wraps(function)
            def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
                backend = get_backend()
                if isinstance(backend, AsyncBackend):
                    raise PydanticCacheError("Can't use an async cache backend on a synchronous function.")
                key = get_key(*args, **kwargs)
                try:
                    return result_adapter.validate_python(json.loads(backend.get(key)))
                except KeyError:
                    result = function(*args, **kwargs)
                    backend.write(key, json.dumps(result, default=to_jsonable_python))
                    return result

        return wrapper

    return decorator


def disk_cache(path: Path | str, ttl: timedelta) -> Callable[[Callable[Params, Return]], Callable[Params, Return]]:
    backend = DiskBackend(path, ttl)
    return cache(backend)
