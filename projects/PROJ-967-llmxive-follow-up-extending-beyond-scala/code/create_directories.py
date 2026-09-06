import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The Path object representing the directory to ensure.

    Returns:
        True if the directory exists or was created successfully, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {path}")
        return True
    except PermissionError:
        logger.error(f"Permission denied creating directory: {path}")
        return False
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False

def main():
    """
    Main function to create the project directory structure.
    """
    # Define the project root relative to the repository root
    # Assuming this script is run from the repository root
    project_root = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")

    # Define the required directories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "code",
        project_root / "tests"
    ]

    logger.info(f"Creating project structure in: {project_root}")

    success = True
    for directory in directories:
        if not ensure_directory(directory):
            success = False

    if success:
        logger.info("Project directory structure created successfully.")
        return 0
    else:
        logger.error("Failed to create some directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())