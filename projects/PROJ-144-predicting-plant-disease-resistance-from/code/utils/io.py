import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from utils.constants import STATE_DIR

STATE_ARTIFACTS_FILE = STATE_DIR / "artifact_hashes.yaml"

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_artifact(file_path: Path, artifact_type: str = "data") -> None:
    """Log artifact hash to state/artifact_hashes.yaml."""
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    
    file_hash = compute_file_hash(file_path)
    relative_path = str(file_path.relative_to(Path(__file__).parent.parent.parent))
    
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    artifact_entry = {
        "path": relative_path,
        "hash": file_hash,
        "type": artifact_type
    }
    
    # Load existing logs if any
    if STATE_ARTIFACTS_FILE.exists():
        with open(STATE_ARTIFACTS_FILE, 'r') as f:
            try:
                existing_logs = yaml.safe_load(f) or []
            except yaml.YAMLError:
                existing_logs = []
    else:
        existing_logs = []
    
    # Append new entry
    existing_logs.append(artifact_entry)
    
    with open(STATE_ARTIFACTS_FILE, 'w') as f:
        yaml.dump(existing_logs, f, default_flow_style=False)

def compute_checksum(data: bytes) -> str:
    """Compute SHA256 checksum of raw bytes."""
    return hashlib.sha256(data).hexdigest()

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify file hash matches expected hash."""
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash

def log_data_acquisition_step(step_name: str, details: Dict[str, Any]) -> None:
    """Log data acquisition steps."""
    logger = logging.getLogger("data_acquisition")
    logger.info(f"Step: {step_name}, Details: {details}")

def log_preprocessing_step(step_name: str, details: Dict[str, Any]) -> None:
    """Log preprocessing steps."""
    logger = logging.getLogger("preprocessing")
    logger.info(f"Step: {step_name}, Details: {details}")

def log_pipeline_status(status: str, message: str) -> None:
    """Log overall pipeline status."""
    logger = logging.getLogger("pipeline")
    logger.info(f"Status: {status}, Message: {message}")
