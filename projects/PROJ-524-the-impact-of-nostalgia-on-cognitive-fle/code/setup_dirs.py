"""
Task T001: Create all required data directories.

Creates the following directory structure:
- data/raw/
- data/processed/
- data/results/
- data/stimuli/
- contracts/
- code/ (ensures existence)
- tests/
- paper/
"""
import os
import sys
import logging
from pathlib import Path

from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning


def main():
    """Create all required directories for the project."""
    # Setup logging
    logger = setup_logging(level=logging.INFO)
    
    # Get base path from config
    config = get_config()
    base_path = Path(config.get("base_path", "."))
    
    # Define required directories relative to base path
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/stimuli",
        "contracts",
        "code",
        "tests",
        "paper",
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        
        try:
            if not dir_path.exists():
              dir_path.mkdir(parents=True, exist_ok=True)
              log_info(logger, f"Created directory: {dir_path}")
              created_count += 1
            else:
                log_info(logger, f"Directory already exists: {dir_path}")
                skipped_count += 1
        except OSError as e:
            log_warning(logger, f"Failed to create directory {dir_path}: {e}")
    
    log_info(logger, f"Directory setup complete. Created: {created_count}, Skipped: {skipped_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
