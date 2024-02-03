import re
import subprocess
from pathlib import Path
from typing import Callable, List, Tuple

import requests
from changelog import dump_to_file as write_changelog
from changelog import load_from_file as load_changelog
from changelog.model import Bump, Changelog, ReleaseTag
from invoke import task
from invoke.exceptions import Exit
from termcolor import cprint

from tasks.helpers import package

RELEASE_BRANCH = "main"

PACKAGE_FILE = str(Path(package.__file__).relative_to(Path(__file__).parent.parent.absolute()))


@task
def publish(ctx, tag: str = "auto", bump: str = "auto") -> None:
    _validate_branch(ctx)
    changelog = load_changelog()
    if not has_untagged_changes(changelog):
        cprint("❌ No unreleased changes in changelog.", "red")
        raise Exit(code=1)
    previous_tag, new_tag = cut_release(changelog, tag=tag, bump=bump)
    cprint(
        f"ℹ️ Pushing new release commit ({previous_tag} -> {new_tag}).",
        "blue",
    )
    tag_release(ctx, new_tag)
    changelog = load_changelog()
    if not changelog.latest_tag or already_published(changelog.latest_tag):
        cprint("✅ Already up-to-date.", "green")
        return
    cprint(f"🚀 Publishing version {changelog.latest_tag}")
    publish_release(ctx, changelog.latest_tag)


def has_untagged_changes(changelog: Changelog) -> bool:
    unreleased = changelog.releases[ReleaseTag("Unreleased")]
    return bool(unreleased.entries)


def cut_release(changelog: Changelog, tag: str = "auto", bump: str = "auto") -> Tuple[str, str]:
    previous_tag: str = changelog.latest_tag or "unknown"
    new_tag, release_content = changelog.cut_release(
        force=None if bump == "auto" else Bump[bump],  # type: ignore
        tag=None if tag == "auto" else tag,  # type: ignore
    )

    write_changelog(changelog)

    update_file(
        PACKAGE_FILE,
        lambda content: re.sub(
            r'__version__ *= *".*"',
            f'__version__ = "{new_tag}"',
            content,
        ),
    )

    update_file(
        "pyproject.toml",
        lambda content: re.sub(
            r'^version *= *".*"',
            f'version = "{new_tag}"',
            content,
            flags=re.MULTILINE,
            count=1,
        ),
    )
    return previous_tag, str(new_tag)


def tag_release(ctx, tag: str) -> None:
    files: List[str] = [
        "CHANGELOG.md",
        "pyproject.toml",
        PACKAGE_FILE,
    ]
    ctx.run(f"git commit -i {' '.join(files)} -m {tag}")
    ctx.run(f"git push origin {RELEASE_BRANCH}")
    ctx.run(f"git tag -a {tag} -m {tag}")
    ctx.run(f"git push origin {tag}")
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            tag,
            "--latest",
            "--verify-tag",
            "--title",
            tag,
            "--notes",
            f"[Release Notes](https://github.com/jacksmith15/pydantic-cache/blob/{tag}/CHANGELOG.md)",
        ],
        check=True,
    )


def update_file(path: str, processor: Callable[[str], str]):
    with open(path, "r") as file:
        content = processor(file.read())
    with open(path, "w") as file:
        file.write(content)


def already_published(tag: ReleaseTag) -> bool:
    response = requests.get(
        "https://pypi.org/simple/pydantic-cache",
        headers={"Accept": "application/vnd.pypi.simple.v1+json"},
    )
    if response.status_code == 404:
        return False
    response.raise_for_status()
    body = response.json()
    versions = body["versions"]
    if str(tag) in versions:
        return True
    return False


def publish_release(ctx, tag: ReleaseTag) -> None:
    ctx.run("poetry build")
    ctx.run("poetry publish")


def _validate_branch(ctx) -> None:
    branch = ctx.run("git branch --show-current", hide=True).stdout.strip()
    if branch != RELEASE_BRANCH:
        raise Exit(code=1, message=f"You are not on the release branch: {branch!r}")
