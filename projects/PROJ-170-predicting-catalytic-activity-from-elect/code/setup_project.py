import os
import sys
import logging
from pathlib import Path
from config import get_project_root

# Ensure the logging is configured before we start logging heavy operations
# Assuming code/logging_config.py is already implemented as per T006
try:
    from logging_config import setup_logging
    setup_logging()
except ImportError:
    # Fallback if logging config isn't ready yet (early stage)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "code/models",
    "outputs",
    "tests",
    "state/projects"
]

def setup_verification_logging():
    """Initialize logging for the setup verification process."""
    logger.info("Starting project directory setup verification.")

def create_directories():
    """Create all required directories if they do not exist."""
    project_root = get_project_root()
    created_count = 0
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    if created_count > 0:
        logger.info(f"Successfully created {created_count} directories.")
    else:
        logger.info("No new directories created; all exist.")

def verify_directories():
    """Verify that all required directories exist. Fail loudly if any are missing."""
    project_root = get_project_root()
    missing_dirs = []
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        error_msg = f"CRITICAL: The following required directories are missing: {missing_dirs}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info("Verification passed: All required directories exist.")
    return True

def create_init_files():
    """Create __init__.py in all Python package directories."""
    project_root = get_project_root()
    # Identify directories that should be Python packages
    # Based on the required structure: code, tests, state/projects (if needed), code/models
    package_dirs = [
        "code",
        "code/models",
        "tests",
        "state/projects",
        "data", # Optional, but good practice if data has python modules
    ]

    created_count = 0
    for dir_path in package_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                logger.info(f"Created __init__.py: {init_file}")
                created_count += 1
            else:
                logger.debug(f"__init__.py already exists: {init_file}")
        
        # Also ensure subdirectories in 'code' and 'tests' have __init__.py if they exist
        # This handles nested structures dynamically
        for item in full_path.rglob("*"):
            if item.is_dir():
                init_file = item / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
                    logger.debug(f"Created __init__.py: {init_file}")
                    created_count += 1
    
    logger.info(f"Created {created_count} __init__.py files.")

def main():
    """Main entry point for T001: Initialize project directory structure."""
    setup_verification_logging()
    try:
        create_directories()
        verify_directories()
        create_init_files()
        logger.info("Project directory structure initialization completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Project directory initialization failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
