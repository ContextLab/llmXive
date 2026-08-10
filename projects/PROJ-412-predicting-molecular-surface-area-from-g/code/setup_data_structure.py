import os
import sys
import logging
from pathlib import Path

# Adjust imports based on project structure expectations
# Assuming this file is run from the project root or code/ directory
# We will use absolute imports relative to the package if installed, or relative if run directly
try:
    from code.utils.logging import get_logger
    from code.utils.config import get_project_root, get_data_dir
except ImportError:
    # Fallback for direct execution without package installation
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from code.utils.logging import get_logger
    from code.utils.config import get_project_root, get_data_dir


def create_data_directories(logger: logging.Logger) -> None:
    """
    Initialize data directories as per task T001b.
    Creates: data/raw/, data/processed/, data/splits/, data/schemas/
    """
    data_root = get_data_dir()
    logger.info(f"Ensuring data directories exist under: {data_root}")

    required_dirs = [
        "raw",
        "processed",
        "splits",
        "schemas"
    ]

    for dir_name in required_dirs:
        dir_path = data_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")


def main() -> None:
    """
    Entry point for T001b.
    """
    logger = get_logger("T001b")
    logger.info("Starting T001b: Initialize data directories")

    try:
        create_data_directories(logger)
        logger.info("T001b completed successfully.")
    except Exception as e:
        logger.error(f"Failed to create data directories: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()