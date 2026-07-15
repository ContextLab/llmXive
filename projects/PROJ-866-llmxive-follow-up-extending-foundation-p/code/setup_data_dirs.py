"""
Data directory initialization script.
Ensures data subdirectories exist for raw, processed, and results.
"""
import os
import sys
from pathlib import Path

def create_data_directories():
    """
    Creates data subdirectories: raw, processed, results.
    """
    root = Path(__file__).parent.parent
    data_root = root / "data"
    
    subdirs = [
        "raw",
        "processed",
        "results"
    ]
    
    created = []
    for subdir in subdirs:
        dir_path = data_root / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(root)))
    
    print(f"Created {len(created)} data subdirectories:")
    for item in sorted(created):
        print(f"  - {item}")
    
    return created

def main():
    """Entry point for script execution."""
    print("Initializing data directories...")
    create_data_directories()
    print("Data directory initialization complete.")

if __name__ == "__main__":
    main()