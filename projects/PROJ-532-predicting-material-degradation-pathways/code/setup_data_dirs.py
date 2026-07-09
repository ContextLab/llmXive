"""
Script to initialize the data directory structure for the project.
Creates raw/, processed/, and contracts/ subdirectories under data/.
Updates data/README.md if it doesn't exist or needs versioning.
"""
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    
    # Define required subdirectories
    subdirs = ["raw", "processed", "contracts"]
    
    # Create directories
    for subdir in subdirs:
        dir_path = data_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked in git
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("# Keep directory\n")
    
    print(f"Data directory structure created at: {data_dir}")
    for subdir in subdirs:
        print(f"  - {data_dir / subdir}")

if __name__ == "__main__":
    main()
