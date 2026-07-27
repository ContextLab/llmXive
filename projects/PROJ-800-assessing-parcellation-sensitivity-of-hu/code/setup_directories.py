import os
import sys
from pathlib import Path
from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)

def ensure_directory(path_str: str) -> None:
    """
    Create a directory if it does not exist.
    
    Args:
        path_str: The path to the directory to create.
    
    Raises:
        ConfigurationError: If the directory cannot be created.
    """
    path = Path(path_str)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        except OSError as e:
            msg = f"Failed to create directory {path}: {e}"
            logger.error(msg)
            raise ConfigurationError(msg) from e
    else:
        logger.debug(f"Directory already exists: {path}")

def main() -> int:
    """
    Main entry point to create the project directory structure.
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    project_root = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")
    
    # Define subdirectories based on task requirements
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "code",
        project_root / "tests",
    ]
    
    logger.info(f"Setting up project structure at: {project_root}")
    
    try:
        for directory in directories:
            ensure_directory(str(directory))
        
        logger.info("Project directory structure created successfully.")
        return 0
    except ConfigurationError as e:
        logger.error(f"Failed to set up project structure: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())