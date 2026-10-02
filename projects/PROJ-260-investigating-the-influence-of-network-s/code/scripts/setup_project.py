"""
Script to initialize the project directory structure for PROJ-260.
Creates all required directories for data, code, tests, and outputs.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the full project directory hierarchy."""
    base = Path(__file__).resolve().parent.parent.parent
    
    # Define all required directories
    directories = [
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
    
    created = []
    for dir_path in directories:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path.relative_to(base)))
    
    return created

def main():
    """Main entry point."""
    print("Creating project directory structure...")
    created = create_directories()
    print(f"Created {len(created)} directories:")
    for d in sorted(created):
        print(f"  - {d}")
    print("Directory structure initialization complete.")

if __name__ == "__main__":
    main()
