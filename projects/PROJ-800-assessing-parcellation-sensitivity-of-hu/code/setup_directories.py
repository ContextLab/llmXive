"""
Script to initialize the project directory structure for PROJ-800.
This implements Task T001: Create project directory structure.
"""
import os
import sys
from pathlib import Path
from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The Path object representing the directory to create.

    Returns:
        True if the directory was created or already existed, False on failure.
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
            return True
        elif path.is_dir():
            logger.debug(f"Directory already exists: {path}")
            return True
        else:
            logger.error(f"Path exists but is not a directory: {path}")
            return False
    except PermissionError as e:
        logger.error(f"Permission denied creating directory {path}: {e}")
        return False
    except OSError as e:
        logger.error(f"OS error creating directory {path}: {e}")
        return False


def main() -> int:
    """
    Main entry point for directory setup.
    Creates the required project structure under projects/PROJ-800-assessing-parcellation-sensitivity-of-hu.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    project_root = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")
    
    # Define the required directory structure
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "code",
        project_root / "tests",
    ]

    logger.info(f"Initializing project structure at: {project_root}")
    
    success = True
    for directory in directories:
        if not ensure_directory(directory):
            success = False
            logger.error(f"Failed to create directory: {directory}")
    
    if success:
        logger.info("Project directory structure created successfully.")
        # Print the tree structure for verification
        print("\nCreated directory structure:")
        for root, dirs, files in os.walk(project_root):
            level = root.replace(str(project_root), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                print(f'{sub_indent}{file}')
        return 0
    else:
        logger.error("Failed to create some directories. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())