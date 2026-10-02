"""
Project structure setup and verification utilities.
Creates the required directory tree and verifies its existence.
"""
import os
import sys
import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> str:
    """
    Returns the absolute path to the project root.
    Assumes this file is at code/setup_structure.py.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, ".."))

def ensure_dir(path: str) -> None:
    """
    Creates a directory if it does not exist.
    """
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Created directory: {path}")
    else:
        logger.debug(f"Directory already exists: {path}")

def create_project_structure() -> None:
    """
    Creates the standard project directory structure:
    - code/
    - data/
    - docs/
    - tests/
    """
    root = get_project_root()
    logger.info(f"Project root identified at: {root}")

    required_dirs = [
        os.path.join(root, "code"),
        os.path.join(root, "data"),
        os.path.join(root, "docs"),
        os.path.join(root, "tests")
    ]

    # Create subdirectories for data organization
    data_subdirs = [
        os.path.join(root, "data", "raw"),
        os.path.join(root, "data", "processed"),
        os.path.join(root, "data", "reports"),
        os.path.join(root, "data", "results"),
        os.path.join(root, "data", "figures")
    ]
    required_dirs.extend(data_subdirs)

    # Create code subdirectories
    code_subdirs = [
        os.path.join(root, "code", "data"),
        os.path.join(root, "code", "features"),
        os.path.join(root, "code", "analysis"),
        os.path.join(root, "code", "utils")
    ]
    required_dirs.extend(code_subdirs)

    for dir_path in required_dirs:
        ensure_dir(dir_path)

    logger.info("Project structure creation complete.")

def verify_structure() -> bool:
    """
    Verifies that the required project directories exist.
    Returns True if all exist, False otherwise.
    Prints a tree-like listing of the 'code/' directory for verification.
    """
    root = get_project_root()
    required_dirs = [
        "code",
        "data",
        "docs",
        "tests"
    ]

    all_exist = True
    logger.info("Verifying project structure...")

    for dir_name in required_dirs:
        dir_path = os.path.join(root, dir_name)
        if os.path.isdir(dir_path):
            logger.info(f"  [OK] {dir_name}/ exists")
        else:
            logger.error(f"  [MISSING] {dir_name}/ does not exist")
            all_exist = False

    if all_exist:
        # Print a tree-like listing of the code/ directory
        print("\n--- Directory Listing (code/) ---")
        _print_tree(root, "code")
        print("--- End Listing ---\n")
    else:
        logger.error("Project structure verification FAILED.")

    return all_exist

def _print_tree(root: str, directory: str, prefix: str = "") -> None:
    """
    Helper to print a directory tree structure.
    """
    dir_path = os.path.join(root, directory)
    if not os.path.isdir(dir_path):
        return

    try:
        items = sorted(os.listdir(dir_path))
    except PermissionError:
        logger.warning(f"Permission denied: {dir_path}")
        return

    for i, item in enumerate(items):
        item_path = os.path.join(dir_path, item)
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{item}")

        if os.path.isdir(item_path):
            extension = "    " if is_last else "│   "
            _print_tree(root, os.path.join(directory, item), prefix + extension)

def main() -> int:
    """
    Main entry point for the script.
    Creates the structure if missing, then verifies it.
    """
    logger.info("Starting project structure setup...")

    # Attempt to create structure
    create_project_structure()

    # Verify
    if verify_structure():
        logger.info("SUCCESS: Project structure is valid.")
        return 0
    else:
        logger.error("FAILURE: Project structure is incomplete.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
