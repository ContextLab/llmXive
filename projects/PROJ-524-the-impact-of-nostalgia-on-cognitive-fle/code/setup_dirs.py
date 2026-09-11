"""
Task T001: Create all required data directories.
Creates: data/raw/, data/processed/, data/results/, data/stimuli/, contracts/, code/, tests/, paper/
"""
import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_required_directories():
    """
    Creates the standard directory structure required for the project.
    Returns a list of created directory paths.
    """
    config = get_config()
    base_dir = config.get('base_dir', Path.cwd())
    
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
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            log_info(f"Created directory: {full_path}")
            created_dirs.append(str(full_path))
        else:
            log_info(f"Directory already exists: {full_path}")
            created_dirs.append(str(full_path))
    
    return created_dirs

def main():
    """
    Main entry point for T001 execution.
    """
    # Setup logging
    log_level = get_config().get('log_level', 'INFO')
    logger = setup_logging(level=log_level)
    
    log_info("Starting T001: Create required data directories")
    
    try:
        created = create_required_directories()
        log_info(f"Successfully created/verified {len(created)} directories")
        return 0
    except Exception as e:
        log_error(f"Failed to create directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())