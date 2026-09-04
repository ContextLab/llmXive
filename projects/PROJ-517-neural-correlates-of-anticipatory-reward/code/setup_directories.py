import os
from pathlib import Path
import logging
from logging_config import setup_logging, get_logger

def create_directory(path_str: str, logger: logging.Logger) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path_str: Relative or absolute path string.
        logger: Logger instance.
        
    Returns:
        True if directory exists or was created, False otherwise.
    """
    path = Path(path_str)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
            return True
        except OSError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    else:
        logger.debug(f"Directory already exists: {path}")
        return True

def main():
    """
    Main entry point for T001a: Create source code directory.
    Checks if 'code/' exists; if not, creates it. Verifies existence after creation.
    """
    logger = setup_logging()
    logger.info("Starting T001a: Create source code directory")
    
    project_root = Path.cwd()
    code_dir = project_root / "code"
    
    success = create_directory(str(code_dir), logger)
    
    if not success:
        logger.error("Failed to create 'code/' directory.")
        return 1
        
    if not code_dir.exists():
        logger.error("Verification failed: 'code/' directory does not exist after creation attempt.")
        return 1
        
    logger.info("Successfully created and verified 'code/' directory.")
    return 0

if __name__ == "__main__":
    exit(main())
