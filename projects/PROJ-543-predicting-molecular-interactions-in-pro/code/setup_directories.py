import os
import sys
from pathlib import Path
from utils.io import setup_logging, log_exception

def create_directories():
    """
    Create the project directory structure for PROJ-543.
    Creates code/, data/raw/, data/processed/, data/results/, tests/, and specs/.
    """
    project_root = Path("projects/PROJ-543-predicting-molecular-interactions-in-pro")
    
    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "tests",
        project_root / "specs",
    ]
    
    created_count = 0
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            logging.info(f"Created directory: {directory}")
        except OSError as e:
            logging.error(f"Failed to create directory {directory}: {e}")
            raise
    
    logging.info(f"Successfully created {created_count} directories.")
    return created_count

def main():
    """Entry point for directory setup."""
    setup_logging()
    try:
        create_directories()
        print("Directory structure created successfully.")
        return 0
    except Exception as e:
        log_exception(e)
        print(f"Error creating directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())