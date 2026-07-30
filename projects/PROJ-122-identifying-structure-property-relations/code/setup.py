import os
from pathlib import Path
from setuptools import setup, find_packages

def run_setup():
    """
    Entry point for project setup.
    Orchestrates the creation of directories and state files.
    """
    # Import local modules
    from code.setup_directories import create_directories
    from code.setup_state import create_state_structure
    from code.utils.logger import setup_logging

    # Setup logging
    logger = setup_logging()
    logger.info("Starting project setup...")

    # Create directory structure
    logger.info("Creating directory structure...")
    created_count = create_directories()
    logger.info(f"Created {created_count} new directories.")

    # Create state structure
    logger.info("Creating state structure...")
    state_file = create_state_structure()
    logger.info(f"State file created at: {state_file}")

    logger.info("Project setup complete.")
    return True

if __name__ == "__main__":
    success = run_setup()
    if success:
        print("Setup completed successfully.")
        exit(0)
    else:
        print("Setup failed.")
        exit(1)
