import os
import sys
import logging
from datetime import datetime
from utils import setup_logging, get_logger, set_task_id, get_unique_id

def ensure_directory(path: str) -> bool:
    """Create directory if it does not exist."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        logging.error(f"Failed to create directory {path}: {e}")
        return False

def create_init_file(dir_path: str) -> bool:
    """Create an empty __init__.py in the specified directory."""
    init_path = os.path.join(dir_path, "__init__.py")
    try:
        with open(init_path, "w") as f:
          f.write(f"# Auto-generated init file for {dir_path}\n")
        return True
    except OSError as e:
        logging.error(f"Failed to create {init_path}: {e}")
        return False

def main():
    """
    T001a: Create directory structure at projects/PROJ-294-evaluating-the-impact-of-code-generation/
    T001b: Create state/ directory
    T001c: Create __init__.py files in code/, tests/, tests/unit/, tests/integration/
    """
    task_id = "T001a"
    set_task_id(task_id)
    logger = setup_logging(task_id=task_id)
    logger.info("Starting Project Structure Setup (T001a, T001b, T001c)")

    base_dir = "projects/PROJ-294-evaluating-the-impact-of-code-generation"
    
    # T001a: Core directories
    core_dirs = [
        "code",
        "data",
        "results",
        "tests",
        "docs"
    ]
    
    logger.info(f"Ensuring base directory: {base_dir}")
    if not ensure_directory(base_dir):
        logger.error("Base directory creation failed.")
        sys.exit(1)

    for d in core_dirs:
        full_path = os.path.join(base_dir, d)
        logger.info(f"Ensuring directory: {full_path}")
        if not ensure_directory(full_path):
            logger.error(f"Failed to create {full_path}")
            sys.exit(1)

    # T001b: State directory
    state_dir = os.path.join(base_dir, "state")
    logger.info(f"Ensuring state directory: {state_dir}")
    if not ensure_directory(state_dir):
        logger.error(f"Failed to create {state_dir}")
        sys.exit(1)

    # T001c: __init__.py files
    init_dirs = [
        os.path.join(base_dir, "code"),
        os.path.join(base_dir, "tests"),
        os.path.join(base_dir, "tests", "unit"),
        os.path.join(base_dir, "tests", "integration")
    ]

    for d in init_dirs:
        logger.info(f"Creating __init__.py in {d}")
        if not ensure_directory(d):
            logger.warning(f"Directory {d} did not exist, attempting to create.")
            ensure_directory(d)
        create_init_file(d)

    logger.info("Project structure setup complete.")

if __name__ == "__main__":
    main()
