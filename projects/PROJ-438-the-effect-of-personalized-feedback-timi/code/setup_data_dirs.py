import os
import pathlib
from pathlib import Path

def main():
    """
    Creates the required data directory structure for the project.
    This script ensures that 'raw', 'processed', 'cache', and 'checksums'
    directories exist under the project's 'data' folder, creating .gitkeep
    files to preserve the directory structure in version control.
    """
    # Determine the project root based on the script's location
    # The script is expected to be run from the project root or the code directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    data_dir = project_root / "data"
    subdirs = ["raw", "processed", "cache", "checksums"]

    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)
        
        gitkeep_path = subdir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            # Add a descriptive comment to the .gitkeep file
            with open(gitkeep_path, "w") as f:
                f.write(f"# This directory stores {subdir_name} data.\n")
                f.write("# .gitkeep ensures the directory exists in git.\n")
            print(f"Created directory: {subdir_path}")
        else:
            print(f"Directory already exists: {subdir_path}")

    print("Data directory setup complete.")

if __name__ == "__main__":
    main()