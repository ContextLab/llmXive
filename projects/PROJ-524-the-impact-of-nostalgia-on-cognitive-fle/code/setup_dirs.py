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
    base_path = config.get('base_path', Path.cwd())

    required_dirs = [
        'data/raw',
        'data/processed',
        'data/results',
        'data/stimuli',
        'contracts',
        'code',
        'tests',
        'paper'
    ]

    created_dirs = []
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir_path))
                log_info(f"Created directory: {dir_path}")
            except PermissionError:
                log_error(f"Permission denied creating directory: {dir_path}")
                raise
            except Exception as e:
                log_error(f"Error creating directory {dir_path}: {e}")
                raise
        else:
            log_info(f"Directory already exists: {dir_path}")

    if not created_dirs:
        log_info("All required directories already exist.")
    else:
        log_info(f"Successfully created {len(created_dirs)} directories.")

    return created_dirs

def main():
    setup_logging()
    log_info("Starting directory creation task (T001)...")
    try:
        create_required_directories()
        log_info("T001 completed successfully.")
    except Exception as e:
        log_error(f"T001 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
