"""Create the repository skeleton required for the project.

This script ensures that the top‑level directories required by the
specification exist:

- src
- tests
- data
- results
- docs
- contracts

For ``src`` and ``tests`` an ``__init__.py`` file is added so that they are
recognised as Python packages. Minimal placeholder files are added to
``docs`` and ``contracts`` to make the directories non‑empty (helpful for
version‑control tools and for the repository‑skeleton verification tests).

The script is idempotent – running it repeatedly will not modify existing
files or raise errors.
"""

import sys
from pathlib import Path

# List of top‑level directories that must exist.
REQUIRED_DIRS = [
    "src",
    "tests",
    "data",
    "results",
    "docs",
    "contracts",
]


def _ensure_dir(path: Path) -> None:
    """Create *path* (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def _touch_file(path: Path, content: str = "") -> None:
    """Create *path* if it does not exist and optionally write *content*."""
    if not path.exists():
        path.write_text(content)


def main() -> int:
    """
    Entry point for the skeleton‑creation script.

    Returns
    -------
    int
        Exit code – ``0`` for success, non‑zero for unexpected errors.
    """
    try:
        project_root = Path(__file__).resolve().parents[1]  # ``code/`` → project root
        for dirname in REQUIRED_DIRS:
            dir_path = project_root / dirname
            _ensure_dir(dir_path)

            # Add minimal placeholder files where appropriate.
            if dirname == "src":
                _touch_file(dir_path / "__init__.py")
            elif dirname == "tests":
                _touch_file(dir_path / "__init__.py")
            elif dirname == "docs":
                _touch_file(dir_path / "README.md", "# Documentation\n")
            elif dirname == "contracts":
                _touch_file(dir_path / "placeholder.schema.yaml", "# Placeholder schema\n")
    except Exception as exc:  # pragma: no cover – any failure should be visible.
        print(f"Error creating repository skeleton: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())