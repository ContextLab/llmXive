import os
from pathlib import Path

def create_directories():
    """Create the root-level data and output directories."""
    root_dirs = [
        "data/raw",
        "data/processed",
        "output/results",
        "output/figures",
        "logs"
    ]
    
    for dir_path in root_dirs:
        full_path = Path(dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked by git
        gitkeep_path = full_path / ".gitkeep"
        gitkeep_path.touch(exist_ok=True)
        
    print(f"Created {len(root_dirs)} root data/output directories with .gitkeep files.")

def main():
    create_directories()
    print("Data directory initialization complete.")

if __name__ == "__main__":
    main()
