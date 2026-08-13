"""
Input/Output utilities for the plant disease resistance prediction pipeline.
Provides checksumming, artifact logging, and detailed step logging capabilities.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the algorithm is not supported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        hash_obj = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm '{algorithm}': {e}")
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def log_artifact(
    artifact_path: Path,
    artifact_type: str,
    description: str = "",
    state_file: Optional[Path] = None
) -> None:
    """
    Log an artifact to the state file with its hash.
    
    Args:
        artifact_path: Path to the artifact
        artifact_type: Type of artifact (e.g., 'data', 'model', 'results')
        description: Optional description of the artifact
        state_file: Path to the state file (default: state/artifact_hashes.yaml)
    """
    if state_file is None:
        state_file = Path("state/artifact_hashes.yaml")
    
    # Ensure state directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Compute hash
    file_hash = compute_file_hash(artifact_path)
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    # Add artifact entry
    artifact_key = str(artifact_path.relative_to(Path.cwd()))
    state[artifact_key] = {
        "type": artifact_type,
        "hash": file_hash,
        "description": description,
        "timestamp": datetime.now().isoformat()
    }
    
    # Write updated state
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logger.info(f"Logged artifact: {artifact_key} (hash: {file_hash[:16]}...)")

def log_data_acquisition_step(
    step_name: str,
    details: Dict[str, Any],
    log_file: Optional[Path] = None
) -> None:
    """
    Log a data acquisition step with detailed metrics.
    
    Args:
        step_name: Name of the step (e.g., 'study_query', 'download_start', 'download_complete')
        details: Dictionary of step details (e.g., study_id, file_size, record_count, status)
        log_file: Path to log file (default: state/data_acquisition.log)
    """
    if log_file is None:
        log_file = Path("state/data_acquisition.log")
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step_name,
        "details": details
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    logger.info(f"Logged data acquisition step: {step_name} | Details: {json.dumps(details)}")

def log_preprocessing_step(
    step_name: str,
    details: Dict[str, Any],
    log_file: Optional[Path] = None
) -> None:
    """
    Log a preprocessing step with detailed metrics.
    
    Args:
        step_name: Name of the step (e.g., 'log_transform', 'filter_missing', 'combat_correction')
        details: Dictionary of step details (e.g., rows_processed, features_dropped, batch_info)
        log_file: Path to log file (default: state/preprocessing.log)
    """
    if log_file is None:
        log_file = Path("state/preprocessing.log")
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step_name,
        "details": details
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    logger.info(f"Logged preprocessing step: {step_name} | Details: {json.dumps(details)}")

def verify_checksum(
    file_path: Path,
    expected_hash: str,
    algorithm: str = 'sha256'
) -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file
        expected_hash: Expected hash string
        algorithm: Hash algorithm to use
        
    Returns:
        True if hashes match, False otherwise
    """
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash