"""
Setup data directories for the project.
Creates raw, processed, and checksums directories.
"""
import os
import sys
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_data_directories(base_path: Path) -> None:
    """
    Create the required data directories.

    Args:
        base_path: The root directory of the project.
    """
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "checksums"
    ]

    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")


def main() -> int:
    """
    Main entry point for the setup script.

    Returns:
        0 on success, 1 on failure.
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    logger.info(f"Project root detected at: {project_root}")

    try:
        create_data_directories(project_root)
        logger.info("Data directories setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create data directories: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
