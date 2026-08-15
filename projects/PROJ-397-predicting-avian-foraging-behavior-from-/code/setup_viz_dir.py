import os
import sys
from pathlib import Path

# Ensure the project root is in the path so we can import utils
# Assuming this script runs from the project root or code/
# We add the parent of 'code' to sys.path if running from 'code'
current_file = Path(__file__).resolve()
code_dir = current_file.parent
project_root = code_dir.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_viz_dir, ensure_directories

def main():
    """
    Initialize the viz directory structure for the project.
    Creates the directory defined in config and places a .gitkeep file inside.
    """
    print("Initializing viz directory...")
    
    # Get the path to the viz directory using the project's config
    viz_dir = get_viz_dir()
    
    # Ensure the directory exists (and parents if needed)
    ensure_directories([viz_dir])
    
    # Create the .gitkeep file to ensure the directory is tracked by git
    gitkeep_path = viz_dir / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        print(f"Created .gitkeep at: {gitkeep_path}")
    else:
        print(f".gitkeep already exists at: {gitkeep_path}")
    
    print(f"Viz directory initialized successfully at: {viz_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
