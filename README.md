# Pydantic Cache

Cache results of Python functions, with support for serialization of rich data types powered by [Pydantic](https://docs.pydantic.dev/latest/).

Supports caching to disk by default, but additional caching backends can easily be added.

## Example

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

In the above example, subsequent calls to the function with the same argument will fetch the results from the cache on disk. Serialization and deserialization is handled based on the function's type annotations.

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

### TODOs

- [ ] `asyncio` support
- [ ] Redis back-end

# License

This project is distributed under the MIT license.
