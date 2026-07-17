"""
Project Structure Setup Script for llmXive Automated Science Pipeline.

This script initializes the directory structure for the Heusler Alloy Hysteresis project.
It creates the required directories: code/, tests/, data/, docs/ and their subdirectories.
"""
import os
import sys
from pathlib import Path
import shutil

def get_project_root() -> Path:
    """Get the root directory of the project (parent of code/)."""
    # Assuming this script is located at code/setup_project.py
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    return project_root

def create_directories(project_root: Path) -> None:
    """Create the required project directory structure."""
    dirs_to_create = [
        # Source code structure
        "code/src/ingestion",
        "code/src/preprocessing",
        "code/src/features",
        "code/src/models",
        "code/src/validation",
        "code/src/utils",
        "code/scripts",
        
        # Test structure
        "code/tests/unit",
        "code/tests/integration",
        
        # Data structure
        "data/raw",
        "data/processed",
        "data/external",
        "data/interim",
        
        # Documentation structure
        "docs/reports",
        "docs/notebooks",
        "docs/images",
        
        # Specs structure
        "specs/001-predict-heusler-hysteresis/contracts",
        "specs/001-predict-heusler-hysteresis/plans",
        
        # Output structure
        "figures",
        "code/models"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {full_path.relative_to(project_root)}")
    
    print(f"\nTotal directories created: {created_count}")

def create_gitkeep(project_root: Path) -> None:
    """Create .gitkeep files in all directories to ensure they are tracked by git."""
    dirs_to_keep = [
        "code/src/ingestion",
        "code/src/preprocessing",
        "code/src/features",
        "code/src/models",
        "code/src/validation",
        "code/src/utils",
        "code/scripts",
        "code/tests/unit",
        "code/tests/integration",
        "data/raw",
        "data/processed",
        "data/external",
        "data/interim",
        "docs/reports",
        "docs/notebooks",
        "docs/images",
        "specs/001-predict-heusler-hysteresis/contracts",
        "specs/001-predict-heusler-hysteresis/plans",
        "figures",
        "code/models"
    ]
    
    created_count = 0
    for dir_path in dirs_to_keep:
        full_path = project_root / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.touch()
            created_count += 1
        else:
            print(f".gitkeep already exists in {dir_path}")
    
    print(f"Total .gitkeep files created: {created_count}")

def main() -> None:
    """Main entry point for project setup."""
    print("=== Heusler Alloy Hysteresis Project Setup ===")
    print("Initializing project structure...\n")
    
    project_root = get_project_root()
    print(f"Project root detected at: {project_root}\n")
    
    # Create directory structure
    create_directories(project_root)
    
    # Create .gitkeep files
    print("\nCreating .gitkeep files...")
    create_gitkeep(project_root)
    
    print("\n=== Project Setup Complete ===")
    print("Directory structure has been initialized successfully.")
    print("Next steps:")
    print("  1. Initialize Python environment (requirements.txt)")
    print("  2. Configure linting and formatting tools")
    print("  3. Set up CI/CD pipeline")

if __name__ == "__main__":
    main()
