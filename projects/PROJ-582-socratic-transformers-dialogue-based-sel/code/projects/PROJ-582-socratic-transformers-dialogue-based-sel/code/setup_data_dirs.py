"""
Script to set up the data directory structure for the Socratic Transformers project.
Creates the required directories and .gitkeep files to ensure they are tracked by git.
"""
import os
import sys
from pathlib import Path

def create_gitkeep(directory: Path) -> None:
    """Create a .gitkeep file in the specified directory if it doesn't exist."""
    gitkeep_path = directory / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        print(f"Created: {gitkeep_path}")
    else:
        print(f"Exists: {gitkeep_path}")

def main() -> int:
    """Main entry point to create the data directory structure."""
    # Determine the project root relative to this script's location
    # Script is at: code/setup_data_dirs.py (or similar in the project tree)
    # We need to create directories under: code/data/
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent  # Assuming script is in code/
    
    data_root = project_root / "data"
    
    # Define the required subdirectories per task T004
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "results"
    ]
    
    print(f"Setting up data directories in: {data_root}")
    
    for dir_path in required_dirs:
        # Create the directory if it doesn't exist
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
        
        # Create .gitkeep file
        create_gitkeep(dir_path)
    
    print("Data directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
