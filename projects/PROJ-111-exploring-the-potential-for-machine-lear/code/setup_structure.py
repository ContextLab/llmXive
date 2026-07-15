"""
Project structure initialization script for llmXive research pipeline.
Creates the required directory hierarchy and initializes Python packages.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to the script location or current working directory
# Assuming the script is run from the project root or the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Required directories relative to project root
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "specs/001-gene-regulation/contracts",
]

def create_directories():
    """Create all required directories if they do not exist."""
    created = []
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")
    return created

def create_init_files():
    """Create __init__.py files in code and tests directories to make them packages."""
    init_paths = [
        "code/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/contract/__init__.py",
        "specs/001-gene-regulation/__init__.py",
        "specs/001-gene-regulation/contracts/__init__.py",
    ]
    created = []
    for init_path in init_paths:
        full_path = PROJECT_ROOT / init_path
        if not full_path.exists():
            full_path.touch()
            created.append(str(full_path))
    
    if created:
        print(f"Created __init__.py files: {', '.join(created)}")
    else:
        print("All __init__.py files already exist.")
    return created

def main():
    """Entry point for creating the project structure."""
    print(f"Initializing project structure at: {PROJECT_ROOT}")
    create_directories()
    create_init_files()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
