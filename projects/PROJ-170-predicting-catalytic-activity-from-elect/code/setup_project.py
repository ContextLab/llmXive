import os
import sys
import logging
from pathlib import Path
from config import get_project_root

def setup_verification_logging():
    """Configure basic logging for verification scripts."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def create_directories():
    """Create the required project directory structure."""
    project_root = get_project_root()
    directories = [
        'data/raw',
        'data/processed',
        'code',
        'outputs',
        'tests',
        'state/projects',
        'code/models'
    ]

    created_paths = []
    for dir_name in directories:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(dir_path)
        logging.info(f"Created directory: {dir_path}")

    return created_paths

def verify_directories():
    """Verify that all required directories exist. Exit with error if any are missing."""
    project_root = get_project_root()
    required_dirs = [
        'data/raw',
        'data/processed',
        'code',
        'outputs',
        'tests',
        'state/projects',
        'code/models'
    ]

    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)

    if missing_dirs:
        error_msg = "Directory initialization failed. Missing directories: " + ", ".join(str(p) for p in missing_dirs)
        logging.error(error_msg)
        sys.exit(1)
    
    logging.info("All required directories verified successfully.")
    return True

def create_init_files():
    """Create __init__.py files in all Python package directories."""
    project_root = get_project_root()
    package_dirs = [
        'code',
        'tests',
        'code/utils',
        'code/models'
    ]

    for dir_name in package_dirs:
        dir_path = project_root / dir_name
        init_file = dir_path / '__init__.py'
        if not init_file.exists():
            init_file.touch()
            logging.info(f"Created __init__.py in {dir_path}")
        else:
            logging.info(f"__init__.py already exists in {dir_path}")

def main():
    """Main entry point for project setup and verification."""
    setup_verification_logging()
    logging.info("Starting project directory setup and verification.")
    
    # Create directories
    create_directories()
    
    # Verify directories exist
    verify_directories()
    
    # Create __init__.py files
    create_init_files()
    
    logging.info("Project setup completed successfully.")

if __name__ == "__main__":
    main()