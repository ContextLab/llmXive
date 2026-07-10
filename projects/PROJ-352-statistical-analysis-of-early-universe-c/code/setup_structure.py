"""
Setup script for the project structure.
"""
import os
import sys
from pathlib import Path

def main():
    """Initialize the project structure."""
    print("Project structure initialization...")
    
    # Ensure we are in the project root
    project_root = Path.cwd()
    if not (project_root / "requirements.txt").exists():
        print("Warning: Not in project root or requirements.txt not found.")
    
    # Run directory setup
    from setup_data_dirs import main as setup_dirs
    setup_dirs()
    
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()