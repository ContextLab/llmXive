"""
Data loader module for managing raw data ingestion and artifact tracking.

This module handles:
- Saving downloaded or generated datasets to the `data/raw` directory.
- Calculating and storing SHA-256 checksums of these artifacts.
- Updating the project state file (`state/projects/PROJ-490-...yaml`) with artifact hashes.
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd
import yaml

# Import local utilities to ensure project structure
from utils.logger import get_logger

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE_NAME = "PROJ-490-the-effect-of-simulated-social-compariso.yaml"
STATE_FILE_PATH = STATE_DIR / STATE_FILE_NAME

logger = get_logger(__name__)


def calculate_file_hash(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path} for hashing: {e}")
        raise


def load_data_to_raw(data: pd.DataFrame, filename: str) -> Path:
    """
    Save a pandas DataFrame to the data/raw directory as a CSV.

    Args:
        data: The DataFrame to save.
        filename: The name of the file (e.g., 'dataset.csv').

    Returns:
        Path to the saved file.

    Raises:
        ValueError: If data is not a DataFrame or is empty.
    """
    if not isinstance(data, pd.DataFrame):
        raise ValueError("Input data must be a pandas DataFrame.")
    if data.empty:
        raise ValueError("Input DataFrame is empty.")

    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_RAW_DIR / filename

    logger.info(f"Saving data to {output_path}...")
    data.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(data)} rows to {output_path}")

    return output_path


def write_artifact_hashes_to_state(artifact_path: Path, artifact_type: str = "raw_data") -> None:
    """
    Calculate the hash of an artifact and write/update it in the project state YAML.

    This implements Constitution Principle III and V by ensuring artifact integrity
    and provenance tracking.

    Args:
        artifact_path: Path to the artifact file.
        artifact_type: A label for the artifact (e.g., 'raw_data', 'synthetic_data').
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    file_hash = calculate_file_hash(artifact_path)
    state_dir = STATE_FILE_PATH.parent
    state_dir.mkdir(parents=True, exist_ok=True)

    # Load existing state or initialize new
    state_data = {}
    if STATE_FILE_PATH.exists():
        try:
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                state_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Could not parse existing state file: {e}. Starting fresh.")
            state_data = {}

    # Ensure structure exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    # Update the specific artifact entry
    entry = {
        "path": str(artifact_path.relative_to(PROJECT_ROOT)),
        "hash": file_hash,
        "type": artifact_type,
        "updated_at": str(pd.Timestamp.now())
    }

    state_data["artifact_hashes"][artifact_path.name] = entry

    # Write back to state file
    try:
        with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Updated state file at {STATE_FILE_PATH} with hash for {artifact_path.name}")
    except IOError as e:
        logger.error(f"Failed to write state file: {e}")
        raise


def run_loader(
    data: pd.DataFrame,
    filename: str = "raw_dataset.csv",
    artifact_type: str = "raw_data"
) -> Dict[str, Any]:
    """
    Main entry point to load data to raw storage and update state.

    This function orchestrates:
    1. Saving the data to `data/raw`.
    2. Calculating the file hash.
    3. Updating the project state YAML.

    Args:
        data: The DataFrame to save.
        filename: The desired filename for the CSV.
        artifact_type: Label for the artifact in state tracking.

    Returns:
        A dictionary containing the output path and the calculated hash.

    Raises:
        Exception: If any step in the loading or state update process fails.
    """
    logger.info(f"Starting data loader for file: {filename}")

    # Step 1: Save to raw
    output_path = load_data_to_raw(data, filename)

    # Step 2 & 3: Calculate hash and update state
    write_artifact_hashes_to_state(output_path, artifact_type)

    result = {
        "status": "success",
        "path": str(output_path),
        "filename": filename,
        "artifact_type": artifact_type
    }
    logger.info(f"Loader completed successfully. Output: {result}")
    return result
