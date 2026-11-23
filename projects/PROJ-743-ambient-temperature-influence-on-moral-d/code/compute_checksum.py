import hashlib
import os
import sys
import logging
import yaml
from datetime import datetime, timezone
from pathlib import Path

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_state_file_exists(state_file_path: Path) -> None:
    """Ensure the state YAML file exists, creating an empty structure if not."""
    if not state_file_path.exists():
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file_path, "w") as f:
            yaml.dump({"artifact_hashes": {}, "updated_at": None}, f)
        logging.getLogger(__name__).info(f"Created new state file: {state_file_path}")

def update_state_file(state_file_path: Path, key: str, value: str, logger: logging.Logger) -> None:
    """
    Update a nested key in the state YAML file.
    
    Args:
        state_file_path: Path to the YAML file.
        key: Dot-separated path (e.g., 'artifact_hashes.era5_sample').
        value: The value to set.
        logger: Logger instance for status updates.
    """
    # Load existing data
    with open(state_file_path, "r") as f:
        data = yaml.safe_load(f) or {}
    
    # Navigate and update the nested key
    keys = key.split(".")
    current = data
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
    
    # Update timestamp
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Write back
    with open(state_file_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file: {key} = {value}")

def main():
    """Entry point for checksum computation (generic)."""
    logger = logging.getLogger(__name__)
    if len(sys.argv) < 3:
        logger.error("Usage: python compute_checksum.py <file_path> <state_key>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    state_key = sys.argv[2]
    state_file = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    checksum = compute_sha256(file_path)
    ensure_state_file_exists(state_file)
    update_state_file(state_file, state_key, checksum, logger)
    print(f"Checksum: {checksum}")

if __name__ == "__main__":
    main()
