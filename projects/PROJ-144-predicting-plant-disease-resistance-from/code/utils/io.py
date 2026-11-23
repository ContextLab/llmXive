"""
I/O utilities for the research pipeline.
Handles file hashing, artifact logging, and logging.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

def ensure_dirs():
    """Ensure all required directories exist."""
    for d in [STATE_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_checksum(data: bytes) -> str:
    """Compute SHA256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify file hash matches expected."""
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash

def log_artifact(file_path: str, file_hash: str):
    """Log an artifact to the state/artifact_hashes.yaml file."""
    ensure_dirs()
    manifest_path = STATE_DIR / "artifact_hashes.yaml"
    
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            try:
                manifest = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                manifest = {}
    else:
        manifest = {}
    
    if 'artifacts' not in manifest:
        manifest['artifacts'] = {}
    
    manifest['artifacts'][file_path] = {
        'sha256': file_hash
    }
    
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    
    logger.info(f"Logged artifact: {file_path}")

def log_data_acquisition_step(step_name: str, details: Dict[str, Any]):
    """Log a data acquisition step."""
    ensure_dirs()
    log_path = STATE_DIR / "data_acquisition_log.json"
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = []
    else:
        log_data = []
    
    entry = {
        'step': step_name,
        'details': details,
        'status': 'completed'
    }
    log_data.append(entry)
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Logged acquisition step: {step_name}")

def log_preprocessing_step(step_name: str, details: Dict[str, Any]):
    """Log a preprocessing step."""
    ensure_dirs()
    log_path = STATE_DIR / "preprocessing_log.json"
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = []
    else:
        log_data = []
    
    entry = {
        'step': step_name,
        'details': details,
        'status': 'completed'
    }
    log_data.append(entry)
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Logged preprocessing step: {step_name}")

def log_pipeline_status(status: str, message: str):
    """Log overall pipeline status."""
    ensure_dirs()
    log_path = STATE_DIR / "pipeline_status.json"
    
    entry = {
        'status': status,
        'message': message
    }
    
    with open(log_path, 'w') as f:
        json.dump(entry, f, indent=2)
    
    logger.info(f"Pipeline status: {status} - {message}")
