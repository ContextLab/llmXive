import os
import sys
import venv
import subprocess
from pathlib import Path
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


def setup_venv(project_root: Path) -> bool:
    """
    Initialize a Python virtual environment in the project root.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if successful, False otherwise.
    """
    venv_dir = project_root / "venv"

    if venv_dir.exists():
        logger.warning(f"Virtual environment already exists at {venv_dir}. Skipping creation.")
        return True

    logger.info(f"Creating virtual environment at {venv_dir}...")
    try:
        venv.create(venv_dir, with_pip=True)
        logger.info("Virtual environment created successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return False


def main() -> int:
    """
    Main entry point for the setup_venv script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Determine project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    logger.info(f"Project root: {project_root}")

    success = setup_venv(project_root)

    if success:
        logger.info("Virtual environment setup completed.")
        return 0
    else:
        logger.error("Virtual environment setup failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
