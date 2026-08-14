import os
import sys
from pathlib import Path

def ensure_dir(path: str) -> Path:
    """Ensures a directory exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def create_init_file(path: Path) -> None:
    """Creates an __init__.py file in the directory."""
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.touch()

def main():
    """Main entry point for project setup."""
    # Create standard directories
    dirs = ["code", "tests", "data/raw", "data/processed", "code/utils", "code/models"]
    for d in dirs:
        ensure_dir(d)
    
    # Create __init__.py files
    for d in dirs:
        create_init_file(Path(d))
    
    print("Project structure created.")

if __name__ == "__main__":
    main()