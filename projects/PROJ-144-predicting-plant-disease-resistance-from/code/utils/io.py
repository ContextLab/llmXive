"""
I/O utilities for checksumming and logging artifacts.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from code.utils.constants import STATE_DIR

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist.")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def log_artifact(file_path: Path, artifact_name: str) -> Dict[str, Any]:
    """Log an artifact to state/artifact_hashes.yaml."""
    state_file = STATE_DIR / "artifact_hashes.yaml"
    
    if not state_file.exists():
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w") as f:
            yaml.dump({}, f)
    
    with open(state_file, "r") as f:
        try:
            data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            data = {}
    
    file_hash = compute_file_hash(file_path)
    data[artifact_name] = {
        "path": str(file_path),
        "hash": file_hash,
        "algorithm": "sha256"
    }
    
    with open(state_file, "w") as f:
        yaml.dump(data, f, sort_keys=False)
    
    logger.info(f"Logged artifact {artifact_name} with hash {file_hash}")
    return data[artifact_name]

def log_data_acquisition_step(step_name: str, details: Optional[Dict] = None):
    """Log a data acquisition step."""
    logger.info(f"Data Acquisition: {step_name} - {details}")

def log_preprocessing_step(step_name: str, details: Optional[Dict] = None):
    """Log a preprocessing step."""
    logger.info(f"Preprocessing: {step_name} - {details}")
