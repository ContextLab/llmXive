"""
Setup script to initialize the project directory structure for PROJ-582.
Creates the required directories and .gitkeep files for data folders.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the required directory structure."""
    project_root = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    
    # Ensure the base code directory exists
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Define the required subdirectories
    directories = [
        project_root / "src",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "tests",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    return True

def create_gitkeep_files():
    """Create .gitkeep files in data directories to ensure they are tracked by git."""
    project_root = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
    ]
    
    for directory in data_dirs:
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {directory}")
        else:
            print(f".gitkeep already exists in: {directory}")
    
    return True

def verify_structure():
    """Verify that all required directories exist."""
    project_root = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    
    required_paths = [
        project_root / "src",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "tests",
    ]
    
    all_exist = all(path.exists() and path.is_dir() for path in required_paths)
    
    if all_exist:
        print("✓ All required directories exist.")
    else:
        missing = [str(p) for p in required_paths if not (p.exists() and p.is_dir())]
        print(f"✗ Missing directories: {missing}")
    
    return all_exist

def main():
    """Main entry point for the setup script."""
    print("Initializing project directory structure...")
    
    create_directories()
    create_gitkeep_files()
    
    if verify_structure():
        print("Setup completed successfully.")
        return 0
    else:
        print("Setup failed due to missing directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())