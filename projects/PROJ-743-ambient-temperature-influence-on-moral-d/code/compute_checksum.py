import hashlib
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import yaml

from config import get_path_env_override

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def ensure_state_file_exists(state_file_path: str) -> Path:
    """
    Ensure the state YAML file exists. If not, create it with an empty structure.

    Args:
        state_file_path: Path to the state YAML file.

    Returns:
        Path object for the state file.
    """
    path = Path(state_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not path.exists():
        logger.info(f"Creating new state file at {state_file_path}")
        initial_data = {
            "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
            "created_at": datetime.utcnow().isoformat(),
            "checksums": {}
        }
        with open(path, 'w') as f:
            yaml.dump(initial_data, f, default_flow_style=False)
    else:
        logger.info(f"State file already exists at {state_file_path}")
        
    return path

def update_state_file(state_file_path: str, file_path: str, checksum: str) -> None:
    """
    Update the state YAML file with the new checksum entry.

    Args:
        state_file_path: Path to the state YAML file.
        file_path: Path to the file whose checksum is being recorded.
        checksum: The SHA-256 checksum string.
    """
    path = Path(state_file_path)
    
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    if 'checksums' not in data:
        data['checksums'] = {}
    
    # Store relative path for portability
    relative_path = str(Path(file_path).relative_to(Path.cwd().parent)) if 'state' not in str(file_path) else str(file_path)
    
    data['checksums'][relative_path] = {
        "algorithm": "sha256",
        "value": checksum,
        "recorded_at": datetime.utcnow().isoformat()
    }
    
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    
    logger.info(f"Updated state file with checksum for {relative_path}")

def main():
    """
    Main entry point for the checksum computation task.
    Computes the SHA-256 of the ERA5 sample file and updates the project state.
    """
    # Define paths based on project structure
    # Assuming standard project layout: root -> data/raw/era5_sample.h5
    # and root -> state/projects/...
    project_root = Path.cwd()
    sample_file = project_root / "data" / "raw" / "era5_sample.h5"
    state_file = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    
    # Allow overrides via environment if needed, though task specifies exact paths
    # Using the explicit paths from the task description
    if sample_file.exists():
        logger.info(f"Computing checksum for {sample_file}")
        try:
            checksum = compute_sha256(str(sample_file))
            logger.info(f"SHA-256: {checksum}")
            
            ensure_state_file_exists(str(state_file))
            update_state_file(str(state_file), str(sample_file), checksum)
            
            logger.info("Checksum computation and state update completed successfully.")
        except Exception as e:
            logger.error(f"Failed to compute or record checksum: {e}")
            sys.exit(1)
    else:
        logger.error(f"Sample file not found at {sample_file}. "
                     "Please ensure T002 (fetch_era5.py) has been run successfully.")
        sys.exit(1)

if __name__ == "__main__":
    main()
