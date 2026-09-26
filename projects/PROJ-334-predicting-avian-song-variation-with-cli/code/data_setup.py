import os
import hashlib
from pathlib import Path
import yaml
import csv
from utils import setup_logging

def ensure_directory(dir_path: str) -> None:
    """Create directory if it does not exist."""
    path = Path(dir_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def initialize_checksums_file(checksums_path: str) -> None:
    """Initialize the checksums file with a CSV header if it doesn't exist."""
    path = Path(checksums_path)
    if not path.exists():
        ensure_directory(path.parent)
        with open(path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'hash'])

def initialize_state_file(state_path: str) -> None:
    """Initialize the project state file with an empty artifact_hashes map."""
    path = Path(state_path)
    if not path.exists():
        ensure_directory(path.parent)
        state_data = {
            "artifact_hashes": {}
        }
        with open(path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False)

def main():
    """Main entry point for data setup."""
    logger = setup_logging("data_setup")
    
    # Define paths relative to project root
    # Assuming the script is run from the project root or code directory
    # We use a robust way to find the project root or assume relative structure
    base_dir = Path(__file__).resolve().parent.parent
    
    data_raw_dir = base_dir / "data" / "raw"
    data_processed_dir = base_dir / "data" / "processed"
    checksums_file = base_dir / "data" / "checksums.txt"
    state_file = base_dir / "state" / "projects" / "PROJ-334-predicting-avian-song-variation-with-cli.yaml"

    logger.info("Setting up data directory structure...")
    ensure_directory(data_raw_dir)
    ensure_directory(data_processed_dir)
    
    logger.info(f"Initializing checksums file at {checksums_file}")
    initialize_checksums_file(str(checksums_file))
    
    logger.info(f"Initializing state file at {state_file}")
    initialize_state_file(str(state_file))
    
    logger.info("Data setup complete.")

if __name__ == "__main__":
    main()
