import os
import sys
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

# Ensure parent directory is in path for imports if run directly
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

STATE_FILE_PATH = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")
ERA5_FULL_FILE_PATH = Path("data/raw/era5_full.parquet")

def ensure_state_file_exists():
    """Ensure the state YAML file exists, creating it with basic structure if not."""
    if not STATE_FILE_PATH.exists():
        logging.info(f"State file {STATE_FILE_PATH} not found. Creating basic structure.")
        STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE_PATH, 'w') as f:
            f.write("project_id: PROJ-743-ambient-temperature-influence-on-moral-d\n")
            f.write("artifact_hashes:\n")
            f.write("  era5_full: null\n")
            f.write("  era5_sample: null\n")
            f.write("updated_at: null\n")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def update_state_file(checksum: str):
    """Update the state YAML file with the new checksum and timestamp."""
    import yaml

    if not STATE_FILE_PATH.exists():
        ensure_state_file_exists()

    with open(STATE_FILE_PATH, 'r') as f:
        data = yaml.safe_load(f)

    # Ensure structure exists
    if 'artifact_hashes' not in data:
        data['artifact_hashes'] = {}
    
    # Update checksum
    data['artifact_hashes']['era5_full'] = checksum
    
    # Update timestamp
    data['updated_at'] = datetime.now(timezone.utc).isoformat()

    with open(STATE_FILE_PATH, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    logging.info(f"Updated state file with checksum: {checksum}")

def main():
    """Main execution for T002e."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info(f"Verifying existence of {ERA5_FULL_FILE_PATH}")
    
    if not ERA5_FULL_FILE_PATH.exists():
        logger.error(f"Critical Error: {ERA5_FULL_FILE_PATH} does not exist. "
                     "Task T002d must complete successfully before T002e can run.")
        # Fail loudly as per constraints
        sys.exit(1)

    logger.info(f"Computing SHA-256 checksum for {ERA5_FULL_FILE_PATH}")
    checksum = compute_sha256(ERA5_FULL_FILE_PATH)
    logger.info(f"Checksum computed: {checksum}")

    logger.info(f"Updating {STATE_FILE_PATH}")
    update_state_file(checksum)

    logger.info("T002e Checksum Full ERA5 File task completed.")

if __name__ == "__main__":
    main()