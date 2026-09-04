"""
Directory verification module for PROJ-517-neural-correlates-of-anticipatory-reward.

Ensures all required project directories exist and are accessible.
Raises FileNotFoundError if any required directory is missing.
"""
import os
import sys
from pathlib import Path
import logging
from logging_config import setup_logging, get_logger

# Define required directories relative to project root
REQUIRED_DIRS = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "data/figures",
]

def create_directory(dir_path: Path, logger: logging.Logger) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        dir_path: Path object representing the directory to create
        logger: Logger instance for logging actions
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False

def verify_directories(project_root: Optional[Path] = None) -> bool:
    """
    Verify that all required project directories exist.
    
    Creates missing directories and raises FileNotFoundError if creation fails
    or if any directory cannot be accessed.
    
    Args:
        project_root: Optional path to project root. Defaults to current working directory.
        
    Returns:
        True if all directories exist and are accessible, False otherwise
        
    Raises:
        FileNotFoundError: If any required directory is missing and cannot be created
    """
    if project_root is None:
        project_root = Path.cwd()
        
    logger = get_logger(__name__)
    all_ok = True
    
    for dir_name in REQUIRED_DIRS:
        dir_path = project_root / dir_name
        
        if not dir_path.exists():
            logger.info(f"Directory missing: {dir_path}. Attempting creation...")
            if not create_directory(dir_path, logger):
                all_ok = False
        else:
            # Verify it's actually a directory and is accessible
            if not dir_path.is_dir():
                logger.error(f"Path exists but is not a directory: {dir_path}")
                all_ok = False
            elif not os.access(dir_path, os.R_OK | os.W_OK | os.X_OK):
                logger.error(f"Directory exists but is not accessible: {dir_path}")
                all_ok = False
                
    if not all_ok:
        missing_dirs = [
            d for d in REQUIRED_DIRS 
            if not (project_root / d).exists() or not os.access(project_root / d, os.R_OK)
        ]
        raise FileNotFoundError(
            f"Required directories missing or inaccessible: {missing_dirs}. "
            f"Please check permissions or run with appropriate privileges."
        )
        
    logger.info("All required directories verified successfully.")
    return True

def main():
    """
    Main entry point for directory verification script.
    
    Verifies all required directories exist, creates them if missing,
    and exits with appropriate status code.
    """
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        project_root = Path.cwd()
        logger.info(f"Verifying directories in project root: {project_root}")
        
        if verify_directories(project_root):
            logger.info("Directory verification completed successfully.")
            sys.exit(0)
        else:
            logger.error("Directory verification failed.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"Directory verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during directory verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
