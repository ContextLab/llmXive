"""
Project Structure Initialization Script.

This script creates the complete directory structure for the PROJ-799 project,
including all necessary subdirectories for code, data, tests, docs, and state.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the complete directory structure for the project."""
    # Define the base project directory
    project_root = Path("projects/PROJ-799-statistical-properties-of-integer-partit")
    
    # Define all required subdirectories
    directories = [
        # Core directories
        project_root / "code",
        project_root / "code" / "utils",
        
        # Data directories
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "schemas",
        
        # Test directories
        project_root / "tests",
        project_root / "tests" / "data",
        
        # Documentation
        project_root / "docs",
        
        # State tracking
        project_root / "state" / "projects",
    ]
    
    # Create all directories
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"\nProject structure initialization complete.")
    print(f"Total directories created: {created_count}")
    print(f"Base project directory: {project_root}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
