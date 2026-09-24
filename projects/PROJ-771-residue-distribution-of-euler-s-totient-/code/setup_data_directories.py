import os
from pathlib import Path

def setup_data_directories():
    """
    Create the required data directory structure:
    - data/raw/
    - data/processed/

    Returns:
        dict: Paths to the created directories for verification/logging.
    """
    base_path = Path("data")
    raw_dir = base_path / "raw"
    processed_dir = base_path / "processed"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    return {
        "raw": str(raw_dir),
        "processed": str(processed_dir)
    }

if __name__ == "__main__":
    paths = setup_data_directories()
    print(f"Created directories: {paths}")