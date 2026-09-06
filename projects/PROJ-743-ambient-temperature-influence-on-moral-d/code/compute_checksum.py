import hashlib
import os
import sys
import logging
import yaml
from datetime import datetime, timezone
from pathlib import Path

# Import config to get paths if needed, though we might hardcode based on task
from config import get_path_env_override

def ensure_state_file_exists(state_path: Path):
    """Ensure the state YAML file exists, creating an empty one if necessary."""
    if not state_path.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump({"artifact_hashes": {}, "updated_at": None}, f)
        logging.getLogger(__name__).info(f"Created new state file at {state_path}")

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def update_state_file(state_path: Path, key: str, value: str):
    """Update the state YAML file with a new checksum and timestamp."""
    with open(state_path, 'r', encoding='utf-8') as f:
        try:
            state_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in state file: {e}")

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    state_data["artifact_hashes"][key] = value
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logging.getLogger(__name__).info(f"Updated state file: {key} = {value}")

def main():
    """
    Main entry point for the checksum task T003.
    Computes SHA-256 of data/raw/era5_sample.h5 and updates state.
    """
    logger = logging.getLogger(__name__)
    
    # Define paths relative to project root
    # Assuming the script is run from the project root or we resolve relative to script location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    input_file = project_root / "data" / "raw" / "era5_sample.h5"
    state_file = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    
    logger.info(f"Target file: {input_file}")
    logger.info(f"State file: {state_file}")

    # Ensure state file exists
    ensure_state_file_exists(state_file)

    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        sys.exit(1)

    try:
        checksum = compute_sha256(input_file)
        logger.info(f"Computed checksum: {checksum}")
        
        update_state_file(state_file, "era5_sample", checksum)
        logger.info("State file updated successfully.")
    except Exception as e:
        logger.error(f"Error during checksum process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
