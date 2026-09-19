"""
Setup script to create the 'code/' directory structure.
This script ensures the 'code/' directory exists for the project.
"""
import os
from pathlib import Path

def main():
    """Create the code/ directory if it doesn't exist."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        code_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {code_dir}")
    else:
        print(f"Directory already exists: {code_dir}")
    
    # Ensure subdirectories for utils are present
    utils_dir = code_dir / "utils"
    if not utils_dir.exists():
        utils_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {utils_dir}")
    
    return 0

if __name__ == "__main__":
    exit(main())
