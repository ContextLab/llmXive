"""
I/O Helpers for the Neural Oscillations TDCS Biomarker project.

Provides utilities for:
- Loading CSV and Parquet datasets.
- Computing and verifying SHA-256 checksums.
- Writing checksums to the project state YAML file (FR-005).
"""
import csv
import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

# Import shared config to ensure path consistency
from .config import PROJECT_ROOT

# Configure logging to capture warnings and info as per FR-008
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

STATE_DIR = PROJECT_ROOT / "state" / "projects"
PROJECT_STATE_FILE = STATE_DIR / "PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml"


def load_csv(path: Union[str, Path]) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.

    Args:
        path: Path to the CSV file.

    Returns:
        DataFrame containing the CSV data.

    Raises:
        FileNotFoundError: If the file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV file not found: {p}")
    logger.info(f"Loading CSV from {p}")
    return pd.read_csv(p)


def load_parquet(path: Union[str, Path]) -> pd.DataFrame:
    """
    Load a Parquet file into a pandas DataFrame.

    Args:
        path: Path to the Parquet file.

    Returns:
        DataFrame containing the Parquet data.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Parquet file not found: {p}")
    logger.info(f"Loading Parquet from {p}")
    return pd.read_parquet(p)


def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read for large file handling.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found for hashing: {p}")

    sha256_hash = hashlib.sha256()
    logger.debug(f"Computing SHA-256 for {p}")
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def verify_checksum(
    file_path: Union[str, Path],
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify the checksum of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected hexadecimal checksum string.
        algorithm: Hash algorithm to use (currently only 'sha256' is supported).

    Returns:
        True if the checksum matches, False otherwise.

    Logs:
        WARNING if checksums do not match.
    """
    if algorithm != "sha256":
        raise ValueError(f"Unsupported algorithm: {algorithm}. Only 'sha256' is supported.")

    try:
        actual_checksum = compute_sha256(file_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return False

    if actual_checksum.lower() == expected_checksum.lower():
        logger.info(f"Checksum verified for {file_path}: {actual_checksum}")
        return True
    else:
        logger.warning(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
        return False


def write_checksum_to_state(
    file_path: Union[str, Path],
    checksum: Optional[str] = None,
    project_id: str = "PROJ-164-neural-oscillations-as-a-biomarker-for-p"
) -> None:
    """
    Verify the checksum of a file and write the successful result to the project state YAML.
    This function implements FR-005 and Constitution Principle III.

    If `checksum` is not provided, it is computed from the file.
    If verification fails, the file is NOT written to the state file, and a warning is logged.

    Args:
        file_path: Path to the file to verify and record.
        checksum: Optional pre-computed checksum. If None, computed on the fly.
        project_id: The project ID key for the state file.
    """
    p = Path(file_path)
    if not p.exists():
        logger.error(f"Cannot write checksum to state: file not found {p}")
        return

    if checksum is None:
        try:
            checksum = compute_sha256(p)
        except Exception as e:
            logger.error(f"Failed to compute checksum for {p}: {e}")
            return

    # Verify before writing to state
    if not verify_checksum(p, checksum):
        logger.warning(f"Skipping state update for {p} due to checksum verification failure.")
        return

    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    state_data: Dict[str, Any] = {}
    if PROJECT_STATE_FILE.exists():
        try:
            import yaml
            with open(PROJECT_STATE_FILE, "r") as f:
                state_data = yaml.safe_load(f) or {}
        except ImportError:
            logger.warning("PyYAML not installed. State file cannot be updated. Install with 'pip install pyyaml'.")
            return
        except Exception as e:
            logger.error(f"Error reading existing state file: {e}")
            return

    # Structure: { project_id: { "files": { "relative_path": "checksum" } } }
    if project_id not in state_data:
        state_data[project_id] = {"files": {}}

    if "files" not in state_data[project_id]:
        state_data[project_id]["files"] = {}

    # Store relative path for cleaner state file
    try:
        relative_path = p.relative_to(PROJECT_ROOT)
    except ValueError:
        # If file is outside project root, store absolute path
        relative_path = str(p)

    state_data[project_id]["files"][str(relative_path)] = checksum

    try:
        import yaml
        with open(PROJECT_STATE_FILE, "w") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Checksum for {p} written to {PROJECT_STATE_FILE}")
    except Exception as e:
        logger.error(f"Failed to write state file {PROJECT_STATE_FILE}: {e}")