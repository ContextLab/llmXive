import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directory_structure():
    """
    Creates the necessary directory structure for the project.
    Specifically creates 'data/raw' and 'data/processed' as per T001.
    Also ensures 'code' and 'tests' exist if not already present (T002 scope,
    but executed here to ensure a clean environment for the project).
    """
    base_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "state",
        "figures"
    ]

    created_count = 0
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    logger.info(f"Directory setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for directory setup."""
    logger.info("Starting directory structure creation (Task T001 & T002)...")
    try:
        create_directory_structure()
        logger.info("Directory structure creation successful.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create directory structure: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
