"""
Script to configure directory structure for the project.
Implements Task T008: Configure directory structure for data/raw/, data/processed/, and state/.
"""
import sys
from pathlib import Path
from src.utils.io import configure_logging, ensure_directory

def main():
    """
    Main entry point to create the required directory structure.
    Creates:
      - data/raw/
      - data/processed/
      - state/
    """
    logger = configure_logging()
    logger.info("Starting directory structure setup (Task T008)...")

    # Define the root directory (current working directory or explicit project root)
    # Assuming this script is run from the project root
    project_root = Path.cwd()

    # Define required subdirectories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state",
    ]

    created_count = 0
    for dir_path in directories:
        if ensure_directory(dir_path):
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.info(f"Directory already exists: {dir_path}")

    logger.info(f"Directory setup complete. Created/Verified {created_count} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())