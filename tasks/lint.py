from typing import cast

from invoke import Collection, Task, task
from termcolor import cprint

from tasks.helpers import package, print_header

_SOURCE_DIRECTORIES = " ".join(
    [
        package.__name__,
        "tasks",
        "tests",
    ]
)

lint = Collection("lint")


@task
def check(ctx):
    """Run linter on source code and tests.

    A non-zero return code from this task indicates invalid code was discovered.
    """
    print_header("RUNNING LINTER")

    print_header("pyflakes", level=2)
    ctx.run(f"pyflakes {_SOURCE_DIRECTORIES}")
    # pyflakes doesn't give positive output
    cprint("✔ No issues found.", "green")

    print_header("autoflake", level=2)
    ctx.run(f"autoflake --check-diff --recursive {_SOURCE_DIRECTORIES}")

    print_header("isort", level=2)
    ctx.run(f"isort --check --diff {_SOURCE_DIRECTORIES}")
    # isort doesn't give positive output
    cprint("✔ No issues found.", "green")

    print_header("black", level=2)
    ctx.run(f"black --check --diff {_SOURCE_DIRECTORIES}")


@task
def fix(ctx):
    print_header("FIXING LINTER ERRORS")

    ctx.run(f"autoflake --in-place {_SOURCE_DIRECTORIES}")

    ctx.run(f"isort {_SOURCE_DIRECTORIES}")

    ctx.run(f"black {_SOURCE_DIRECTORIES}")


lint.add_task(cast(Task, check), default=True)
lint.add_task(cast(Task, fix))
