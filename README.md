# Pydantic Cache

Caching decorator with Pydantic support.

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
