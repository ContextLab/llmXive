"""
Task T002e: Compute SHA-256 checksum of data/raw/era5_full.parquet and record it
in state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml.
"""
import os
import sys
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

# Configuration
STATE_FILE_REL = "state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
DATA_FILE_REL = "data/raw/era5_full.parquet"
ARTIFACT_KEY = "era5_full"
ARTIFACT_HASH_KEY = "artifact_hashes"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_state_file_exists(state_file: Path) -> None:
    """Ensure the state YAML file exists. If not, create an empty structure."""
    if not state_file.exists():
        state_file.parent.mkdir(parents=True, exist_ok=True)
        # Create minimal valid YAML structure
        with open(state_file, "w", encoding="utf-8") as f:
            f.write("project_id: PROJ-743-ambient-temperature-influence-on-moral-d\n")
            f.write("artifact_hashes: {}\n")
            f.write("updated_at: null\n")

def update_state_file(state_file: Path, hash_value: str, artifact_key: str) -> None:
    """Update the state YAML file with the new checksum and timestamp."""
    import yaml

    # Load existing state
    with open(state_file, "r", encoding="utf-8") as f:
        state = yaml.safe_load(f) or {}

    # Ensure nested keys exist
    if ARTIFACT_HASH_KEY not in state:
        state[ARTIFACT_HASH_KEY] = {}

    # Update hash
    state[ARTIFACT_HASH_KEY][artifact_key] = hash_value

    # Update timestamp
    state["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Write back
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def main():
    """Main entry point for T002e."""
    setup_logging()
    logger = get_data_quality_logger()

    # Resolve paths relative to project root
    state_file = project_root / STATE_FILE_REL
    data_file = project_root / DATA_FILE_REL

    logger.info(f"Starting checksum computation for {DATA_FILE_REL}")

    # Verify data file exists
    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        logger.error("Task T002e FAILED: Input file missing. Dependencies (T002d) may not have completed.")
        sys.exit(1)

    # Verify file size > 0
    if data_file.stat().st_size == 0:
        logger.error(f"Data file is empty: {data_file}")
        logger.error("Task T002e FAILED: Input file is empty.")
        sys.exit(1)

    try:
        # Compute checksum
        checksum = compute_sha256(data_file)
        logger.info(f"Computed SHA-256 checksum: {checksum}")

        # Ensure state file exists
        ensure_state_file_exists(state_file)

        # Update state file
        update_state_file(state_file, checksum, ARTIFACT_KEY)
        logger.info(f"Updated state file: {state_file}")
        logger.info(f"Recorded checksum for '{ARTIFACT_KEY}' under '{ARTIFACT_HASH_KEY}'")

        logger.info("Task T002e COMPLETED successfully.")

    except Exception as e:
        logger.error(f"Task T002e FAILED with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()