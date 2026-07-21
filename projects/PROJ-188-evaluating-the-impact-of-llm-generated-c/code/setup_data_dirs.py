import os
from pathlib import Path

def create_data_directories():
    """
    Creates the required data directory structure for the project.
    Creates: data/raw/, data/intermediate/, data/processed/
    """
    base_dir = Path("data")
    subdirs = ["raw", "intermediate", "processed"]

    for subdir in subdirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked in git even if empty
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
        print(f"Created directory: {dir_path}")

if __name__ == "__main__":
    create_data_directories()
