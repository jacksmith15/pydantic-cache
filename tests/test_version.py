import changelog
import toml

import pydantic_cache as package


class TestVersion:
    @staticmethod
    def should_match_pyproject() -> None:
        with open("pyproject.toml", "r") as file:
            pyproject = toml.loads(file.read())
        assert pyproject["tool"]["poetry"]["version"] == package.__version__

    @staticmethod
    def should_match_changelog() -> None:
        log = changelog.load_from_file("CHANGELOG.md")
        if log.latest_tag:
            assert log.latest_tag == package.__version__
