import os
import sys
from pathlib import Path
from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists. If not, create it and all parent directories.

    Args:
        path: The Path object representing the directory to ensure.

    Raises:
        ConfigurationError: If the directory cannot be created.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
    except OSError as e:
        error_msg = f"Failed to create directory {path}: {e}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e

def main() -> None:
    """
    Main entry point for creating the project directory structure.
    Creates the required directories for PROJ-800-assessing-parcellation-sensitivity-of-hu.
    """
    project_root = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")
    
    # Define directory structure based on task requirements
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "code",
        project_root / "tests",
    ]

    logger.info(f"Starting directory creation for project: {project_root}")
    
    for directory in directories:
        ensure_directory(directory)
    
    logger.info("All project directories created successfully.")
    print(f"Project structure created at: {project_root.absolute()}")

if __name__ == "__main__":
    main()
