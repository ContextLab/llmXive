import os
from pathlib import Path
from utils.config import get_path, ensure_dirs_exist

def main():
    """Set up code directories."""
    code_dirs = [
        'code/utils',
        'code/agents',
        'code/analysis',
        'code/dataset'
    ]
    
    for dir_path in code_dirs:
        full_path = get_path(dir_path)
        ensure_dirs_exist(full_path)
        print(f"Created code directory: {full_path}")

if __name__ == "__main__":
    main()
