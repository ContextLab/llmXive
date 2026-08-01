import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_processed_directory() -> Path:
    """
    Creates the 'data/processed/' directory if it does not exist.
    Returns the path to the created directory.
    """
    config = get_config()
    # Ensure the base data directory exists first
    data_root = Path(config.get('paths', {}).get('data_root', 'data'))
    ensure_dirs([data_root])

    processed_dir = data_root / 'processed'
    
    if not processed_dir.exists():
        try:
            processed_dir.mkdir(parents=True, exist_ok=True)
            log_info(f"Created directory: {processed_dir}")
            # Create a placeholder .gitkeep to ensure the directory is tracked by git
            gitkeep = processed_dir / '.gitkeep'
            gitkeep.touch()
            log_info(f"Created placeholder file: {gitkeep}")
        except OSError as e:
            log_error(f"Failed to create directory {processed_dir}: {e}")
            raise
    else:
        log_info(f"Directory already exists: {processed_dir}")

    return processed_dir

def main():
    """Entry point for the task."""
    # Setup logging
    logger = setup_logging(level=logging.INFO)
    
    try:
        log_info("Starting T001b: Create data/processed/ directory")
        path = create_processed_directory()
        log_info(f"T001b Complete: {path}")
        return 0
    except Exception as e:
        log_critical(f"T001b Failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
