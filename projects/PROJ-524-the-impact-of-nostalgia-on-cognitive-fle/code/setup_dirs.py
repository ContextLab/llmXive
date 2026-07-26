"""
Master script to create all required project directories.
"""
import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def main():
    setup_logging(level=logging.INFO)
    config = get_config()
    base_dir = Path(config.get('base_dir', '.'))
    
    dirs = [
        base_dir / 'data' / 'raw',
        base_dir / 'data' / 'processed',
        base_dir / 'data' / 'results',
        base_dir / 'data' / 'stimuli',
        base_dir / 'code',
        base_dir / 'tests',
    ]
    
    try:
        ensure_dirs([str(d) for d in dirs])
        log_info("All project directories created/verified.")
        return 0
    except Exception as e:
        log_warning(f"Failed to create directories: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())