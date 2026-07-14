import os
import json
from pathlib import Path

def main():
    """
    Creates the required project directory structure for the disorder study.
    Ensures all necessary folders exist and initializes the provenance metadata file.
    """
    # Determine the project root relative to this script's location
    # The script is at code/setup_data_dirs.py, so root is parent of 'code'
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define the directory structure to create
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/metadata",
        "tests",
        "docs",
        "specs"
    ]

    created = []
    for d in dirs:
        full_path = project_root / d
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path.relative_to(project_root)))
        else:
            # Ensure it is a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

    # Initialize the provenance metadata file if it doesn't exist
    metadata_dir = project_root / "data" / "metadata"
    provenance_file = metadata_dir / "provenance.json"
    
    if not provenance_file.exists():
        initial_data = {
            "version": "1.0.0",
            "created_at": "2026-06-07T00:00:00Z",
            "entries": []
        }
        with open(provenance_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
        created.append("data/metadata/provenance.json")
    
    if created:
        print(f"Created directories and files: {', '.join(created)}")
    else:
        print("All required directories and files already exist.")

if __name__ == "__main__":
    main()