"""
Project Setup Script for llmXive Automated Science Pipeline.

This script creates the required directory structure and initialization files
for the project: 'Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals'.

Directories created:
- code/ (source code)
- tests/ (test suites)
- data/ (raw, curated, artifacts)
- models/ (trained models)
- reports/ (validation reports, logs)
"""

import os
import sys
from pathlib import Path
from typing import List

# Define the root directory (parent of this script's directory)
# Assuming this script is in code/setup_project.py, root is two levels up
ROOT_DIR = Path(__file__).resolve().parent.parent

# Define required directories relative to root
REQUIRED_DIRS: List[Path] = [
    ROOT_DIR / "code",
    ROOT_DIR / "tests",
    ROOT_DIR / "data" / "raw",
    ROOT_DIR / "data" / "curated",
    ROOT_DIR / "data" / "artifacts",
    ROOT_DIR / "data" / "logs",
    ROOT_DIR / "models",
    ROOT_DIR / "reports",
    ROOT_DIR / "figures",
    ROOT_DIR / "specs",
]

def create_directories() -> None:
    """Create all required directories if they do not exist."""
    created_count = 0
    for dir_path in REQUIRED_DIRS:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(ROOT_DIR)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(ROOT_DIR)}")
    
    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

def create_init_files() -> None:
    """Create __init__.py files in all Python package directories."""
    python_dirs = [
        ROOT_DIR / "code",
        ROOT_DIR / "tests",
        ROOT_DIR / "code" / "utils",
        ROOT_DIR / "code" / "data",
        ROOT_DIR / "code" / "models",
        ROOT_DIR / "code" / "validation",
    ]
    
    # Ensure parent directories exist before creating __init__.py
    for dir_path in python_dirs:
        if dir_path.exists():
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"Created __init__.py in {dir_path.relative_to(ROOT_DIR)}")
            else:
                print(f"__init__.py exists in {dir_path.relative_to(ROOT_DIR)}")

def main() -> None:
    """Main entry point for project setup."""
    print(f"Setting up project structure at: {ROOT_DIR}")
    create_directories()
    create_init_files()
    print("Project setup complete.")

if __name__ == "__main__":
    main()