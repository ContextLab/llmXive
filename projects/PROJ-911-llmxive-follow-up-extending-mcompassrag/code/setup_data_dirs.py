"""
Setup script to initialize the data directory structure for the project.
Creates raw, processed, and results directories as defined in config.
"""
import os
from pathlib import Path
from code.config import DATA_DIR, PROJECT_ROOT, RAW_DIR, PROCESSED_DIR, RESULTS_DIR


def setup_directories():
    """
    Creates the required directory structure for data storage.
    Ensures data/raw, data/processed, and data/results exist.
    """
    directories = [
        RAW_DIR,
        PROCESSED_DIR,
        RESULTS_DIR
    ]

    created_count = 0
    for dir_path in directories:
        path_obj = Path(dir_path)
        if not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {path_obj}")
        else:
            print(f"Directory already exists: {path_obj}")

    print(f"Data directory setup complete. {created_count} new directories created.")
    return True


if __name__ == "__main__":
    setup_directories()