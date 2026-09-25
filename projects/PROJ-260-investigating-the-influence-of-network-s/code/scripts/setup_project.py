import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the full project directory structure as defined in T001a.
    All paths are relative to the project root (current working directory).
    """
    base = Path(".")
    
    # Core directories
    dirs = [
        "src",
        "tests",
        "data/raw",
        "data/derived",
        "outputs",
        "data/metadata",
        "data/derived/topology",
        "data/derived/vdos",
        "data/derived/reference",
        "data/derived/correlation",
        "outputs/figures",
        "outputs/reports",
    ]
    
    created_count = 0
    for dir_path in dirs:
        full_path = base / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSetup complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for script execution."""
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()