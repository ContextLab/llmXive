import os
import sys
import logging
from pathlib import Path
from config import get_project_root

def setup_verification_logging():
    """Configure logging for directory verification."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_directories(root_path: Path):
    """Create the required project directory structure."""
    directories = [
        'data/raw',
        'data/processed',
        'code',
        'outputs',
        'tests',
        'state/projects',
        'code/models'
    ]

    for dir_name in directories:
        dir_path = root_path / dir_name
        os.makedirs(dir_path, exist_ok=True)
        logging.info(f"Created directory: {dir_path}")

def verify_directories(root_path: Path):
    """Verify that all required directories exist. Exit with failure if any are missing."""
    required_dirs = [
        'data/raw',
        'data/processed',
        'code',
        'outputs',
        'tests',
        'state/projects',
        'code/models'
    ]

    all_exist = True
    for dir_name in required_dirs:
        dir_path = root_path / dir_name
        if not os.path.isdir(dir_path):
            logging.error(f"Directory missing: {dir_path}")
            all_exist = False
        else:
            logging.info(f"Verified directory: {dir_path}")

    if not all_exist:
        logging.error("Directory initialization failed.")
        sys.exit(1)
    
    logging.info("All required directories verified successfully.")

def create_init_files(root_path: Path):
    """Create __init__.py files to make directories Python packages."""
    package_dirs = [
        'code',
        'tests',
        'code/utils',
        'code/models'
    ]

    for dir_name in package_dirs:
        dir_path = root_path / dir_name
        init_file = dir_path / '__init__.py'
        if not init_file.exists():
            init_file.touch()
            logging.info(f"Created __init__.py: {init_file}")
        else:
            logging.info(f"__init__.py already exists: {init_file}")

def main():
    """Main entry point for project setup and verification."""
    setup_verification_logging()
    root = get_project_root()
    
    logging.info(f"Project root: {root}")
    
    create_directories(root)
    verify_directories(root)
    create_init_files(root)
    
    logging.info("Project setup completed successfully.")

if __name__ == "__main__":
    main()
