import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning, log_error

def create_required_directories():
    """
    Creates all required data directories for the project.
    Directories: data/raw/, data/processed/, data/results/, data/stimuli/,
                 contracts/, code/, tests/, paper/
    """
    config = get_config()
    base_path = Path(config.get('base_path', '.'))

    # Define relative paths based on task T001 description
    required_dirs = [
        base_path / 'data' / 'raw',
        base_path / 'data' / 'processed',
        base_path / 'data' / 'results',
        base_path / 'data' / 'stimuli',
        base_path / 'contracts',
        base_path / 'code',
        base_path / 'tests',
        base_path / 'paper'
    ]

    created_count = 0
    for dir_path in required_dirs:
        try:
            # exist_ok=True ensures we don't error if it already exists
            dir_path.mkdir(parents=True, exist_ok=True)
            log_info(f"Directory created or verified: {dir_path}")
            created_count += 1
        except PermissionError:
            log_error(f"Permission denied creating directory: {dir_path}")
        except Exception as e:
            log_error(f"Error creating directory {dir_path}: {e}")

    log_info(f"Successfully created/verified {created_count} directories.")
    return created_count

def main():
    """Entry point for T001 directory creation."""
    setup_logging()
    log_info("Starting T001: Create required directories")
    create_required_directories()
    log_info("T001 completed successfully")

if __name__ == "__main__":
    main()
