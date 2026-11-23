import os
from pathlib import Path
from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir, get_results_dir, get_mock_data_dir
from logging_config import setup_logging, get_logger

def create_directory_structure():
    """
    Create the required data sub-directories:
    - data/raw/
    - data/processed/
    - data/consent/
    - data/results/
    - data/mock/

    Each directory will contain a .gitkeep file to ensure they are tracked by git.
    """
    logger = get_logger()
    logger.info("Starting directory structure creation...")

    # Define the directories relative to the project root
    project_root = get_project_root()
    
    # Using the config functions to ensure paths are correct
    # Note: get_data_dir() returns the root 'data/' directory
    data_dir = get_project_root() / "data"
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_data_dir()
    consent_dir = get_consent_dir()
    results_dir = get_results_dir()
    mock_dir = get_mock_data_dir()

    directories = [raw_dir, processed_dir, consent_dir, results_dir, mock_dir]

    created_count = 0
    for dir_path in directories:
        try:
            # Create the directory if it doesn't exist (parents=True for nested)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            
            # Create .gitkeep file
            gitkeep_path = dir_path / ".gitkeep"
            gitkeep_path.touch(exist_ok=True)
            logger.info(f"Created .gitkeep in: {dir_path}")
            created_count += 1
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise

    logger.info(f"Successfully created {created_count} directories with .gitkeep files.")
    return True

def main():
    """Main entry point for the script."""
    setup_logging()
    try:
        create_directory_structure()
        print("Directory structure created successfully.")
        return 0
    except Exception as e:
        print(f"Error creating directory structure: {e}")
        return 1

if __name__ == "__main__":
    exit(main())