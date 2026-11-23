import json
import os
from pathlib import Path

def main():
    """
    Initialize the data directory structure and the checksums registry file.
    Creates:
      - data/raw/
      - data/processed/
      - data/checksums.json (initialized with empty structure)
    """
    # Define the project root relative to the script location (code/scripts/)
    # Assuming standard layout: code/scripts/init_data_dirs.py -> project root is parent of code
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    checksums_file = data_dir / "checksums.json"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Initialize checksums.json if it doesn't exist or is empty
    if not checksums_file.exists():
        initial_data = {
            "version": "1.0.0",
            "files": {}
        }
        with open(checksums_file, "w") as f:
            json.dump(initial_data, f, indent=2)
        print(f"Initialized {checksums_file}")
    else:
        print(f"Checksums file already exists at {checksums_file}")

    print(f"Data directory structure ready:")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")
    print(f"  - {checksums_file}")

if __name__ == "__main__":
    main()