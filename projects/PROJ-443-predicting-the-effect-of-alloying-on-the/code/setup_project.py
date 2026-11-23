"""
Project setup script.

Creates the required top‑level directory scaffold for the project
and ensures that the ``code/requirements.txt`` file exists.
This script is intended to be run via ``python -m code.setup_project`` or
through the ``code/setup_project.py`` entry point defined in ``code/main.py``.
"""

import os
from pathlib import Path
import argparse
import sys

# List of directories that must exist at the repository root
REQUIRED_DIRS = [
    Path("code"),
    Path("data"),
    Path("data/raw"),
    Path("data/processed"),
    Path("results"),
    Path("scripts"),
    Path("specs"),
]

def create_directories() -> None:
    """Create all required directories if they do not already exist."""
    for directory in REQUIRED_DIRS:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as exc:
            print(f"❌ Failed to create directory {directory}: {exc}", file=sys.stderr)
            raise

def verify_requirements_file() -> None:
    """Ensure that ``code/requirements.txt`` exists."""
    req_path = Path("code") / "requirements.txt"
    if not req_path.is_file():
        raise FileNotFoundError(
            f"Requirements file not found at expected location: {req_path}"
        )
    print(f"✅ Requirements file present: {req_path}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set up the project scaffold and verify basic dependencies."
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify that the scaffold and requirements file exist.",
    )
    args = parser.parse_args()

    if args.verify:
        # Just verification mode
        for d in REQUIRED_DIRS:
            if not d.is_dir():
                raise FileNotFoundError(f"Required directory missing: {d}")
        verify_requirements_file()
        print("✅ Scaffold verification passed.")
    else:
        # Create everything
        create_directories()
        verify_requirements_file()
        print("✅ Project scaffold created and verified.")

if __name__ == "__main__":
    main()
