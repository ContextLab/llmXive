"""
T001 Implementation: Python-based directory setup utility.
Provides programmatic directory creation and verification for the project.
"""
import os
import sys
from pathlib import Path
import logging
import argparse

# Configure logging to match project standards
from utils.logging import setup_logging

PROJECT_ROOT = "projects/PROJ-422-predicting-molecular-permeability-coeffi"

REQUIRED_DIRS = [
  "code/data",
  "code/models",
  "code/analysis",
  "data/raw",
  "data/processed",
  "data/interim",
  "results",
  "tests/unit",
  "tests/integration",
]

def setup_logging_config():
    """Initialize logging for the setup script."""
    log_path = Path(PROJECT_ROOT) / "results" / "setup_dirs.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=str(log_path), level=logging.INFO)
    return logging.getLogger(__name__)

def create_directories():
    """
    Create the required directory structure programmatically.
    
    Returns:
        bool: True if all directories were created successfully.
    """
    logger = setup_logging_config()
    base_path = Path(PROJECT_ROOT)
    
    logger.info(f"Starting directory creation for {base_path}")
    
    created_count = 0
    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            logger.info(f"Created/Verified: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create {full_path}: {e}")
            return False
    
    logger.info(f"Successfully created {created_count}/{len(REQUIRED_DIRS)} directories.")
    return True

def verify_structure():
    """
    Verify that all required directories exist.
    
    Returns:
        bool: True if structure is valid.
    """
    logger = logging.getLogger(__name__)
    base_path = Path(PROJECT_ROOT)
    
    if not base_path.exists():
        logger.error(f"Project root {base_path} does not exist.")
        return False
    
    missing = []
    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        if not full_path.is_dir():
            missing.append(dir_name)
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False
    
    logger.info("Structure verification passed.")
    return True

def main():
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(description="Setup project directory structure.")
    parser.add_argument("--verify", action="store_true", help="Only verify existing structure.")
    args = parser.parse_args()

    if args.verify:
        success = verify_structure()
    else:
        if create_directories():
            success = verify_structure()
        else:
            success = False

    if success:
        print("Setup completed successfully.")
        sys.exit(0)
    else:
        print("Setup failed or verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()