import os
import sys
from pathlib import Path
from typing import List

from config import DATA_DIR, PROJECT_ROOT, LOG_DIR, ERRORS_DIR, MODELS_DIR, REPORTS_DIR
from utils.logging import get_logger


def create_directories() -> None:
    """
    Create the required directory structure for the project.
    
    Creates:
    - data/raw/
    - data/curated/
    - data/artifacts/
    - data/logs/
    - errors/
    - models/
    - reports/
    """
    logger = get_logger(__name__)
    
    # Define all directories to create
    directories: List[Path] = [
        DATA_DIR / "raw",
        DATA_DIR / "curated",
        DATA_DIR / "artifacts",
        DATA_DIR / "logs",
        ERRORS_DIR,
        MODELS_DIR,
        REPORTS_DIR,
        LOG_DIR,
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {directory}")
    
    logger.info(f"Directory setup complete. Created {created_count} new directories.")


def create_init_files() -> None:
    """
    Create __init__.py files in all Python package directories.
    This ensures they are recognized as Python packages.
    """
    logger = get_logger(__name__)
    
    # Define directories that should be Python packages
    package_dirs: List[Path] = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "code" / "data",
        PROJECT_ROOT / "code" / "utils",
        PROJECT_ROOT / "code" / "models",
        PROJECT_ROOT / "code" / "validation",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "tests" / "contract",
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "integration",
    ]
    
    for package_dir in package_dirs:
        init_file = package_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created __init__.py in: {package_dir}")


def main() -> None:
    """
    Main function to set up the project directory structure.
    This is the entry point for the setup script.
    """
    logger = get_logger(__name__)
    logger.info("Starting project directory setup...")
    
    # Create directory structure
    create_directories()
    
    # Create __init__.py files
    create_init_files()
    
    logger.info("Project directory setup completed successfully.")
    
    # Print summary of created directories
    print("\nProject structure summary:")
    print(f"  DATA_DIR: {DATA_DIR}")
    print(f"    - raw/")
    print(f"    - curated/")
    print(f"    - artifacts/")
    print(f"    - logs/")
    print(f"  ERRORS_DIR: {ERRORS_DIR}")
    print(f"  MODELS_DIR: {MODELS_DIR}")
    print(f"  REPORTS_DIR: {REPORTS_DIR}")
    print(f"  LOG_DIR: {LOG_DIR}")


if __name__ == "__main__":
    main()
