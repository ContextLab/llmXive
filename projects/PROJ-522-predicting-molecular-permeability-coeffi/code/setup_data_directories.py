"""
Script to create and preserve data directory structure.
Creates .gitkeep files in all data/ subdirectories to ensure
version control preserves the directory structure.
"""
import os
from pathlib import Path

def create_data_directories():
    """Create data directory structure with .gitkeep files."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    
    # Define the required subdirectories
    subdirectories = [
        "raw",
        "processed",
        "external",
        "interim",
        "temp"
    ]
    
    # Create root data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories and .gitkeep files
    for subdir in subdirectories:
        dir_path = data_dir / subdir
        dir_path.mkdir(exist_ok=True)
        
        # Create .gitkeep file
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("# Git keeps this directory\n")
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Exists: {gitkeep_path}")
    
    # Also create .gitkeep in root data directory
    root_gitkeep = data_dir / ".gitkeep"
    if not root_gitkeep.exists():
        root_gitkeep.write_text("# Git keeps this directory\n")
        print(f"Created: {root_gitkeep}")
    
    print(f"\nData directory structure created at: {data_dir}")
    return data_dir

def main():
    """Entry point for script execution."""
    print("Creating data directory structure...")
    create_data_directories()
    print("Done.")

if __name__ == "__main__":
    main()