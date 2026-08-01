"""
setup_project_structure.py

This script creates the required project directory hierarchy for the
PROJ-236-exploring-the-influence-of-network-topol project.

Execution
----------
Running the module as a script (``python -m code.setup_project_structure``)
will create the following directories relative to the repository root:

    projects/PROJ-236-exploring-the-influence-of-network-topol/
        code/utils
        code/tests/unit
        code/tests/integration
        data/raw
        data/networks
        data/transport
        data/analysis
        plots
        state/projects

The script is idempotent – existing directories are left untouched.
"""

import os
from pathlib import Path

# Base directory for the project structure
BASE_PROJECT_PATH = Path("projects") / "PROJ-236-exploring-the-influence-of-network-topol"

# List of sub‑directories to create (relative to BASE_PROJECT_PATH)
SUBDIRS = [
    "code/utils",
    "code/tests/unit",
    "code/tests/integration",
    "data/raw",
    "data/networks",
    "data/transport",
    "data/analysis",
    "plots",
    "state/projects",
]


def create_directories(base_path: Path = BASE_PROJECT_PATH, subdirs=SUBDIRS) -> None:
    """
    Create the directory hierarchy required for the project.

    Parameters
    ----------
    base_path : pathlib.Path
        The root of the project hierarchy.
    subdirs : list[str]
        Relative directory names to be created under ``base_path``.
    """
    for rel_dir in subdirs:
        dir_path = base_path / rel_dir
        # ``parents=True`` creates any missing parent directories;
        # ``exist_ok=True`` makes the operation a no‑op if the directory already exists.
        dir_path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    Entry point for the script.

    Creates the directory tree and prints a short confirmation message.
    """
    create_directories()
    print(f"Project structure created under '{BASE_PROJECT_PATH}'.")
    # Optionally list the created directories for easy debugging
    for path in sorted((BASE_PROJECT_PATH).rglob("*")):
        if path.is_dir():
            print(f"  - {path}")


if __name__ == "__main__":
    main()