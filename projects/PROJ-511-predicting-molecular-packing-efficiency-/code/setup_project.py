import os
import sys
from pathlib import Path
import logging

def create_directories():
    """
    Creates the required project directory structure for PROJ-511.
    
    Directories created:
    - code/
    - data/
    - data/raw_cif/
    - models/
    - results/
    - contracts/
    - specs/
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data",
        "data/raw_cif",
        "models",
        "results",
        "contracts",
        "specs"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logging.debug(f"Directory already exists: {dir_path}")
    
    logging.info(f"Project setup complete. Created {created_count} new directories.")
    return created_count

def main():
    """Entry point for the project setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        create_directories()
        logging.info("Directory structure successfully created.")
    except Exception as e:
        logging.error(f"Failed to create directory structure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
