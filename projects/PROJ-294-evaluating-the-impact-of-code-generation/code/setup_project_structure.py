import os
import sys
import logging
from datetime import datetime
from utils import setup_logging, get_logger, set_task_id, get_unique_id

def ensure_directory(path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Created directory: {path}")
    else:
        logging.debug(f"Directory already exists: {path}")

def create_init_file(path: str) -> None:
    """Create an empty __init__.py file."""
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write("")
        logging.info(f"Created __init__.py: {path}")
    else:
        logging.debug(f"__init__.py already exists: {path}")

def main():
    """Create the project directory structure for T001a."""
    # Setup logging
    logger = setup_logging(task_id="T001a")
    
    project_root = "projects/PROJ-294-evaluating-the-impact-of-code-generation"
    
    # Define required directories
    directories = [
        f"{project_root}/code",
        f"{project_root}/data",
        f"{project_root}/results",
        f"{project_root}/tests",
        f"{project_root}/docs",
        f"{project_root}/state",  # T001b requirement
        f"{project_root}/code/utils",
        f"{project_root}/code/prompt_templates",
        f"{project_root}/tests/unit",
        f"{project_root}/tests/integration",
        f"{project_root}/data/raw",
        f"{project_root}/data/generated",
        f"{project_root}/data/analysis",
        f"{project_root}/results/figures",
        f"{project_root}/data/sandbox"
    ]
    
    logger.info("Starting directory structure creation...")
    
    for directory in directories:
        ensure_directory(directory)
    
    # Create __init__.py files
    init_files = [
        f"{project_root}/code/__init__.py",
        f"{project_root}/tests/__init__.py",
        f"{project_root}/tests/unit/__init__.py",
        f"{project_root}/tests/integration/__init__.py"
    ]
    
    for init_file in init_files:
        create_init_file(init_file)
    
    logger.info("Directory structure creation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
