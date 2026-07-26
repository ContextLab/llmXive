"""
Script to ensure all required project directories exist.
"""
import os
import sys
from config import ensure_directories

def main():
    """Create all necessary directories."""
    from config import get_config
    cfg = get_config()
    
    dirs = [
        cfg['data_raw_dir'],
        cfg['data_processed_dir'],
        cfg['data_assets_dir'],
        cfg['code_dir'],
        cfg['artifacts_dir'],
        cfg['tests_dir']
    ]
    
    ensure_directories(dirs)
    print("All directories created or verified.")

if __name__ == "__main__":
    main()
