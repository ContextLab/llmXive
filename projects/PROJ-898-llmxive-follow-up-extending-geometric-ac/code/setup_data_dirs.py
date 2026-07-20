import os
import sys
from typing import List, Optional

def ensure_gitkeep(directory: str) -> bool:
    """
    Ensure the specified directory exists and contains a .gitkeep file.
    
    Args:
        directory: Path to the directory to ensure.
        
    Returns:
        True if the directory and .gitkeep file were successfully created or already existed,
        False otherwise.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Path to .gitkeep file
        gitkeep_path = os.path.join(directory, '.gitkeep')
        
        # Create .gitkeep file if it doesn't exist
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write('# This file ensures the directory is tracked by git\n')
        
        return True
    except Exception as e:
        print(f"Error ensuring gitkeep in {directory}: {e}", file=sys.stderr)
        return False

def main() -> int:
    """
    Main entry point for setting up data directory structure.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Define the required data directories relative to project root
    # Assuming this script is run from the project root
    data_dirs = [
        'data/raw',
        'data/generated',
        'data/results'
    ]
    
    success = True
    for directory in data_dirs:
        if not ensure_gitkeep(directory):
            success = False
            print(f"Failed to setup directory: {directory}", file=sys.stderr)
    
    if success:
        print("Successfully setup data directory structure with .gitkeep files.")
        return 0
    else:
        print("Failed to setup some data directories.", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
