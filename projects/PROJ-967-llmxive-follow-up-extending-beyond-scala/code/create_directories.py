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

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path object representing the directory to create
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
    except PermissionError:
        logger.error(f"Permission denied when creating directory: {path}")
        raise
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        raise

def main() -> int:
    """
    Main function to create project directories for llmXive follow-up project.
    
    Returns:
        int: 0 on success, 1 on failure
    """
    # Define the project root relative to repository root
    project_root = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
    
    # Define required directories
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "results"
    ]
    
    logger.info(f"Creating project directories under: {project_root}")
    
    success = True
    for dir_path in required_dirs:
        try:
            ensure_directory(dir_path)
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False
    
    if success:
        logger.info("All project directories created successfully.")
        return 0
    else:
        logger.error("Some directories failed to create.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
