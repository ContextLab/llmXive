import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from utils.constants import STATE_DIR, PROJECT_ROOT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(STATE_DIR / "pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Computes the hash of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).
    
    Returns:
        Hex digest of the file hash.
    """
    hash_obj = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise

def log_artifact(file_path: Path, artifact_type: str, hashes: Dict[str, str] = None) -> None:
    """
    Logs an artifact to state/artifact_hashes.yaml.
    
    Args:
        file_path: Path to the artifact.
        artifact_type: Type of artifact (e.g., 'data', 'model').
        hashes: Optional dict of additional hashes.
    """
    if not file_path.exists():
        logger.error(f"Artifact not found: {file_path}")
        return

    sha256_hash = compute_file_hash(file_path)
    
    artifact_record = {
        "path": str(file_path.relative_to(PROJECT_ROOT)),
        "type": artifact_type,
        "sha256": sha256_hash
    }
    if hashes:
        artifact_record.update(hashes)

    hash_file = STATE_DIR / "artifact_hashes.yaml"
    
    # Load existing records
    records = []
    if hash_file.exists():
        try:
            with open(hash_file, "r") as f:
                existing_data = yaml.safe_load(f)
                if existing_data:
                    records = existing_data if isinstance(existing_data, list) else [existing_data]
        except yaml.YAMLError:
            logger.warning("artifact_hashes.yaml is not valid YAML. Overwriting.")
            records = []

    # Append new record
    records.append(artifact_record)

    # Write back
    with open(hash_file, "w") as f:
        yaml.dump(records, f, default_flow_style=False)
    
    logger.info(f"Logged artifact: {file_path} (SHA256: {sha256_hash})")

def log_data_acquisition_step(step_name: str, details: Dict[str, Any]) -> None:
    """Logs a data acquisition step."""
    logger.info(f"Data Acquisition - {step_name}: {details}")

def log_preprocessing_step(step_name: str, details: Dict[str, Any]) -> None:
    """Logs a preprocessing step."""
    logger.info(f"Preprocessing - {step_name}: {details}")

def verify_checksum(file_path: Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verifies the checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_hash: Expected hash string.
        algorithm: Hash algorithm.
    
    Returns:
        True if hashes match, False otherwise.
    """
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash

def log_pipeline_status(status: str, message: str = "") -> None:
    """Logs the overall pipeline status."""
    if status == "ERROR":
        logger.error(f"Pipeline Status: {status} - {message}")
    elif status == "WARNING":
        logger.warning(f"Pipeline Status: {status} - {message}")
    else:
        logger.info(f"Pipeline Status: {status} - {message}")
