import json
from datetime import datetime, timedelta
from pathlib import Path


class Backend:
    def get(self, key: str) -> str:
        raise NotImplementedError  # pragma: no cover

    def write(self, key: str, value: str) -> None:
        raise NotImplementedError  # pragma: no cover


class DiskBackend(Backend):
    def __init__(self, directory: Path | str, ttl: timedelta) -> None:
        self.directory = Path(directory)
        self.ttl = ttl

    def get(self, key: str) -> str:
        path = self.directory / f"{key}.json"
        if not path.exists():
            raise KeyError(key)
        content = json.loads(path.read_text(encoding="utf-8"))
        timestamp = datetime.fromisoformat(content["timestamp"])
        if datetime.now() - timestamp > self.ttl:
            raise KeyError(key)
        return content["value"]

    def write(self, key: str, value: str) -> None:
        path = self.directory / f"{key}.json"
        timestamp = datetime.now()
        path.write_text(
            json.dumps(
                {
                    "timestamp": timestamp.isoformat(),
                    "value": value,
                }
            )
        )
