"""
Setup script to create the tests directory structure.

Creates the following directories:
- tests/
- tests/contract/
- tests/unit/
- tests/integration/
"""
import os
import sys
import logging
from pathlib import Path
from utils.logging import get_logger
from utils.config import get_project_root

def create_tests_directories():
    """Create the tests directory structure."""
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    tests_root = project_root / "tests"
    directories = [
        tests_root,
        tests_root / "contract",
        tests_root / "unit",
        tests_root / "integration",
    ]
    
    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(project_root)))
            logger.info(f"Created directory: {directory.relative_to(project_root)}")
        else:
            logger.debug(f"Directory already exists: {directory.relative_to(project_root)}")
    
    # Create __init__.py files to make directories proper Python packages
    for directory in directories:
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logger.debug(f"Created __init__.py in: {directory.relative_to(project_root)}")
    
    return created

def main():
    """Main entry point for the script."""
    logger = get_logger(__name__)
    logger.info("Starting tests directory structure creation...")
    
    try:
        created_dirs = create_tests_directories()
        logger.info(f"Successfully created {len(created_dirs)} directories")
        logger.info(f"Created directories: {', '.join(created_dirs)}")
        return 0
    except Exception as e:
        logger.error(f"Failed to create tests directory structure: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
