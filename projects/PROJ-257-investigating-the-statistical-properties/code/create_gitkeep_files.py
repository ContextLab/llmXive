import os
from pathlib import Path

def create_gitkeep_files():
    """
    Create .gitkeep files in the required directories to ensure they are tracked
    by git even if they are empty.
    
    Target directories:
    - src/data/
    - src/analysis/
    - src/viz/
    - src/utils/
    """
    base_path = Path.cwd()
    
    # Define the relative paths for the directories requiring .gitkeep
    target_dirs = [
        base_path / "src" / "data",
        base_path / "src" / "analysis",
        base_path / "src" / "viz",
        base_path / "src" / "utils"
    ]
    
    created_files = []
    
    for dir_path in target_dirs:
        if not dir_path.exists():
            print(f"Warning: Directory {dir_path} does not exist. Skipping .gitkeep creation.")
            continue
        
        gitkeep_path = dir_path / ".gitkeep"
        try:
            # Create the file if it doesn't exist, or touch it if it does
            gitkeep_path.touch(exist_ok=True)
            created_files.append(gitkeep_path)
            print(f"Created: {gitkeep_path}")
        except OSError as e:
            print(f"Error creating {gitkeep_path}: {e}")
    
    return created_files

def main():
    """Entry point for the script."""
    print("Starting .gitkeep file creation for src subdirectories...")
    files = create_gitkeep_files()
    if files:
        print(f"Successfully created {len(files)} .gitkeep files.")
    else:
        print("No .gitkeep files were created.")

if __name__ == "__main__":
    main()