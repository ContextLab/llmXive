"""
Setup script to create all required data and project directories.
Implements Task T001: Create data/raw/, data/processed/, data/results/, data/stimuli/, contracts/, code/, tests/, paper/.
"""
import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning, log_error

def create_required_directories():
    """
    Creates all required directories for the project.
    Returns a list of created directory paths.
    """
    config = get_config()
    project_root = Path(config.get('project_root', '.'))
    
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
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            log_info(f"Directory created: {full_path}")
        except OSError as e:
            log_error(f"Failed to create directory {full_path}: {e}")
            raise
    
    return created_dirs

def main():
    """Main entry point for the directory setup script."""
    setup_logging()
    log_info("Starting directory creation for T001...")
    
    try:
        created = create_required_directories()
        log_info(f"Successfully created {len(created)} directories.")
        log_info(f"Directories: {', '.join(created)}")
        return 0
    except Exception as e:
        log_error(f"Directory creation failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
