import os
from pathlib import Path
from utils.config import get_path, ensure_dirs_exist

def main():
    """Set up all project directories."""
    # Code directories
    code_dirs = [
        'code/utils',
        'code/agents',
        'code/analysis',
        'code/dataset'
    ]
    
    # Test directories
    test_dirs = [
        'tests/unit',
        'tests/integration'
    ]
    
    # Data directories
    data_dirs = [
        'data/raw',
        'data/derived',
        'data/logs',
        'data/results',
        'data/figures'
    ]
    
    all_dirs = code_dirs + test_dirs + data_dirs
    
    for dir_path in all_dirs:
        full_path = get_path(dir_path)
        ensure_dirs_exist(full_path)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    main()
