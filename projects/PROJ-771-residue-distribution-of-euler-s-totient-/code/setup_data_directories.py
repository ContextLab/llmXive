"""
Setup script to create the required data directory structure.
Creates data/raw/ and data/processed/ directories.
"""
import os
from pathlib import Path

def setup_data_directories():
    """
    Create the data/raw and data/processed directories if they do not exist.
    Returns a list of created directory paths.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    created_dirs = []

    if not data_dir.exists():
        data_dir.mkdir(parents=True)
        created_dirs.append(str(data_dir))

    if not raw_dir.exists():
        raw_dir.mkdir(parents=True)
        created_dirs.append(str(raw_dir))

    if not processed_dir.exists():
        processed_dir.mkdir(parents=True)
        created_dirs.append(str(processed_dir))

    return created_dirs

if __name__ == "__main__":
    dirs = setup_data_directories()
    print(f"Data directories created/verified: {dirs}")