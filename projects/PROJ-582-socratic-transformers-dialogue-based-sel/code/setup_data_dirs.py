"""
Setup script to create data directories and .gitkeep files for T004.
"""
import os
import sys
from pathlib import Path

def create_gitkeep(path: Path):
    gitkeep_file = path / ".gitkeep"
    if not gitkeep_file.exists():
        gitkeep_file.write_text("# Data directory\n")
        print(f"Created .gitkeep: {gitkeep_file}")
    else:
        print(f".gitkeep already exists: {gitkeep_file}")

def main():
    project_root = Path(__file__).parent
    data_root = project_root / "data"
    
    # Define data subdirectories
    data_dirs = [
        "raw",
        "processed",
        "results"
    ]

    for dir_name in data_dirs:
        full_path = data_root / dir_name
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
        create_gitkeep(full_path)

    print("Data directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())