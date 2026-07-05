import os
from pathlib import Path

def setup_directories():
    """Create the required project directory structure."""
    base_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "specs",
        "state",
        "figures"
    ]
    
    for dir_path in base_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

if __name__ == "__main__":
    setup_directories()
