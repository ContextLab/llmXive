import os
import sys
import logging
from pathlib import Path
from config import get_project_root

def setup_verification_logging():
    """Setup basic logging for directory verification."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def create_directories():
    """Create the required project directory structure."""
    root = get_project_root()
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "code",
        "outputs",
        "tests",
        "state/projects",
        "code/models"
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logging.info(f"Directory already exists: {full_path}")
    
    return created_count

def verify_directories():
    """Verify all required directories exist using os.path.isdir."""
    root = get_project_root()
    dirs_to_verify = [
        "data/raw",
        "data/processed",
        "code",
        "outputs",
        "tests",
        "state/projects",
        "code/models"
    ]

    all_exist = True
    missing_dirs = []

    for dir_path in dirs_to_verify:
        full_path = root / dir_path
        if not os.path.isdir(full_path):
            missing_dirs.append(str(full_path))
            all_exist = False
            logging.error(f"Directory missing: {full_path}")
        else:
            logging.info(f"Verified directory: {full_path}")

    if not all_exist:
        logging.error(f"Missing directories: {missing_dirs}")
        sys.exit(1)

    return True

def create_init_files():
    """Create __init__.py files in Python package directories."""
    root = get_project_root()
    package_dirs = [
        "code",
        "tests",
        "code/utils",
        "code/models"
    ]

    for pkg_dir in package_dirs:
        pkg_path = root / pkg_dir
        init_file = pkg_path / "__init__.py"
        
        if not init_file.exists():
            init_file.touch()
            logging.info(f"Created __init__.py: {init_file}")
        else:
            logging.info(f"__init__.py already exists: {init_file}")

def main():
    """Main entry point for project setup and verification."""
    setup_verification_logging()
    logging.info("Starting project directory setup and verification...")
    
    create_directories()
    create_init_files()
    verify_directories()
    
    logging.info("Project directory structure verified successfully.")

if __name__ == "__main__":
    main()
