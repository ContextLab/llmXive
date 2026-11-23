import os
import logging
import sys
from pathlib import Path
from typing import List, Tuple

from config import get_project_root, get_config
from setup_logging import log_directory_creation, setup_logger

def ensure_data_directories() -> List[Tuple[str, bool]]:
    """
    Ensure all required project directories exist.
    
    Returns:
        List of tuples (directory_path, created_flag) indicating which dirs were created.
    """
    project_root = get_project_root()
    config = get_config()
    
    # Define subdirectories relative to project root
    subdirs = [
        "code",
        "data",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "data/figures",
        "docs",
        "specs",
        "contracts"
    ]
    
    created_dirs = []
    logger = setup_logger("directory_setup")
    
    # Ensure project root exists
    project_root.mkdir(parents=True, exist_ok=True)
    log_directory_creation("root", str(project_root), "directory_setup")
    
    # Create subdirectories
    for subdir in subdirs:
        dir_path = project_root / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append((str(dir_path), True))
            log_directory_creation("subdirectory", str(dir_path), "directory_setup")
        else:
            created_dirs.append((str(dir_path), False))
            
    return created_dirs

def generate_init_files() -> List[str]:
    """
    Generate __init__.py files for all Python packages.
    
    Returns:
        List of paths to created __init__.py files.
    """
    project_root = get_project_root()
    python_packages = ["code", "code/data", "code/analysis", "code/inference", 
                     "code/utils", "code/contracts", "tests", "tests/unit"]
    
    init_files = []
    
    for package in python_packages:
        pkg_path = project_root / package
        if pkg_path.exists():
            init_path = pkg_path / "__init__.py"
            if not init_path.exists():
                init_path.write_text("# Package initialization\n")
                init_files.append(str(init_path))
                
    return init_files

def main():
    """
    Main entry point for directory setup.
    Creates all required directories and generates init files.
    """
    logger = setup_logger("directory_setup")
    logger.info("Starting directory setup...")
    
    # Ensure directories
    created_dirs = ensure_data_directories()
    logger.info(f"Created/verified {len(created_dirs)} directories")
    
    # Generate init files
    init_files = generate_init_files()
    logger.info(f"Generated {len(init_files)} __init__.py files")
    
    logger.info("Directory setup completed successfully")

if __name__ == "__main__":
    main()
