import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the required data directory structure:
    - data/raw
    - data/processed

    Creates .gitkeep files in each to ensure they are tracked by git.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    directories = [data_dir, raw_dir, processed_dir]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created directory: {directory}")
            print(f"Created .gitkeep in: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    return True

if __name__ == "__main__":
    success = setup_data_directories()
    if success:
        print("Data directory structure setup complete.")
    else:
        print("Failed to setup data directory structure.")
        exit(1)