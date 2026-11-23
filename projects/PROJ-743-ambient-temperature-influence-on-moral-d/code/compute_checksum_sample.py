import os
import sys
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

# Import existing utilities from the project API surface
# Note: config.py in this project only provides get_path_env_override, not direct path constants.
# We derive paths relative to the project root.
from config import get_path_env_override

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_state_file_exists(state_path: Path) -> None:
    """Ensure the state YAML file exists with basic structure."""
    import yaml
    
    if not state_path.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        initial_data = {
            "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
            "status": "in_progress",
            "artifact_hashes": {},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        with open(state_path, "w") as f:
            yaml.dump(initial_data, f, default_flow_style=False, sort_keys=False)

def update_state_file(state_path: Path, artifact_key: str, checksum: str) -> None:
    """Update the state YAML file with the new checksum and timestamp."""
    import yaml
    
    with open(state_path, "r") as f:
        data = yaml.safe_load(f)
    
    if "artifact_hashes" not in data:
        data["artifact_hashes"] = {}
    
    data["artifact_hashes"][artifact_key] = checksum
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Ensure status is not blocked if we are successfully updating checksums
    if data.get("status") == "blocked":
        data["status"] = "in_progress"
    
    with open(state_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Main entry point for T003: Checksum ERA5 Sample File.
    Computes SHA-256 of data/raw/era5_sample.h5 and updates state file.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("results/logs/checksum_sample.log")
        ]
    )
    logger = logging.getLogger(__name__)

    # Determine paths
    # Assuming project root is the current working directory or one level up from code/
    # Standard convention: code/ and state/ are siblings at root
    project_root = Path(__file__).resolve().parent.parent
    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    sample_file = project_root / "data" / "raw" / "era5_sample.h5"

    # Verify input file exists
    if not sample_file.exists():
        logger.error(f"Sample file not found: {sample_file}")
        logger.error("T003 FAILED: Input file data/raw/era5_sample.h5 is missing.")
        sys.exit(1)

    logger.info(f"Computing checksum for: {sample_file}")
    
    try:
        checksum = compute_sha256(sample_file)
        logger.info(f"Checksum computed: {checksum}")
    except Exception as e:
        logger.error(f"Failed to compute checksum: {e}")
        sys.exit(1)

    # Ensure state file exists
    try:
        ensure_state_file_exists(state_file)
    except Exception as e:
        logger.error(f"Failed to ensure state file exists: {e}")
        sys.exit(1)

    # Update state file
    try:
        update_state_file(state_file, "era5_sample", checksum)
        logger.info(f"State file updated at: {state_file}")
        logger.info("T003 COMPLETED: Checksum recorded successfully.")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
