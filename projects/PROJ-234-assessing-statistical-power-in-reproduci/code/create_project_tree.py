"""Create the required project directory tree with placeholder .gitkeep files.

This script is part of task T001. When executed it creates the following
structure relative to the repository root:

projects/PROJ-001-assessing-statistical-power/
    code/
        utils/
    data/
        raw/
        processed/
    tests/
        unit/
        integration/
    docs/
    contracts/

Each directory receives an empty ``.gitkeep`` file so that version control
tracks empty folders. The script is idempotent – running it multiple times
does not raise errors and will leave the tree in the desired state.
"""

import sys
from pathlib import Path

def _create_dir_with_gitkeep(dir_path: Path) -> None:
    """Create a directory (including parents) and a ``.gitkeep`` file inside."""
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep = dir_path / ".gitkeep"
    # ``touch`` creates the file if it does not exist; ``exist_ok`` avoids
    # overwriting an existing file.
    gitkeep.touch(exist_ok=True)

def main() -> int:
    """Entry point for the script.

    Returns
    -------
    int
        0 on success, non‑zero on unexpected failure.
    """
    # Base directory for the new project tree.
    base = Path(__file__).resolve().parents[1] / "projects" / "PROJ-001-assessing-statistical-power"

    # Define the sub‑directories that must exist.
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
            _create_dir_with_gitkeep(base / sub)
    except Exception as exc:  # pragma: no cover – unexpected errors should surface.
        print(f"Error while creating project tree: {exc}", file=sys.stderr)
        return 1

    print(f"Project tree created under: {base}")
    return 0

if __name__ == "__main__":
    sys.exit(main())