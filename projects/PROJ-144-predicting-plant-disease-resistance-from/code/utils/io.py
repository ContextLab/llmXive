import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from code.utils.constants import STATE_DIR

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file using the specified algorithm (MD5 or SHA256)."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def log_artifact(artifact_path: Path, artifact_type: str, description: str = "") -> None:
    """Log an artifact's hash and metadata to state/artifact_hashes.yaml.
    
    Supports MD5 and SHA256 checksumming. Defaults to SHA256.
    Appends to the YAML file if it exists, avoiding duplicate entries for the same path.
    """
    state_file = STATE_DIR / "artifact_hashes.yaml"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    if not artifact_path.exists():
        logger.warning(f"Artifact not found, cannot log: {artifact_path}")
        return

    # Compute SHA256 hash
    file_hash = compute_file_hash(artifact_path, algorithm="sha256")

    artifact_record = {
        "path": str(artifact_path.relative_to(Path("."))),
        "type": artifact_type,
        "hash": file_hash,
        "description": description
    }

    # Load existing records or create new list
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            try:
                records = yaml.safe_load(f) or []
            except yaml.YAMLError:
                records = []
    else:
        records = []

    # Append new record (check for duplicates by path)
    if not any(r["path"] == artifact_record["path"] for r in records):
        records.append(artifact_record)
        with open(state_file, "w", encoding="utf-8") as f:
            yaml.dump(records, f, default_flow_style=False, allow_unicode=True)
        logger.info(f"Logged artifact: {artifact_path} ({artifact_type}) -> {file_hash}")
    else:
        logger.info(f"Artifact already logged, skipping duplicate: {artifact_path}")

def log_data_acquisition_step(step_name: str, details: Dict[str, Any]) -> None:
    """Log a data acquisition step to state/data_log.yaml.
    
    Records the step name and a dictionary of details (e.g., study IDs, file counts, 
    download status, error messages) to a persistent YAML log file.
    """
    log_file = STATE_DIR / "data_log.yaml"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "step": step_name,
        "details": details
    }

    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            try:
                logs = yaml.safe_load(f) or []
            except yaml.YAMLError:
                logs = []
    else:
        logs = []

    logs.append(entry)
    with open(log_file, "w", encoding="utf-8") as f:
        yaml.dump(logs, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Logged data acquisition step: {step_name}")

def log_preprocessing_step(step_name: str, details: Dict[str, Any]) -> None:
    """Log a preprocessing step to state/preprocessing_log.yaml.
    
    Records the step name and a dictionary of details (e.g., number of features removed,
    transformation types applied, batch correction parameters) to a persistent YAML log file.
    """
    log_file = STATE_DIR / "preprocessing_log.yaml"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "step": step_name,
        "details": details
    }

    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            try:
                logs = yaml.safe_load(f) or []
            except yaml.YAMLError:
                logs = []
    else:
        logs = []

    logs.append(entry)
    with open(log_file, "w", encoding="utf-8") as f:
        yaml.dump(logs, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Logged preprocessing step: {step_name}")
