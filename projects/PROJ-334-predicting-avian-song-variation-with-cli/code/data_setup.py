import os
import hashlib
from pathlib import Path
import yaml
import csv
from utils import setup_logging

logger = setup_logging("data_setup")

def ensure_directory(dir_path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(dir_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    else:
        logger.debug(f"Directory already exists: {dir_path}")

def initialize_checksums_file(checksums_path: str) -> None:
    """
    Initialize the checksums file with a CSV header if it does not exist.
    If it exists, do nothing (preserve existing data).
    """
    path = Path(checksums_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'sha256_hash'])
        logger.info(f"Initialized checksums file: {checksums_path}")
    else:
        logger.debug(f"Checksums file already exists: {checksums_path}")

def initialize_state_file(state_path: str) -> None:
    """
    Initialize the project state file with an empty artifact_hashes map
    and a default updated_at timestamp if it does not exist.
    If it exists, do nothing (preserve existing state).
    """
    path = Path(state_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        state_data = {
            "artifact_hashes": {},
            "updated_at": "1970-01-01T00:00:00Z"
        }
        with open(path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False)
        logger.info(f"Initialized state file: {state_path}")
    else:
        logger.debug(f"State file already exists: {state_path}")

def main():
    """
    Main entry point to setup the data directory structure and initialize
    the checksums and state files.
    """
    # Define paths relative to the project root (assumed to be parent of 'code')
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    logs_dir = data_dir / "logs"
    checksums_file = data_dir / "checksums.txt"
    
    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "PROJ-334-predicting-avian-song-variation-with-cli.yaml"

    # Create directory structure
    ensure_directory(str(data_dir))
    ensure_directory(str(raw_dir))
    ensure_directory(str(processed_dir))
    ensure_directory(str(logs_dir))
    ensure_directory(str(state_dir))

    # Initialize files
    initialize_checksums_file(str(checksums_file))
    initialize_state_file(str(state_file))

    logger.info("Data directory structure and initialization files setup complete.")

if __name__ == "__main__":
    main()
