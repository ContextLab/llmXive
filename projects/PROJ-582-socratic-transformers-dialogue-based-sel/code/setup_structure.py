"""
Task T001: Initialize project directory structure.

Creates the required directory hierarchy for the Socratic Transformers project
and places .gitkeep files in data directories to ensure they are tracked by git.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the project directory structure."""
    # Define the root path for this specific project
    project_root = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    
    # Define subdirectories to create
    subdirs = [
        "src",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]
    
    created_paths = []
    
    for subdir in subdirs:
        full_path = project_root / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(full_path))
        print(f"Created directory: {full_path}")
        
        # Create .gitkeep in data directories
        if subdir.startswith("data"):
            gitkeep_path = full_path / ".gitkeep"
            gitkeep_path.touch(exist_ok=True)
            print(f"  -> Created .gitkeep in {full_path}")
    
    return created_paths

def verify_structure():
    """Verify that the required directories exist."""
    project_root = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    
    required_dirs = [
        project_root / "src",
        project_root / "data/raw",
        project_root / "data/processed",
        project_root / "data/results",
        project_root / "tests"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if not dir_path.is_dir():
            print(f"ERROR: Missing directory {dir_path}")
            all_exist = False
        else:
            print(f"Verified: {dir_path}")
    
    return all_exist

def main():
    """Main entry point for the script."""
    print("Initializing project directory structure for PROJ-582...")
    
    # Create directories
    created = create_directories()
    print(f"\nSuccessfully created {len(created)} directories.")
    
    # Verify structure
    print("\nVerifying structure...")
    if verify_structure():
        print("\n✅ All directories verified successfully.")
        return 0
    else:
        print("\n❌ Verification failed. Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())