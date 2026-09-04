import os
from pathlib import Path
import logging
from logging_config import setup_logging, get_logger

def create_spec_directories():
    """
    Creates the required specification directories for the project.
    Specifically creates:
    - specs/001-neural-correlates-of-anticipatory-reward/
    
    This implements task T001c.
    """
    logger = get_logger()
    project_root = Path(__file__).resolve().parent.parent
    spec_base = project_root / "specs"
    feature_dir = spec_base / "001-neural-correlates-of-anticipatory-reward"

    logger.info(f"Ensuring spec directory exists: {feature_dir}")
    
    # Create the directory if it doesn't exist
    feature_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify creation
    if feature_dir.exists() and feature_dir.is_dir():
        logger.info(f"Successfully created directory: {feature_dir}")
        return True
    else:
        logger.error(f"Failed to create directory: {feature_dir}")
        return False

def main():
    """Main entry point for script execution."""
    setup_logging()
    logger = get_logger()
    logger.info("Starting spec directory creation (T001c)...")
    
    success = create_spec_directories()
    
    if success:
        logger.info("T001c completed successfully.")
        return 0
    else:
        logger.error("T001c failed.")
        return 1

if __name__ == "__main__":
    exit(main())
