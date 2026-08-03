"""
Project structure setup utilities for llmXive.
Creates required directory structure and .gitkeep files.
"""
import os
import sys
from typing import List, Optional

def create_directory_structure(base_path: Optional[str] = None) -> List[str]:
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: Base directory path. If None, uses current working directory.
        
    Returns:
        List of created directory paths.
    """
    if base_path is None:
        base_path = os.getcwd()
    
    # Define required directories relative to base_path
    directories = [
        "code",
        "data",
        "data/raw",
        "data/generated",
        "data/results",
        "tests",
        "tests/unit",
        "tests/integration",
        "scripts",
        "figures",
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            created_dirs.append(full_path)
    
    return created_dirs

def create_gitkeep_files(base_path: Optional[str] = None) -> List[str]:
    """
    Create .gitkeep files in all data subdirectories to preserve them in git.
    
    Args:
        base_path: Base directory path. If None, uses current working directory.
        
    Returns:
        List of created .gitkeep file paths.
    """
    if base_path is None:
        base_path = os.getcwd()
    
    data_dirs = [
        "data/raw",
        "data/generated",
        "data/results",
    ]
    
    created_files = []
    for dir_path in data_dirs:
        full_dir = os.path.join(base_path, dir_path)
        gitkeep_path = os.path.join(full_dir, ".gitkeep")
        
        # Ensure directory exists first
        os.makedirs(full_dir, exist_ok=True)
        
        # Create .gitkeep file if it doesn't exist
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write("# Keep this directory in git\n")
            created_files.append(gitkeep_path)
    
    return created_files

def main() -> int:
    """
    Main entry point for creating project structure.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        base_path = os.getcwd()
        
        # Create directory structure
        created_dirs = create_directory_structure(base_path)
        if created_dirs:
            print(f"Created {len(created_dirs)} directories:")
            for d in created_dirs:
                print(f"  - {d}")
        else:
            print("All required directories already exist.")
        
        # Create .gitkeep files
        created_files = create_gitkeep_files(base_path)
        if created_files:
            print(f"\nCreated {len(created_files)} .gitkeep files:")
            for f in created_files:
                print(f"  - {f}")
        else:
            print("\nAll .gitkeep files already exist.")
        
        print("\nProject structure setup complete.")
        return 0
        
    except Exception as e:
        print(f"Error setting up project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
