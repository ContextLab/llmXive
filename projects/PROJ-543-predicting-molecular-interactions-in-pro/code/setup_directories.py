import os
import sys
from pathlib import Path
from utils.io import setup_logging, log_exception

# Define the project root relative to the code directory
# The task requires creating directories under projects/PROJ-543-...
# We assume the script is run from the project root (where 'code' exists)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-543-predicting-molecular-interactions-in-pro"
BASE_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME

# Required subdirectories as per task description
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
    "specs"
]


def create_directories():
    """
    Creates the project directory structure if it does not exist.
    Returns a list of created paths.
    """
    created_paths = []
    logger = logging.getLogger(__name__)

    for dir_name in REQUIRED_DIRS:
        target_path = BASE_DIR / dir_name
        try:
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                created_paths.append(str(target_path))
                logger.info(f"Created directory: {target_path}")
            else:
                logger.debug(f"Directory already exists: {target_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {target_path}: {e}")
            raise

    # Log summary
    logger.info(f"Project structure initialized at: {BASE_DIR}")
    logger.info(f"Total directories created/referenced: {len(created_paths)}")
    return created_paths


def main():
    """
    Entry point for directory setup.
    """
    logger = setup_logging(__name__)
    try:
        paths = create_directories()
        logger.info("Directory setup completed successfully.")
        return 0
    except Exception as e:
        log_exception(logger, e)
        return 1


if __name__ == "__main__":
    sys.exit(main())