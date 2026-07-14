"""
Setup script to create the required directory structure for the codebase.
This script creates the main code directory and subdirectories for models and utils.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Create the following directory structure:
    - code/
    - code/models/
    - code/utils/
    
    Prints confirmation messages and exits with 0 on success.
    """
    base_path = Path(__file__).parent.parent
    code_dir = base_path / "code"
    models_dir = code_dir / "models"
    utils_dir = code_dir / "utils"

    directories = [code_dir, models_dir, utils_dir]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory.relative_to(base_path)}")

    print("Directory setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
