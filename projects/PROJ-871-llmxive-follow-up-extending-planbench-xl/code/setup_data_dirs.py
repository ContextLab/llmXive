import os
import sys
from pathlib import Path
from utils.config import get_project_root, get_path, ensure_dirs_exist

def main():
    """Set up data directories."""
    data_dirs = [
        'data/raw',
        'data/derived',
        'data/logs',
        'data/results',
        'data/figures'
    ]
    
    for dir_path in data_dirs:
        full_path = get_path(dir_path)
        ensure_dirs_exist(full_path)
        print(f"Created data directory: {full_path}")

if __name__ == "__main__":
    main()
