import os
from pathlib import Path
from utils.config import get_path, ensure_dirs_exist

def main():
    """Set up test directories."""
    test_dirs = [
        'tests/unit',
        'tests/integration'
    ]
    
    for dir_path in test_dirs:
        full_path = get_path(dir_path)
        ensure_dirs_exist(full_path)
        print(f"Created test directory: {full_path}")

if __name__ == "__main__":
    main()
