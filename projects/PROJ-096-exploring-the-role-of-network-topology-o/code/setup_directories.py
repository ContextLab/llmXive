"""
Setup project directories (General).
This module handles the creation of general project directories if needed,
though specific setup is handled by dedicated modules (data, test, etc.).
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


def create_directories(base_path: Path) -> None:
    """
    Create standard project directories if they don't exist.

    Args:
        base_path: The root directory of the project.
    """
    # Note: Specific directories like data, code, tests are handled by
    # setup_data_directories.py, setup_test_directories.py, etc.
    # This function is a fallback or for general root-level structure if needed.
    # For now, we ensure the base_path exists.
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created base project directory: {base_path}")


def main() -> int:
    """
    Main entry point.
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    try:
        create_directories(project_root)
        return 0
    except Exception as e:
        logger.error(f"Error creating directories: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
