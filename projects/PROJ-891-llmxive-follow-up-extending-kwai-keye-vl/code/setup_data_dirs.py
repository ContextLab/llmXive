import os
from pathlib import Path

def main():
    """
    Creates the required data directory structure for the project.
    Directories created:
      - data/raw
      - data/distorted
      - data/outputs
      - data/metadata
    """
    base_dir = Path("data")
    subdirs = ["raw", "distorted", "outputs", "metadata"]

    for subdir in subdirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create a .gitkeep file in each to ensure they are tracked by git
    for subdir in subdirs:
        dir_path = base_dir / subdir / ".gitkeep"
        dir_path.touch()

if __name__ == "__main__":
    main()