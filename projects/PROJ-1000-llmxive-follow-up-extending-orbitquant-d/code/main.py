"""
Main entry point for the project skeleton initialization.

This script creates the required sub‑directories under ``code/`` and
writes a marker ``__init__.py`` file in each of them so they are recognised
as Python packages. It is invoked by the quick‑start guide via:

    python -m code.main --phase init

The script prints ``Initialization complete`` on success, which is
asserted by the verification command.
"""
import argparse
from pathlib import Path

def _ensure_package_dir(parent: Path, name: str) -> None:
    """Create a sub‑directory and an ``__init__.py`` marker."""
    dir_path = parent / name
    dir_path.mkdir(parents=True, exist_ok=True)
    init_file = dir_path / "__init__.py"
    init_file.touch(exist_ok=True)

def _create_code_subdirs() -> None:
    """Create all required ``code/`` sub‑directories."""
    base_dir = Path(__file__).parent
    subdirs = [
        "analysis",
        "models",
        "quantization",
        "evaluation",
        "utils",
        "runners",
        "validation",
        "security",
    ]
    for sub in subdirs:
        _ensure_package_dir(base_dir, sub)

def main() -> None:
    parser = argparse.ArgumentParser(description="Project skeleton initializer")
    parser.add_argument(
        "--phase",
        choices=["init"],
        required=True,
        help="Initialization phase to run",
    )
    args = parser.parse_args()

    if args.phase == "init":
        _create_code_subdirs()
        print("Initialization complete")

if __name__ == "__main__":
    main()
