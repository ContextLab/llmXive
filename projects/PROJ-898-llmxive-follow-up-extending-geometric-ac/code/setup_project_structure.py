import os
import sys
from typing import List, Optional

def create_directory_structure(root_path: str, base_dirs: Optional[List[str]] = None) -> None:
    """
    Create the standard project directory structure.
    
    Args:
        root_path: The root directory for the project structure.
        base_dirs: Optional list of base directories to create. Defaults to standard structure.
    """
    if base_dirs is None:
        base_dirs = [
            "code",
            "data/raw",
            "data/generated",
            "data/results",
            "tests",
            "tests/unit",
            "tests/integration",
            "scripts",
            "specs"
        ]
    
    for directory in base_dirs:
        full_path = os.path.join(root_path, directory)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_gitkeep_files(root_path: str, target_dirs: Optional[List[str]] = None) -> None:
    """
    Create .gitkeep files in specified directories to ensure they are tracked by git.
    
    Args:
        root_path: The root directory of the project.
        target_dirs: List of directories relative to root_path to place .gitkeep files.
    """
    if target_dirs is None:
        target_dirs = [
            "data/raw",
            "data/generated",
            "data/results",
            "tests/unit",
            "tests/integration"
        ]
    
    for directory in target_dirs:
        full_path = os.path.join(root_path, directory, ".gitkeep")
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Create .gitkeep file if it doesn't exist
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                f.write("# Keep this directory in git\n")
            print(f"Created .gitkeep: {full_path}")
        else:
            print(f".gitkeep already exists: {full_path}")

def main() -> None:
    """Main entry point for creating project structure."""
    # Determine root path based on script location or argument
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        # Default to current directory
        root_path = "."
    
    print(f"Setting up project structure in: {os.path.abspath(root_path)}")
    
    create_directory_structure(root_path)
    create_gitkeep_files(root_path)
    
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
