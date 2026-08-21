import os
import sys
import logging
from datetime import datetime
from utils import setup_logging, get_logger, set_task_id, get_unique_id

def ensure_directory(path: str) -> bool:
    """Create a directory if it does not exist, including parent directories."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        logging.error(f"Failed to create directory {path}: {e}")
        return False

def create_init_file(path: str) -> bool:
    """Create an empty __init__.py file in the given directory."""
    init_path = os.path.join(path, "__init__.py")
    try:
        with open(init_path, "w") as f:
            f.write("# Auto-generated init file\n")
        return True
    except IOError as e:
        logging.error(f"Failed to create __init__.py at {init_path}: {e}")
        return False

def main():
    """
    T001a: Create directory structure at projects/PROJ-294-evaluating-the-impact-of-code-generation/
    Creates: code/, data/, results/, tests/, docs/
    Also creates __init__.py in code/ and tests/ as per T001c logic embedded here for setup.
    """
    # Initialize logging for the task
    logger = setup_logging(task_id="T001a")
    logger.info("Starting directory structure creation for PROJ-294")

    base_dir = os.path.join("projects", "PROJ-294-evaluating-the-impact-of-code-generation")
    required_dirs = [
        "code",
        "data",
        "results",
        "tests",
        "docs",
        "state"  # T001b requirement
    ]

    # Create base directory
    if not ensure_directory(base_dir):
        logger.error("Failed to create base project directory.")
        sys.exit(1)

    # Create subdirectories
    for subdir in required_dirs:
        full_path = os.path.join(base_dir, subdir)
        if ensure_directory(full_path):
            logger.info(f"Created directory: {full_path}")
        else:
            logger.warning(f"Directory already exists or failed to create: {full_path}")

    # T001c: Create __init__.py files
    init_dirs = [
        os.path.join(base_dir, "code"),
        os.path.join(base_dir, "tests"),
        os.path.join(base_dir, "tests", "unit"),
        os.path.join(base_dir, "tests", "integration")
    ]

    for init_dir in init_dirs:
        ensure_directory(init_dir)  # Ensure unit/integration exist
        if create_init_file(init_dir):
            logger.info(f"Created __init__.py in {init_dir}")

    # Create data subdirectories as per T008
    data_subdirs = ["raw", "generated", "analysis"]
    data_base = os.path.join(base_dir, "data")
    for subdir in data_subdirs:
        full_path = os.path.join(data_base, subdir)
        if ensure_directory(full_path):
            logger.info(f"Created data subdirectory: {full_path}")

    # Create results subdirectories
    results_subdirs = ["figures"]
    results_base = os.path.join(base_dir, "results")
    for subdir in results_subdirs:
        full_path = os.path.join(results_base, subdir)
        if ensure_directory(full_path):
            logger.info(f"Created results subdirectory: {full_path}")

    logger.info("Directory structure creation completed successfully.")

if __name__ == "__main__":
    main()
