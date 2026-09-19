import hashlib
import os
import sys
import logging
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Ensure project root imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup_logging import setup_logging, get_data_quality_logger

def ensure_state_file_exists(state_path: Path) -> bool:
    """
    Ensures the state YAML file exists. If not, creates it with an empty structure.
    """
    if not state_path.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w') as f:
            yaml.dump({"artifact_hashes": {}, "updated_at": None}, f)
        return True
    return False

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(state_path: Path, key: str, checksum: str) -> None:
    """
    Updates the state YAML file with the new checksum and timestamp.
    """
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)

    if state is None:
        state = {"artifact_hashes": {}, "updated_at": None}

    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}

    # Update the specific key
    state["artifact_hashes"][key] = checksum
    
    # Update timestamp
    state["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Main entry point for checksum computation.
    Expects arguments: --input <path>, --state-file <path>, --key <yaml_key>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Compute SHA-256 and update state file")
    parser.add_argument('--input', required=True, help='Path to the input file')
    parser.add_argument('--state-file', required=True, help='Path to the state YAML file')
    parser.add_argument('--key', required=True, help='Key in the state file to update')
    
    args = parser.parse_args()

    setup_logging()
    logger = get_data_quality_logger()

    input_path = Path(args.input)
    state_path = Path(args.state_file)
    key = args.key

    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_path}")
        sys.exit(1)

    ensure_state_file_exists(state_path)

    logger.info(f"Computing checksum for: {input_path}")
    checksum = compute_sha256(input_path)
    logger.info(f"Checksum computed: {checksum}")

    logger.info(f"Updating state file: {state_path} with key: {key}")
    update_state_file(state_path, key, checksum)

    logger.info("State file updated successfully.")

if __name__ == '__main__':
    main()