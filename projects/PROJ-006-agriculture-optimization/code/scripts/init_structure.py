import os
from pathlib import Path

def ensure_dir(path_str):
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path_str)
    path.mkdir(parents=True, exist_ok=True)
    return path

def main():
    """Create the project directory structure."""
    root = Path.cwd()
    dirs = [
        'src',
        'tests',
        'contracts',
        'data',
        'data/raw',
        'data/processed',
        'data/logs',
        'reports'
    ]
    for d in dirs:
        ensure_dir(root / d)
        print(f"Created directory: {root / d}")

if __name__ == '__main__':
    main()
