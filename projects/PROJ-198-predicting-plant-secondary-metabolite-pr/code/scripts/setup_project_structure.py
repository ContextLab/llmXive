"""
Script to create the project directory structure for llmXive.
Implements T001a: Create code/ directory and subdirectories.
Implements T001b: Create data/ directory structure.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if running from script directory
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import setup_logging, get_logger
from config_env import ensure_directories

def create_directories():
    """Create the required directory structure for the project."""
    logger = get_logger(__name__)
    
    # Define directories to create
    code_dirs = [
        "code/data",
        "code/modeling",
        "code/utils",
        "code/cli",
        "tests/unit",
        "tests/integration"
    ]
    
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/interim"
    ]
    
    all_dirs = code_dirs + data_dirs
    
    created_count = 0
    for dir_path in all_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    logger.info(f"Directory creation complete. Created {created_count} new directories.")
    return created_count

def create_init_files():
    """Create __init__.py files in all Python package directories."""
    logger = get_logger(__name__)
    
    # Define Python package directories
    package_dirs = [
        "code",
        "code/data",
        "code/modeling",
        "code/utils",
        "code/cli",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    for dir_path in package_dirs:
        full_path = project_root / dir_path
        init_file = full_path / "__init__.py"
        
        if not init_file.exists():
          # Create empty __init__.py
          init_file.touch()
          logger.info(f"Created __init__.py: {init_file}")
          created_count += 1
        else:
          logger.debug(f"__init__.py already exists: {init_file}")
    
    logger.info(f"Init file creation complete. Created {created_count} new __init__.py files.")
    return created_count

def main():
    """Main entry point for the script."""
    # Setup logging
    log_file = project_root / "logs" / "setup_project.log"
    logger = setup_logging(log_file=log_file, level=logging.INFO)
    
    logger.info("Starting project structure setup...")
    
    # Create directories
    create_directories()
    
    # Create init files
    create_init_files()
    
    # Also ensure data directories via config_env utility
    ensure_directories()
    
    logger.info("Project structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
