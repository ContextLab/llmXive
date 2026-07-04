"""
Script to create and verify required data directories for the exoplanetary atmosphere project.
Creates data/raw/ and data/processed/ directories under the project root.
"""
import os
import sys
from pathlib import Path
import logging

# Import existing logging setup from utils
from utils import setup_logging

# Define required data directories relative to project root
DATA_DIRS = [
    "data/raw",
    "data/processed"
]

def create_directories(base_path: Path, dir_paths: list) -> bool:
    """
    Create directories if they do not exist and verify their creation.

    Args:
        base_path: The root directory for the project
        dir_paths: List of relative directory paths to create

    Returns:
        bool: True if all directories were successfully created/verified, False otherwise
    """
    all_success = True

    for dir_path in dir_paths:
        full_path = base_path / dir_path

        try:
            # Create directory if it doesn't exist (including parents)
            full_path.mkdir(parents=True, exist_ok=True)

            # Verify existence and that it's actually a directory
            if full_path.exists() and full_path.is_dir():
                logging.info(f"Successfully verified directory: {full_path}")
            else:
                logging.error(f"Failed to verify directory creation: {full_path}")
                all_success = False

        except PermissionError:
            logging.error(f"Permission denied when creating directory: {full_path}")
            all_success = False
        except OSError as e:
            logging.error(f"OS error when creating directory {full_path}: {e}")
            all_success = False

    return all_success

def main():
    """Main entry point for directory creation script."""
    # Setup logging
    log_config = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
    logger = setup_logging("create_data_dirs", **log_config)

    # Determine project root (parent of code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    logger.info(f"Project root detected at: {project_root}")

    # Create required data directories
    logger.info(f"Creating data directories: {DATA_DIRS}")
    success = create_directories(project_root, DATA_DIRS)

    if success:
        logger.info("All required data directories created and verified successfully.")
        # Print verification output for the verifier
        print("\n--- Directory Verification Report ---")
        for dir_path in DATA_DIRS:
            full_path = project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                print(f"✓ EXISTS: {full_path}")
            else:
                print(f"✗ MISSING: {full_path}")
        print("--- End Verification Report ---\n")
        return 0
    else:
        logger.error("Failed to create one or more required directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())