"""Create project directory skeleton and write directory_structure.txt.

This script ensures that the required project directories exist:
  - code/
  - tests/
  - data/raw/
  - data/processed/
  - artifacts/
  - artifacts/logs/

It then writes a file named ``directory_structure.txt`` at the repository
root (the current working directory when the script is invoked).  Each
directory is listed on its own line with a trailing ``/`` as required by
``tests/test_directory_structure.py``.
"""

import sys
from pathlib import Path

from llmxive_toolkit import get_logger

def main() -> int:
    """Create directories and write the directory listing.

    Returns:
        int: Exit code (0 for success, non‑zero for failure).
    """
    logger = get_logger(__name__)

    # Directories to create (relative to the repository root)
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "artifacts",
        "artifacts/logs",
    ]

    # Ensure each directory exists
    for rel_dir in required_dirs:
        dir_path = Path(rel_dir)
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created/verified directory: {dir_path}")
        except Exception as exc:
            logger.error(f"Failed to create directory {dir_path}: {exc}")
            return 1

    # Write the directory_structure.txt file at the repository root
    structure_file = Path("directory_structure.txt")
    try:
        with structure_file.open("w", encoding="utf-8") as f:
            for rel_dir in required_dirs:
                # Ensure a trailing slash as expected by the test suite
                line = rel_dir.rstrip("/") + "/"
                f.write(f"{line}\n")
        logger.info(f"Wrote directory structure file: {structure_file}")
    except Exception as exc:
        logger.error(f"Failed to write {structure_file}: {exc}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())