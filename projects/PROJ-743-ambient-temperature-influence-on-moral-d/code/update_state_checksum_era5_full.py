"""
Task T002d: Checksum Full ERA5 File
Compute SHA-256 checksum of data/raw/era5_full.h5 and record it under
artifact_hashes.era5_full in state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml.
Also update the updated_at timestamp.
"""
import os
import sys
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
import yaml

# Add project root to path to allow imports if needed, though this script is self-contained
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path_env_override

# Configure logging
def setup_logging():
    log_dir = project_root / "results" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "data_validation_log.txt"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def update_state_file(state_path: Path, checksum: str, artifact_key: str):
    """Update the state YAML file with the new checksum and timestamp."""
    # Ensure state directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state or create new
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.error(f"Error parsing existing state file: {e}")
                state_data = {}
    else:
        state_data = {}

    # Ensure 'artifact_hashes' key exists
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}

    # Update the specific checksum
    state_data['artifact_hashes'][artifact_key] = checksum

    # Update timestamp
    state_data['updated_at'] = datetime.now(timezone.utc).isoformat()

    # Write back to file
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated state file at {state_path}")
    logger.info(f"Set {artifact_key} checksum to {checksum}")
    logger.info(f"Updated timestamp to {state_data['updated_at']}")

def main():
    # Define paths
    file_path = project_root / "data" / "raw" / "era5_full.h5"
    state_path = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    artifact_key = "era5_full"

    # Check if file exists
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        logger.error("T002d FAILED: Cannot compute checksum for missing file.")
        sys.exit(1)

    logger.info(f"Computing SHA-256 checksum for: {file_path}")
    
    try:
        checksum = compute_sha256(file_path)
        logger.info(f"Checksum computed: {checksum}")
        
        update_state_file(state_path, checksum, artifact_key)
        
        logger.info("T002d COMPLETED successfully.")
        
    except Exception as e:
        logger.error(f"Error during checksum computation or state update: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()