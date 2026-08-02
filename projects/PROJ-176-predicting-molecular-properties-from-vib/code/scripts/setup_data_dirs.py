"""
Script to initialize the project data directory structure.
Creates raw/, preprocessed/, and external/ subdirectories under data/.
"""
import os
from pathlib import Path

def main():
    """Create the required data directory structure."""
    # Determine project root (assuming script is in code/scripts/)
    current_dir = Path(__file__).resolve()
    project_root = current_dir.parent.parent.parent
    
    data_root = project_root / "data"
    subdirs = ["raw", "preprocessed", "external"]
    
    for subdir in subdirs:
        dir_path = data_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create a .gitkeep file to ensure the directory is tracked by git
        keep_file = dir_path / ".gitkeep"
        keep_file.write_text("# Directory kept for project structure\n")
        print(f"Created: {dir_path}")
    
    print(f"Data directory structure initialized at: {data_root}")

if __name__ == "__main__":
    main()