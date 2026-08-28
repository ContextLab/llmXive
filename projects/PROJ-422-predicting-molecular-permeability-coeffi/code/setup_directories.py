import os
import sys
from pathlib import Path
import logging
import argparse

# Configure logging to match project standards
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def create_directories(base_path: str, logger: logging.Logger):
    """
    Creates the required directory structure for the molecular permeability project.
    Ensures all specified paths exist and are writable.
    """
    base = Path(base_path)
    
    # Define the required directory structure
    required_dirs = [
        "code/data",
        "code/models",
        "code/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "results",
        "tests/unit",
        "tests/integration"
    ]

    created_count = 0
    existing_count = 0

    for dir_name in required_dirs:
        full_path = base / dir_name
        
        if full_path.exists():
            existing_count += 1
            logger.info(f"Directory already exists: {full_path}")
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                # Create a .gitkeep file to ensure the directory is tracked by git
                # and to serve as evidence that the directory was intentionally created.
                gitkeep = full_path / ".gitkeep"
                gitkeep.touch()
                created_count += 1
                logger.info(f"Created directory: {full_path} (with .gitkeep)")
            except OSError as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                raise

    logger.info(f"Directory setup complete. Created: {created_count}, Existed: {existing_count}")
    return True

def verify_structure(base_path: str, logger: logging.Logger) -> bool:
    """
    Verifies that all required directories exist.
    Returns True if all exist, False otherwise.
    """
    base = Path(base_path)
    required_dirs = [
        "code/data", "code/models", "code/analysis",
        "data/raw", "data/processed", "data/interim",
        "results", "tests/unit", "tests/integration"
    ]

    all_exist = True
    for dir_name in required_dirs:
        full_path = base / dir_name
        if not full_path.exists():
            logger.error(f"Missing required directory: {full_path}")
            all_exist = False
        elif not full_path.is_dir():
            logger.error(f"Path exists but is not a directory: {full_path}")
            all_exist = False
        
        # Check for .gitkeep to ensure it wasn't just an empty folder left by accident
        # or to confirm intentional creation if we created it.
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            # If we created it, .gitkeep should be there. 
            # If it existed before, we might not have added one, but let's ensure it exists now for safety.
            try:
                gitkeep.touch()
                logger.debug(f"Ensured .gitkeep exists in {full_path}")
            except Exception as e:
                logger.warning(f"Could not write .gitkeep to {full_path}: {e}")

    return all_exist

def main():
    parser = argparse.ArgumentParser(description="Setup project directory structure.")
    parser.add_argument(
        "--base-path", 
        default="projects/PROJ-422-predicting-molecular-permeability-coeffi",
        help="Base path for the project directory structure."
    )
    args = parser.parse_args()

    logger = setup_logging()
    logger.info(f"Starting directory setup for: {args.base_path}")

    try:
        # Create directories
        create_directories(args.base_path, logger)
        
        # Verify structure
        if verify_structure(args.base_path, logger):
            logger.info("SUCCESS: All required directories verified.")
            return 0
        else:
            logger.error("FAILURE: Some directories are missing.")
            return 1
    except Exception as e:
        logger.exception(f"Fatal error during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
