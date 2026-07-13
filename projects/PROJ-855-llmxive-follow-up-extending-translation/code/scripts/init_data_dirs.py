"""
Script to initialize the data directory structure and checksums file.
Creates data/raw/, data/processed/, and ensures data/checksums.json exists.
"""
import json
import os
from pathlib import Path

def main():
    """Initialize data directories and checksums registry."""
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    checksums_file = data_dir / "checksums.json"

    # Create directory structure
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Initialize or update checksums.json
    if checksums_file.exists():
        with open(checksums_file, 'r') as f:
            try:
                checksums = json.load(f)
            except json.JSONDecodeError:
                checksums = {"files": {}, "last_updated": None}
    else:
        checksums = {"files": {}, "last_updated": None}

    # Ensure structure is valid even if file was empty/corrupt
    if "files" not in checksums:
        checksums["files"] = {}
    if "last_updated" not in checksums:
        checksums["last_updated"] = None

    # Write back to ensure valid JSON structure
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f, indent=2)

    print(f"Initialized data directory structure:")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")
    print(f"  - {checksums_file}")

if __name__ == "__main__":
    main()
