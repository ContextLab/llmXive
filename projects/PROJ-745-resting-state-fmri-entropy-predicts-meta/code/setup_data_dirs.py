import os
from pathlib import Path

def main():
    """
    Setup the data directory structure for the project.
    Creates data/raw/ and data/processed/ directories.
    """
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files to ensure directories are tracked by git
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()

    print(f"Created directory structure:")
    print(f"  {raw_dir}")
    print(f"  {processed_dir}")

if __name__ == "__main__":
    main()