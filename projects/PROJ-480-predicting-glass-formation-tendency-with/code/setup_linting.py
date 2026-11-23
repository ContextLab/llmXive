"""Configure linting (Ruff, flake8-compatible) and formatting (Black) tools.

Task T003: creates/updates ``pyproject.toml`` with ``[tool.ruff]`` and
``[tool.black]`` configuration sections and adds linting-related entries
to ``.gitignore``. Extends an existing ``pyproject.toml`` rather than
replacing it.
"""

import os
import sys
from pathlib import Path

RUFF_SECTION = """[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.format]
quote-style = "double"
"""

BLACK_SECTION = """[tool.black]
line-length = 100
target-version = ["py311"]
include = '\\.pyi?$'
extend-exclude = '''(
    /(
        \\eggs
      | \\.git
      | \\.venv
      | venv
      | build
      | dist
    )/
)'
"""

GITIGNORE_ENTRIES = [
    "# Linting / formatting caches (T003)",
    ".ruff_cache/",
    ".mypy_cache/",
]


def create_pyproject_config(root: Path) -> None:
    """Create or update pyproject.toml with Ruff and Black configuration.

    Args:
        root: The project root directory.
    """
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
    else:
        text = ""

    if "[tool.ruff]" not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n" + RUFF_SECTION
    if "[tool.black]" not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n" + BLACK_SECTION

    pyproject.write_text(text, encoding="utf-8")
    print(f"Updated {pyproject} with Ruff and Black configuration.")

def create_gitignore_entries(root: Path) -> None:
    """Add linting and formatting related entries to .gitignore.

    Args:
        root: The project root directory.
    """
    gitignore = root / ".gitignore"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
    else:
        text = ""

    missing = [e for e in GITIGNORE_ENTRIES if e not in text]
    if missing:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n" + "\n".join(missing) + "\n"
        gitignore.write_text(text, encoding="utf-8")
        print(f"Updated {gitignore} with linting cache entries.")
    else:
        print(f"{gitignore} already contains linting entries.")

def main() -> None:
    root = Path(__file__).resolve().parent.parent
    create_pyproject_config(root)
    create_gitignore_entries(root)
    print("Linting (Ruff) and formatting (Black) configuration complete.")

if __name__ == "__main__":
    main()
