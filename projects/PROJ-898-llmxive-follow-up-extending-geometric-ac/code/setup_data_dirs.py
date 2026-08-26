"""
Setup data directory structure for the llmXive project.
Creates required directories and .gitkeep files to ensure they are tracked by git.
"""
import os
import sys
from typing import List, Optional

def ensure_gitkeep(directory_path: str) -> bool:
    """
    Ensure a directory exists and contains a .gitkeep file.
    
    Args:
        directory_path: Path to the directory.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        gitkeep_path = os.path.join(directory_path, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write("# Keep this directory in git\n")
        return True
    except Exception as e:
        print(f"Error ensuring gitkeep in {directory_path}: {e}", file=sys.stderr)
        return False

def main() -> int:
    """
    Main entry point to set up the data directory structure.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Define the required data directories relative to the project root
    # Assuming the script is run from the project root or code/ directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_base = os.path.join(base_dir, "data")
    
    directories = [
        os.path.join(data_base, "raw"),
        os.path.join(data_base, "generated"),
        os.path.join(data_base, "results"),
    ]
    
    success = True
    for dir_path in directories:
        if not ensure_gitkeep(dir_path):
            success = False
            print(f"Failed to create {dir_path}")
    
    if success:
        print("Data directory structure created successfully.")
        return 0
    else:
        print("Some directories could not be created.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())