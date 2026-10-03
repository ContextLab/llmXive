import os
import sys
import csv
import hashlib
from pathlib import Path
import yaml

def ensure_directory(path: str) -> None:
    """Create a directory if it does not exist."""
    dir_path = Path(path)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    else:
        print(f"Directory already exists: {dir_path}")

def initialize_checksums_file(path: str) -> None:
    """Initialize the checksums file with a CSV header if it doesn't exist."""
    file_path = Path(path)
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'sha256_hash'])
        print(f"Initialized checksums file: {file_path}")
    else:
        print(f"Checksums file already exists: {file_path}")

def initialize_state_file(path: str) -> None:
    """Initialize the project state YAML file with empty artifact_hashes and default timestamp."""
    file_path = Path(path)
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        state_data = {
            'artifact_hashes': {},
            'updated_at': '1970-01-01T00:00:00Z'
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(state_data, f, default_flow_style=False)
        print(f"Initialized state file: {file_path}")
    else:
        print(f"State file already exists: {file_path}")

def main():
    """Main entry point to create directory structure and initialize files."""
    # Project root relative to where this script is run
    project_root = Path("projects/PROJ-334-predicting-avian-song-variation-with-cli")
    
    # Define directories to create
    directories = [
        project_root / "data",
        project_root / "code",
        project_root / "tests"
    ]
    
    # Create directories
    for directory in directories:
        ensure_directory(str(directory))
    
    # Initialize checksums file
    checksums_path = project_root / "data" / "checksums.txt"
    initialize_checksums_file(str(checksums_path))
    
    # Initialize state file
    state_path = project_root / "state" / "projects" / "PROJ-334-predicting-avian-song-variation-with-cli.yaml"
    initialize_state_file(str(state_path))
    
    print("Directory structure and initial files created successfully.")

if __name__ == "__main__":
    main()
