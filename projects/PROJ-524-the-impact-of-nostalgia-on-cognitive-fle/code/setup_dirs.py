import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_required_directories():
    """
    Creates all required data directories for the project:
    - data/raw/
    - data/processed/
    - data/results/
    - data/stimuli/
    - contracts/
    - code/
    - tests/
    - paper/
    """
    config = get_config()
    root = Path(config.get('root_dir', '.'))
    
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
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            log_info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            log_info(f"Directory already exists: {dir_path}")
    
    log_info(f"Successfully created/verified {created_count}/{len(required_dirs)} directories.")
    return created_count

def main():
    setup_logging()
    log_info("Starting directory creation task (T001)...")
    count = create_required_directories()
    log_info(f"Task T001 completed. Created {count} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
