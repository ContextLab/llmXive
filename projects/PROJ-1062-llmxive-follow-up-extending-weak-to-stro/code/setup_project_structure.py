"""
Project Structure Initialization Script for llmXive.

This script creates the necessary directory structure for the project
as defined in the implementation plan.

Directories created:
- src/data/, src/models/, src/training/, src/analysis/, src/config/
- tests/unit/, tests/integration/
- contracts/
- data/raw/, data/processed/, data/results/
- artifacts/
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the project root (current directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define the directory structure relative to PROJECT_ROOT
# Based on tasks.md T001 requirements
DIRECTORIES_TO_CREATE = [
    # Source code structure
    "src/data",
    "src/models",
    "src/training",
    "src/analysis",
    "src/config",
    "src/core",  # Needed for existing API surface
    
    # Test structure
    "tests/unit",
    "tests/integration",
    "tests/contract", # Based on existing API surface imports
    
    # Contracts
    "contracts",
    
    # Data structure
    "data/raw",
    "data/processed",
    "data/results",
    
    # Artifacts
    "artifacts",
    
    # Documentation (implied by polish tasks)
    "docs",
    
    # Scripts (implied by existing API surface)
    "scripts",
]

def create_directories():
    """
    Creates the project directory structure.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    logger.info(f"Project root identified at: {PROJECT_ROOT}")
    logger.info(f"Creating {len(DIRECTORIES_TO_CREATE)} directories...")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for dir_path_str in DIRECTORIES_TO_CREATE:
        dir_path = PROJECT_ROOT / dir_path_str
        try:
            if dir_path.exists():
                logger.debug(f"Directory already exists: {dir_path}")
                skipped_count += 1
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
                created_count += 1
        except PermissionError as e:
            logger.error(f"Permission denied creating directory {dir_path}: {e}")
            error_count += 1
        except OSError as e:
            logger.error(f"OS error creating directory {dir_path}: {e}")
            error_count += 1
    
    logger.info("-" * 50)
    logger.info(f"Directory creation summary:")
    logger.info(f"  Created: {created_count}")
    logger.info(f"  Skipped (already exist): {skipped_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info("-" * 50)
    
    # Create __init__.py files to make directories Python packages
    # This is crucial for the import structure defined in the API surface
    logger.info("Initializing Python packages with __init__.py files...")
    package_dirs = [
        "src", "src/data", "src/models", "src/training", 
        "src/analysis", "src/config", "src/core",
        "tests", "tests/unit", "tests/integration", "tests/contract"
    ]
    
    for pkg_dir_str in package_dirs:
        pkg_path = PROJECT_ROOT / pkg_dir_str
        init_file = pkg_path / "__init__.py"
        try:
            if not init_file.exists():
                init_file.touch()
                logger.debug(f"Created __init__.py: {init_file}")
        except Exception as e:
            logger.warning(f"Could not create __init__.py in {pkg_path}: {e}")
    
    if error_count > 0:
        logger.error("Some directories could not be created. Check logs above.")
        return False
    
    logger.info("Project structure initialization complete.")
    return True

def main():
    """Entry point for the script."""
    success = create_directories()
    if success:
        logger.info("SUCCESS: Project structure created successfully.")
        sys.exit(0)
    else:
        logger.error("FAILURE: Project structure creation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()