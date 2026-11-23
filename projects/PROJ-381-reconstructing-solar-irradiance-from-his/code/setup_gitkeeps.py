import os
from pathlib import Path

def main():
    """
    Creates .gitkeep files in data directories to ensure they are tracked by git.
    """
    root = Path(__file__).resolve().parent.parent
    data_dirs = ["data/raw", "data/processed"]
    
    for dir_path in data_dirs:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = full_path / ".gitkeep"
        
        if not gitkeep_path.exists():
            gitkeep_path.write_text("# This file ensures the directory is tracked by git\n")
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Exists: {gitkeep_path}")

if __name__ == "__main__":
    main()
