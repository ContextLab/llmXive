import os
import sys
import logging

from utils import setup_logging, get_logger, set_task_id, get_task_id

def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The directory path to ensure exists.
        
    Returns:
        True if the directory exists or was created successfully, False otherwise.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        logger = get_logger()
        if logger:
            log_error(f"Failed to create directory {path}: {e}")
        return False

def create_init_file(path: str) -> bool:
    """
    Create an empty __init__.py file in the specified directory.
    
    Args:
        path: The directory path where __init__.py should be created.
        
    Returns:
        True if the file was created or already exists, False otherwise.
    """
    init_path = os.path.join(path, "__init__.py")
    try:
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write("")
        return True
    except IOError as e:
        logger = get_logger()
        if logger:
            log_error(f"Failed to create __init__.py in {path}: {e}")
        return False

def main():
    """
    Main entry point for creating the project directory structure.
    
    Creates the following directories under the project root:
    - code/
    - data/
    - state/
    - results/
    - tests/
    - docs/
    
    Also creates __init__.py files in code/ and tests/ directories.
    """
    # Initialize logging
    logger = setup_logging(task_id="T001a")
    logger.info("Starting directory structure setup (T001a)")
    
    # Define the project root (current working directory)
    project_root = os.getcwd()
    
    # Define the subdirectories to create
    subdirectories = [
        "code",
        "data",
        "state",
        "results",
        "tests",
        "docs"
    ]
    
    # Create each directory
    for subdir in subdirectories:
        full_path = os.path.join(project_root, subdir)
        if ensure_directory(full_path):
            logger.info(f"Created directory: {full_path}")
        else:
            logger.error(f"Failed to create directory: {full_path}")
            return 1
    
    # Create __init__.py files in code/ and tests/
    init_directories = [
        "code",
        "tests"
    ]
    
    for subdir in init_directories:
        full_path = os.path.join(project_root, subdir)
        if create_init_file(full_path):
            logger.info(f"Created __init__.py in: {full_path}")
        else:
            logger.error(f"Failed to create __init__.py in: {full_path}")
            return 1
    
    # Create additional __init__.py files for test subdirectories
    test_subdirs = [
        "tests/unit",
        "tests/integration"
    ]
    
    for subdir in test_subdirs:
        full_path = os.path.join(project_root, subdir)
        if ensure_directory(full_path):
            logger.info(f"Created directory: {full_path}")
            if create_init_file(full_path):
                logger.info(f"Created __init__.py in: {full_path}")
            else:
                logger.error(f"Failed to create __init__.py in: {full_path}")
                return 1
        else:
            logger.error(f"Failed to create directory: {full_path}")
            return 1
    
    logger.info("Directory structure setup completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
