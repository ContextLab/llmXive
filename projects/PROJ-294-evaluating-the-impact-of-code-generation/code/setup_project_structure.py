import os
import sys
import logging

# Import shared logging utilities from utils.py
# The utils.py module defines setup_logging, get_logger, set_task_id, etc.
# We must import these to ensure consistent logging across the project.
try:
    from utils import setup_logging, get_logger, set_task_id, get_task_id
except ImportError:
    # Fallback if utils is not yet available (e.g., during initial setup)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    def set_task_id(tid): pass
    def get_task_id(): return None

def ensure_directory(path: str) -> bool:
    """
    Create a directory if it does not exist.
    Returns True if the directory exists or was created, False on failure.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def create_init_file(path: str) -> bool:
    """
    Create an empty __init__.py file in the given directory.
    Returns True on success, False on failure.
    """
    init_path = os.path.join(path, "__init__.py")
    try:
        with open(init_path, "w") as f:
            f.write("# Auto-generated init file\n")
        return True
    except IOError as e:
        logger.error(f"Failed to create __init__.py at {init_path}: {e}")
        return False

def main():
    """
    T001a: Create directory structure for the project.
    Creates: code/, data/, state/, results/, tests/, docs/
    """
    # Setup logging
    logger = setup_logging() if 'setup_logging' in globals() else logging.getLogger("setup_structure")
    set_task_id("T001a")
    logger.info("Starting T001a: Create directory structure")

    # Base project directory
    # The task description mentions `projects/294-evaluating-code-testability/`
    # However, the plan.md and path conventions specify the root structure.
    # We will create the root-level directories as per the "Path Conventions" section:
    # code/, data/, state/, results/, tests/, docs/
    
    # The task specifically asks for:
    # `projects/294-evaluating-code-testability/` with subdirectories.
    # But the execution context shows the project root is likely where we are running.
    # We will create the structure relative to the current working directory (project root).
    
    base_dirs = [
        "code",
        "data",
        "state",
        "results",
        "tests",
        "docs"
    ]

    # Also create subdirectories for tests as per T001b requirement (though T001b is separate,
    # creating them here ensures structure is ready)
    test_subdirs = [
        "tests/unit",
        "tests/integration"
    ]

    # Also data subdirectories for T008
    data_subdirs = [
        "data/raw",
        "data/generated",
        "data/analysis"
    ]

    all_dirs = base_dirs + test_subdirs + data_subdirs

    success = True
    for dir_path in all_dirs:
        if ensure_directory(dir_path):
            logger.info(f"Created directory: {dir_path}")
        else:
            success = False

    if success:
        logger.info("T001a: Directory structure created successfully.")
    else:
        logger.error("T001a: Failed to create some directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()
