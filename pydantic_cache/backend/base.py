class Backend:
    def get(self, key: str) -> str:
        raise NotImplementedError  # pragma: no cover

    def write(self, key: str, value: str) -> None:
        raise NotImplementedError  # pragma: no cover
