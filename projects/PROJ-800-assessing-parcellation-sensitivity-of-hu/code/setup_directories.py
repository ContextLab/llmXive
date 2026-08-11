import os
import sys
from pathlib import Path
from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)

def ensure_directory(path: Path) -> None:
    """
    Create a directory and all its parents if they do not exist.
    Logs the creation and raises ConfigurationError if creation fails.
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")
    except OSError as e:
        error_msg = f"Failed to create directory {path}: {e}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e

def main() -> int:
    """
    Main entry point to create the project directory structure for PROJ-800.
    Returns 0 on success, 1 on failure.
    """
    project_root = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")
    
    # Define the required subdirectories based on T001 specification
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
    ]
    
    code_dirs = [
        project_root / "code",
        project_root / "tests",
    ]
    
    all_dirs = data_dirs + code_dirs

    logger.info(f"Starting directory setup for project: {project_root}")

    for directory in all_dirs:
        ensure_directory(directory)

    logger.info("Directory structure creation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
