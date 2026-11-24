"""
T001 - Create the project directory tree and placeholder .gitkeep files.

This script creates the following directory structure relative to the repository root:

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

Each directory contains a ``.gitkeep`` file to ensure it is tracked by git.
"""

import sys
from pathlib import Path

def create_dir_with_gitkeep(path: Path) -> None:
    """
    Create a directory (including parents) and place a .gitkeep file inside it.
    If the directory already exists, ensure the .gitkeep file exists.
    """
    path.mkdir(parents=True, exist_ok=True)
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()

def main() -> None:
    """
    Build the required project scaffold under ``projects/PROJ-001-assessing-statistical-power``.
    """
    # Base directory for the new project
    base = Path(__file__).resolve().parents[1] / "projects" / "PROJ-001-assessing-statistical-power"

    # Define the directory tree (directories only)
    structure = {
        "code": {
            "utils": {}
        },
        "data": {
            "raw": {},
            "processed": {}
        },
        "tests": {
            "unit": {},
            "integration": {}
        },
        "docs": {},
        "contracts": {}
    }

    def recurse(parent: Path, tree: dict) -> None:
        for name, subtree in tree.items():
            child = parent / name
            create_dir_with_gitkeep(child)
            if isinstance(subtree, dict):
                recurse(child, subtree)

    # Create the scaffold
    recurse(base, structure)

    print(f"Project scaffold created at: {base}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error while creating project scaffold: {e}", file=sys.stderr)
        sys.exit(1)