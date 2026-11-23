import os
import sys
import logging
from pathlib import Path

from utils.logging_config import get_logger

logger = get_logger(__name__)


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The path to the directory.

    Returns:
        True if the directory exists or was created successfully.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def main() -> int:
    """
    Main entry point to verify and create standard project directories.

    Verifies: code/, tests/, logs/, results/, data/raw/, data/processed/, docs/

    Returns:
        0 on success, 1 on failure.
    """
    project_root = Path(__file__).resolve().parent.parent

    directories = [
        project_root / "code",
        project_root / "tests",
        project_root / "logs",
        project_root / "results",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "docs"
    ]

    success = True
    for directory in directories:
        if not ensure_directory(directory):
            success = False

    if success:
        logger.info("All project directories verified/created successfully.")
        return 0
    else:
        logger.error("Some directories failed to be created.")
        return 1


if __name__ == "__main__":
    sys.exit(main())