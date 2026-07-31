import logging
import sys
import os
import hashlib
import yaml
import pyarrow.parquet as pq
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_project_root

logger = logging.getLogger(__name__)

def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure root logger."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

def write_parquet(df: pd.DataFrame, output_path: str) -> None:
    """
    Write a pandas DataFrame to a Parquet file.

    Args:
        df: The DataFrame to write.
        output_path: The full path to the output .parquet file.
    """
    root = get_project_root()
    full_path = root / output_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_parquet(full_path, index=False, engine='pyarrow')
        logger.info(f"Successfully wrote parquet file to {full_path}")
    except Exception as e:
        logger.error(f"Failed to write parquet file to {full_path}: {e}")
        raise

def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: The full path to the file.

    Returns:
        The hexadecimal SHA-256 hash string.
    """
    root = get_project_root()
    full_path = root / file_path

    if not full_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {full_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(full_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {full_path}: {e}")
        raise

def update_state_yaml(file_path: str, checksum: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Update the state.yaml file with a new file entry.

    Args:
        file_path: Relative path to the file being tracked.
        checksum: The SHA-256 checksum of the file.
        metadata: Optional dictionary of additional metadata (e.g., timestamp, task_id).
    """
    root = get_project_root()
    state_path = root / "state.yaml"

    # Load existing state or initialize
    if state_path.exists():
        with open(state_path, 'r') as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Could not parse state.yaml: {e}. Starting fresh.")
                state = {}
    else:
        state = {}

    # Ensure 'files' key exists
    if 'files' not in state:
        state['files'] = {}

    # Update entry
    entry = {
        'checksum': checksum,
        'path': file_path
    }
    if metadata:
        entry.update(metadata)

    state['files'][file_path] = entry

    # Write back
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated state.yaml with entry for {file_path}")