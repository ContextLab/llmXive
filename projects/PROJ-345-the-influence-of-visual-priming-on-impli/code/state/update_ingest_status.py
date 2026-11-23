"""
State management module for updating ingest status and verifying checksums.
Handles checksum verification for downloaded raw data and logging of linked metadata percentage.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from code.config import Config
from code.state_management import get_project_state_dir, load_state_file, save_state_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hex digest of the file checksum
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def load_state_yaml(state_path: Path) -> Dict[str, Any]:
    """
    Load the state YAML file.

    Args:
        state_path: Path to the state.yaml file

    Returns:
        Dictionary containing the state data
    """
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Initializing empty state.")
        return {
            "project_id": Config.PROJECT_ID,
            "created_at": None,
            "artifact_hashes": {},
            "ingest_metrics": {}
        }

    with open(state_path, 'r') as f:
        return yaml.safe_load(f)


def save_state_yaml(state_path: Path, state_data: Dict[str, Any]) -> None:
    """
    Save the state to a YAML file.

    Args:
        state_path: Path to the state.yaml file
        state_data: Dictionary containing the state data
    """
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)


def verify_raw_data_checksums() -> Dict[str, str]:
    """
    Verify checksums for all downloaded raw data files and record them in state.yaml.

    Returns:
        Dictionary mapping file paths to their checksums
    """
    state_path = get_project_state_dir() / "state.yaml"
    state_data = load_state_yaml(state_path)
    checksums = {}

    raw_data_dir = Config.DATA_RAW

    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory not found at {raw_data_dir}")
        return checksums

    # Find all data files in the raw directory
    for file_path in raw_data_dir.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith('.'):
            try:
                checksum = calculate_file_checksum(file_path)
                relative_path = str(file_path.relative_to(Config.PROJECT_ROOT))
                checksums[relative_path] = checksum
                logger.info(f"Verified checksum for {relative_path}: {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to calculate checksum for {file_path}: {e}")

    # Update state with checksums
    state_data["artifact_hashes"] = state_data.get("artifact_hashes", {})
    state_data["artifact_hashes"].update(checksums)
    save_state_yaml(state_path, state_data)

    return checksums


def update_linked_metadata_percentage() -> float:
    """
    Calculate the linked metadata percentage from the processed data and log it.

    Returns:
        The linked metadata percentage
    """
    metrics_path = Config.DATA_PROCESSED / "ingest_metrics.json"
    state_path = get_project_state_dir() / "state.yaml"

    if not metrics_path.exists():
        logger.warning(f"Metrics file not found at {metrics_path}. Cannot calculate percentage.")
        return 0.0

    with open(metrics_path, 'r') as f:
        metrics = json.load(f)

    linked_metadata_percentage = metrics.get("linked_metadata_percentage", 0.0)

    # Update state with the metric
    state_data = load_state_yaml(state_path)
    state_data["ingest_metrics"] = state_data.get("ingest_metrics", {})
    state_data["ingest_metrics"]["linked_metadata_percentage"] = linked_metadata_percentage
    save_state_yaml(state_path, state_data)

    # Log the SC-001 Check message
    logger.info(f"SC-001 Check: Linked Metadata = {linked_metadata_percentage:.2f}% (Target: [deferred])")

    return linked_metadata_percentage


def main():
    """
    Main entry point for verifying checksums and updating ingest status.
    """
    logger.info("Starting checksum verification and metadata percentage update...")

    # Verify raw data checksums
    checksums = verify_raw_data_checksums()
    logger.info(f"Verified {len(checksums)} raw data files.")

    # Update and log linked metadata percentage
    percentage = update_linked_metadata_percentage()
    logger.info(f"Linked metadata percentage: {percentage:.2f}%")

    logger.info("Checksum verification and metadata update complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())