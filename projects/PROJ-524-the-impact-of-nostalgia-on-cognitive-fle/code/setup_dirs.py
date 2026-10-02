import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning, log_error

def create_required_directories():
    """
    Creates all required data and project directories as per T001.
    Directories: data/raw/, data/processed/, data/results/, data/stimuli/,
                 contracts/, code/, tests/, paper/
    """
    config = get_config()
    
    # Define all required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/stimuli",
        "contracts",
        "code",
        "tests",
        "paper"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in required_dirs:
        full_path = Path(config["project_root"]) / dir_path
        try:
            if full_path.exists():
                log_info(f"Directory already exists: {full_path}")
                skipped_count += 1
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                log_info(f"Created directory: {full_path}")
                created_count += 1
        except OSError as e:
            log_error(f"Failed to create directory {full_path}: {e}")
            raise
    
    log_info(f"Directory setup complete. Created: {created_count}, Skipped: {skipped_count}")
    return True

def main():
    """Entry point for directory creation script."""
    setup_logging(level=logging.INFO)
    try:
        success = create_required_directories()
        if success:
            log_info("T001: All required directories created successfully.")
            return 0
        else:
            log_error("T001: Directory creation encountered errors.")
            return 1
    except Exception as e:
        log_error(f"Fatal error in T001: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())