import os
import sys
import logging
from pathlib import Path

# Ensure code directory is in path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.logging import setup_logging, get_logger
from code.utils.directories import create_all_directories

def main() -> None:
    """
    Main entry point to initialize the project directory structure.
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Starting directory structure initialization...")

    try:
        create_all_directories()
        logger.info("Directory structure initialization completed successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize directory structure: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()