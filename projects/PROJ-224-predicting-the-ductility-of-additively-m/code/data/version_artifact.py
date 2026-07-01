"""
Task T020: Version the data/curated_builds.csv artifact.

This module computes the SHA-256 hash of the curated dataset and records
it in the project state file at state/projects/PROJ-224-predicting-the-ductility-of-additively-m.yaml.
"""

import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "curated_builds.csv"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-224-predicting-the-ductility-of-additively-m.yaml"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
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
        logger.error(f"Error computing hash for {file_path}: {e}")
        raise

def ensure_state_file(state_file: Path) -> dict:
    """Ensure the state YAML file exists and return its contents."""
    if not state_file.parent.exists():
        logger.info(f"Creating state directory: {state_file.parent}")
        state_file.parent.mkdir(parents=True, exist_ok=True)

    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f) or {}
                return data
            except yaml.YAMLError as e:
                logger.warning(f"Error parsing existing state file: {e}. Starting fresh.")
                return {}
    else:
        logger.info(f"State file not found. Creating new: {state_file}")
        return {}

def save_state(state_file: Path, data: dict) -> None:
    """Save the state dictionary to the YAML file."""
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    logger.info(f"State saved to {state_file}")

def version_artifact(csv_path: Path, state_file: Path) -> str:
    """
    Compute SHA-256 hash of the CSV and record it in the state file.

    Returns:
        str: The computed hash.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Curated dataset not found at {csv_path}. "
            "Please ensure T015-T019 have been executed successfully."
        )

    logger.info(f"Computing hash for {csv_path}")
    file_hash = compute_sha256(csv_path)
    logger.info(f"SHA-256 hash: {file_hash}")

    state_data = ensure_state_file(state_file)

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"]["curated_builds_csv"] = file_hash

    save_state(state_file, state_data)
    logger.info(f"Hash recorded in {state_file}")

    return file_hash

def main():
    """Entry point for the versioning script."""
    logger.info("Starting T020: Artifact Versioning")
    try:
        file_hash = version_artifact(CSV_PATH, STATE_FILE)
        logger.info(f"Task T020 completed successfully. Hash: {file_hash}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Task T020 failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T020: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())