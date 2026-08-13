"""
I/O utilities for checksumming and logging artifacts.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Computes the hash of a file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def log_artifact(path: str, artifact_type: str, description: str = "") -> None:
    """
    Logs an artifact to state/artifact_hashes.yaml.
    """
    state_dir = Path("state")
    state_dir.mkdir(parents=True, exist_ok=True)
    log_file = state_dir / "artifact_hashes.yaml"

    data = {}
    if log_file.exists():
        with open(log_file, 'r') as f:
            data = yaml.safe_load(f) or {}

    file_hash = compute_file_hash(path)
    
    entry = {
        "path": str(path),
        "type": artifact_type,
        "description": description,
        "sha256": file_hash
    }

    # Append to list or update dict
    if "artifacts" not in data:
        data["artifacts"] = []
    
    # Check if path already exists to avoid duplicates
    existing = [a for a in data["artifacts"] if a.get("path") == str(path)]
    if existing:
        existing[0] = entry
    else:
        data["artifacts"].append(entry)

    with open(log_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

    logger.info(f"Logged artifact: {path} ({file_hash})")

def compute_checksum(file_path: str) -> str:
    """
    Wrapper for compute_file_hash.
    """
    return compute_file_hash(file_path)

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verifies a file's checksum against an expected value.
    """
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash

def log_data_acquisition_step(step_name: str, details: Dict[str, Any]) -> None:
    """
    Logs a step in the data acquisition pipeline.
    """
    logger.info(f"Data Acquisition Step: {step_name} - {details}")

def log_preprocessing_step(step_name: str, details: Dict[str, Any]) -> None:
    """
    Logs a step in the preprocessing pipeline.
    """
    logger.info(f"Preprocessing Step: {step_name} - {details}")

def log_pipeline_status(status: str, message: str) -> None:
    """
    Logs a general pipeline status update.
    """
    logger.info(f"Pipeline Status: {status} - {message}")
