"""Create the required code directory hierarchy for the project.

This script ensures that the following directories exist under the project
root's ``code`` folder:

- src/lib/
- src/metrics/
- src/experiment/
- src/analysis/
- tests/

For each package directory a minimal ``__init__.py`` file is created so that
the directories are recognised as Python packages. The script can be run
directly::

    python code/create_code_structure.py

It is safe to run multiple times; existing directories and files are left
untouched.
"""
import os
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Create a directory if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)

def create_init_file(package_path: Path) -> None:
    """Create an empty ``__init__.py`` file if it does not exist."""
    init_file = package_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()

def main() -> None:
    # Base ``src`` directory relative to this script
    src_base = Path(__file__).parent / "src"

    # Sub‑packages to create
    sub_packages = ["lib", "metrics", "experiment", "analysis"]
    for sub in sub_packages:
        pkg_path = src_base / sub
        ensure_directory(pkg_path)
        create_init_file(pkg_path)

    # Create the top‑level ``tests`` package
    tests_path = Path(__file__).parent / "tests"
    ensure_directory(tests_path)
    create_init_file(tests_path)

    print("Code directory structure created successfully.")

if __name__ == "__main__":
    main()
