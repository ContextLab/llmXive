"""
code/create_project_tree.py
---------------------------

Implements task T001: create a separate project directory tree with placeholder
``.gitkeep`` files and an empty ``__init__.py`` in the top‑level ``code`` package.

The required tree (relative to the repository root) is:

projects/PROJ-001-assessing-statistical-power/
    code/
        __init__.py
        utils/
    data/
        raw/
        processed/
    tests/
        unit/
        integration/
    docs/
    contracts/

Each directory receives an empty ``.gitkeep`` so that Git tracks empty folders.
The script is idempotent – running it multiple times does not raise errors and
leaves the tree in the desired state.
"""

import sys
from pathlib import Path

def _create_dir_with_gitkeep(dir_path: Path) -> None:
    """Create a directory (including parents) and a ``.gitkeep`` file inside."""
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep = dir_path / ".gitkeep"
    gitkeep.touch(exist_ok=True)

def _create_init_file(dir_path: Path) -> None:
    """Create an empty ``__init__.py`` file inside the given directory."""
    init_file = dir_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()

def main() -> int:
    """Entry point for the script.

    Returns
    -------
    int
        0 on success, non‑zero on unexpected failure.
    """
    # Repository root is two levels above the ``projects`` folder that contains
    # the current project (i.e. ``.../projects/PROJ-234-.../code`` -> repo root).
    # The desired new project lives under ``projects/PROJ-001-assessing-statistical-power``.
    repo_root = Path(__file__).resolve().parents[3]   # <repo_root>
    target_root = repo_root / "projects" / "PROJ-001-assessing-statistical-power"

    subdirs = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs",
        "contracts",
    ]

    try:
        for sub in subdirs:
            sub_path = target_root / sub
            _create_dir_with_gitkeep(sub_path)

        # Ensure the empty ``__init__.py`` inside the top‑level ``code`` package.
        _create_init_file(target_root / "code")
    except Exception as exc:  # pragma: no cover – unexpected errors should surface.
        print(f"Error while creating project tree: {exc}", file=sys.stderr)
        return 1

    print(f"Project tree created under: {target_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())