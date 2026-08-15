import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Computes the hash of a file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def compute_data_hash(data: Any) -> str:
    """
    Computes a hash of a Python object (e.g., dict, list).
    """
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

def generate_provenance_record(
    artifact_name: str,
    file_path: Optional[Path] = None,
    source_url: Optional[str] = None,
    version: Optional[str] = None,
    extraction_date: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates a provenance record for an artifact.
    """
    record = {
        "artifact_name": artifact_name,
        "timestamp": datetime.utcnow().isoformat(),
        "source_url": source_url,
        "version": version,
        "extraction_date": extraction_date or datetime.utcnow().isoformat(),
        "metadata": metadata or {}
    }

    if file_path and Path(file_path).exists():
        record["file_hash"] = compute_file_hash(file_path)
        record["file_size"] = Path(file_path).stat().st_size

    return record

def save_provenance_record(record: Dict[str, Any], output_path: Path) -> None:
    """
    Saves a provenance record to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(record, f, indent=2)

def log_step(step_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs a pipeline step execution.
    """
    log_entry = {
        "step": step_name,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    # In a real implementation, this might append to a log file or database
    print(f"[PROVENANCE] {json.dumps(log_entry)}")

def verify_data_integrity(file_path: Path, expected_hash: str) -> bool:
    """
    Verifies the integrity of a file against an expected hash.
    """
    if not file_path.exists():
        return False
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash

def load_provenance_records(record_path: Path) -> List[Dict[str, Any]]:
    """
    Loads provenance records from a JSON file.
    """
    if not record_path.exists():
        return []
    with open(record_path, "r") as f:
        return json.load(f)

def record_artifact_provenance(
    artifact_name: str,
    file_path: Path,
    metadata_file: Path
) -> None:
    """
    Records provenance for an artifact directly into the main metadata.yaml.
    This is a simplified version for the task context.
    """
    import yaml
    
    record = generate_provenance_record(
        artifact_name=artifact_name,
        file_path=file_path
    )
    
    # Load existing metadata
    existing = {}
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            existing = yaml.safe_load(f) or {}
    
    existing[artifact_name] = record
    
    with open(metadata_file, 'w') as f:
        yaml.dump(existing, f, default_flow_style=False)