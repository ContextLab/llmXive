"""
Project Structure Setup Script for PROJ-503-predicting-plant-defense-compound-produc

This script creates the mandatory directory structure for the plant defense 
compound prediction pipeline. All directories are created relative to the 
project root.

Directories created:
- code/
- data/raw/
- data/processed/
- logs/
- outputs/models/
- docs/
- tests/contract/
- tests/integration/
- tests/unit/
"""

import os
import sys
from pathlib import Path


def setup_project_structure():
    """
    Create the required project directory structure.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the project root relative to this script's location
    # The script is at: code/setup_project.py
    # Project root is: two levels up
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    # Define all required directories relative to project root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "logs",
        "outputs/models",
        "docs",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]
    
    created_dirs = []
    failed_dirs = []
    
    print(f"Setting up project structure at: {project_root}")
    print("-" * 60)
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path.relative_to(project_root)))
            print(f"✓ Created: {full_path.relative_to(project_root)}")
        except OSError as e:
            failed_dirs.append(str(full_path.relative_to(project_root)))
            print(f"✗ Failed to create: {full_path.relative_to(project_root)} - {e}")
    
    print("-" * 60)
    print(f"Summary: {len(created_dirs)} directories created, {len(failed_dirs)} failed")
    
    if failed_dirs:
        print("\nFailed directories:")
        for d in failed_dirs:
            print(f"  - {d}")
        return False
    
    return True


def main():
    """Main entry point for the setup script."""
    success = setup_project_structure()
    if success:
        print("\n✓ Project structure setup completed successfully.")
        sys.exit(0)
    else:
        print("\n✗ Project structure setup failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()