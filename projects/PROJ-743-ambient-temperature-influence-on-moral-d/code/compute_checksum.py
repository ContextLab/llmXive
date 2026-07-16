import hashlib
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import yaml

from config import get_path_env_override

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def ensure_state_file_exists(state_file_path: Path) -> None:
    """Ensure the state YAML file exists. If not, create it with an empty structure."""
    if not state_file_path.exists():
        logger.info(f"State file not found. Creating: {state_file_path}")
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file_path, 'w') as f:
            yaml.dump({"project_id": "PROJ-743-ambient-temperature-influence-on-moral-d", "checksums": {}}, f)

def update_state_file(state_file_path: Path, file_key: str, checksum: str) -> None:
    """Update the state YAML file with the new checksum."""
    ensure_state_file_exists(state_file_path)
    
    try:
        with open(state_file_path, 'r') as f:
            state = yaml.safe_load(f)
        if state is None:
            state = {"project_id": "PROJ-743-ambient-temperature-influence-on-moral-d", "checksums": {}}
        
        if "checksums" not in state:
            state["checksums"] = {}
        
        state["checksums"][file_key] = {
            "hash": checksum,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with open(state_file_path, 'w') as f:
            yaml.dump(state, f, default_flow_style=False)
        
        logger.info(f"Updated checksum for {file_key} in {state_file_path}")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        raise

def main():
    """Main entry point to compute and record the checksum."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    sample_file_path = project_root / "data" / "raw" / "era5_sample.h5"
    state_file_path = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"

    # Check if source file exists
    if not sample_file_path.exists():
        logger.error(f"Source file not found: {sample_file_path}. T002 must be completed first.")
        sys.exit(1)

    try:
        checksum = compute_sha256(sample_file_path)
        file_key = "data/raw/era5_sample.h5"
        update_state_file(state_file_path, file_key, checksum)
        logger.info(f"Checksum computed and recorded: {checksum}")
    except Exception as e:
        logger.error(f"Task T003 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
