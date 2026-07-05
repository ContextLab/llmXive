"""Setup script to create the `tests/unit/` directory.

This script is part of the project initialization steps. Running it will
ensure that the `tests/unit/` directory exists, creating any missing parent
directories as needed.
"""

import os
from pathlib import Path

# Re‑use the generic directory‑creation utilities already provided in the
# project.  `setup_directories.create_directory` creates a directory if it
# does not exist (including any missing parents) and is idempotent.
from setup_directories import create_directory, main as setup_main


def main() -> None:
    """Create the `tests/unit/` directory."""
    # Define the target path relative to the repository root.
    target_path = Path("tests") / "unit"

    # Use the shared helper to actually create the directory.
    create_directory(target_path)


if __name__ == "__main__":
    # When executed directly, run the setup.
    main()