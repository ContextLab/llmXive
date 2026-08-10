import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("io_utils")

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def log_artifact(file_path: str, artifact_type: str, metadata: Optional[Dict[str, Any]] = None):
    """Log an artifact to the state/artifact_hashes.yaml file."""
    state_dir = Path("state")
    state_dir.mkdir(parents=True, exist_ok=True)
    log_file = state_dir / "artifact_hashes.yaml"
    
    data = {}
    if log_file.exists():
        with open(log_file, 'r') as f:
            try:
                data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                data = {}
    
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.warning(f"Artifact not found, skipping log: {file_path}")
        return

    file_hash = compute_file_hash(file_path_obj)
    timestamp = os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip()
    
    entry = {
        "path": str(file_path_obj.relative_to(Path("."))),
        "type": artifact_type,
        "hash": file_hash,
        "timestamp": timestamp,
        "metadata": metadata or {}
    }
    
    # Append to list or create new entry
    if "artifacts" not in data:
        data["artifacts"] = []
    
    # Check if already exists and update, or append
    found = False
    for item in data["artifacts"]:
        if item.get("path") == entry["path"]:
            item.update(entry)
            found = True
            break
    
    if not found:
        data["artifacts"].append(entry)
    
    with open(log_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    
    logger.info(f"Logged artifact: {file_path} (Hash: {file_hash[:16]}...)")

def log_data_acquisition_step(step_name: str, details: Dict[str, Any]):
    """Log a data acquisition step."""
    logger.info(f"Data Acquisition: {step_name} - {details}")

def log_preprocessing_step(step_name: str, details: Dict[str, Any]):
    """Log a preprocessing step."""
    logger.info(f"Preprocessing: {step_name} - {details}")
