import os
import sys
import logging
from datetime import datetime
from utils import setup_logging, get_logger, set_task_id, get_unique_id

def ensure_directory(path: str, verbose: bool = True) -> bool:
    """
    Create a directory and all its parent directories if they do not exist.
    
    Args:
        path (str): The directory path to create.
        verbose (bool): If True, log the creation action.
        
    Returns:
        bool: True if the directory was created or already exists, False on error.
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            if verbose:
                logging.info(f"Created directory: {path}")
        else:
            if verbose:
                logging.info(f"Directory already exists: {path}")
        return True
    except OSError as e:
        logging.error(f"Failed to create directory {path}: {e}")
        return False

def create_init_file(directory: str, verbose: bool = True) -> bool:
    """
    Create an empty __init__.py file in the specified directory to make it a Python package.
    
    Args:
        directory (str): The directory path.
        verbose (bool): If True, log the creation action.
        
    Returns:
        bool: True if the file was created or already exists, False on error.
    """
    init_path = os.path.join(directory, "__init__.py")
    try:
        if not os.path.exists(init_path):
            with open(init_path, 'w') as f:
                f.write(f"# Auto-generated package init file created at {datetime.now().isoformat()}\n")
            if verbose:
                logging.info(f"Created __init__.py: {init_path}")
        else:
            if verbose:
                logging.info(f"__init__.py already exists: {init_path}")
        return True
    except IOError as e:
        logging.error(f"Failed to create __init__.py at {init_path}: {e}")
        return False

def main():
    """
    Main entry point for T001a: Create directory structure and init files.
    
    Creates the following directories under the project root:
    - code/
    - data/
    - results/
    - tests/
    - docs/
    
    Also creates __init__.py files in code/, tests/, tests/unit/, tests/integration/.
    """
    # Initialize logging
    logger = setup_logging(task_id="T001a")
    logger.info("Starting T001a: Create directory structure")
    
    # Define base project root (assumes script is run from project root or we resolve relative paths)
    # The task requires paths relative to the project root: projects/PROJ-294-evaluating-the-impact-of-code-generation/
    # We will create directories relative to the current working directory as per task constraint
    
    project_root = os.getcwd()
    
    # Directories to create for T001a
    directories = [
        "code",
        "data",
        "results",
        "tests",
        "docs"
    ]
    
    success = True
    
    for dir_name in directories:
        full_path = os.path.join(project_root, dir_name)
        if not ensure_directory(full_path):
            success = False
        
        # Create __init__.py for specific directories
        if dir_name in ["code", "tests"]:
            if not create_init_file(full_path):
                success = False
        
        # Create subdirectories for tests and their __init__.py
        if dir_name == "tests":
            test_subdirs = ["unit", "integration"]
            for sub in test_subdirs:
                sub_path = os.path.join(full_path, sub)
                if not ensure_directory(sub_path):
                    success = False
                if not create_init_file(sub_path):
                    success = False
    
    # Verification step: Create .gitkeep files to ensure directories are tracked and verified
    gitkeep_dirs = ["code", "data", "results", "tests", "docs"]
    for dir_name in gitkeep_dirs:
        full_path = os.path.join(project_root, dir_name)
        gitkeep_path = os.path.join(full_path, ".gitkeep")
        try:
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, 'w') as f:
                    f.write(f"# Directory marker created at {datetime.now().isoformat()}\n")
                logger.info(f"Created .gitkeep in {full_path}")
        except IOError as e:
            logger.error(f"Failed to create .gitkeep in {full_path}: {e}")
            success = False
    
    if success:
        logger.info("T001a completed successfully. All directories and init files created.")
    else:
        logger.error("T001a completed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
