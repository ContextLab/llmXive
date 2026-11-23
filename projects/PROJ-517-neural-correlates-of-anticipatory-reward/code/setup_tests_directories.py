import os
from pathlib import Path
import logging
from logging_config import setup_logging, get_logger

def create_directory(dir_path: str, logger: logging.Logger) -> bool:
    """
    Check if a directory exists. If not, create it and verify.
    
    Args:
        dir_path: Relative or absolute path to the directory.
        logger: Logger instance for status updates.
        
    Returns:
        True if the directory exists or was successfully created.
        False if creation failed.
    """
    path = Path(dir_path)
    
    if path.exists():
        logger.info(f"Directory already exists: {path.resolve()}")
        return True
    
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path.resolve()}")
        
        # Verification step
        if not path.exists():
            logger.error(f"Verification failed: Directory {path} was not created.")
            return False
            
        if not path.is_dir():
            logger.error(f"Verification failed: {path} exists but is not a directory.")
            return False
            
        logger.info(f"Verification successful: {path.resolve()}")
        return True
        
    except PermissionError:
        logger.error(f"Permission denied: Cannot create directory {path.resolve()}")
        return False
    except OSError as e:
        logger.error(f"OS error creating directory {path.resolve()}: {e}")
        return False

def main():
    """
    Main entry point for creating the tests directory.
    Implements T001b: Create tests directory and verify existence.
    """
    logger = setup_logging()
    
    # Define the target directory relative to project root
    project_root = Path.cwd()
    tests_dir = project_root / "tests"
    
    logger.info(f"Starting directory creation for T001b: {tests_dir}")
    
    success = create_directory(str(tests_dir), logger)
    
    if not success:
        logger.critical("T001b FAILED: Could not create or verify 'tests/' directory.")
        raise SystemExit(1)
        
    logger.info("T001b SUCCESS: 'tests/' directory created and verified.")
    raise SystemExit(0)

if __name__ == "__main__":
    main()
