"""
Script to create the required data directory structure for the project.
Creates: data/raw/, data/processed/, data/consent/
"""
import os
from pathlib import Path
from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir


def create_directories():
    """Create the data directory structure if it doesn't exist."""
    project_root = get_project_root()
    
    # Define the directories to create
    directories = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Data directory setup complete. {created_count} new directory(ies) created.")
    return True


def main():
    """Main entry point for the script."""
    try:
        success = create_directories()
        if success:
            print("SUCCESS: Data directories created successfully.")
            return 0
        else:
            print("ERROR: Failed to create data directories.")
            return 1
    except Exception as e:
        print(f"ERROR: An exception occurred: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
