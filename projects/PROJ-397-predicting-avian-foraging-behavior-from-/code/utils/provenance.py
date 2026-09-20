import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
import yaml
import logging

from utils.config import get_data_dir, get_metadata_file

logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """Compute hash of a file."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def compute_data_hash(data: Any) -> str:
    """Compute hash of serializable data."""
    serialized = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()

def generate_provenance_record(
    step_name: str,
    input_files: Optional[List[Path]] = None,
    output_files: Optional[List[Path]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate a provenance record for a pipeline step."""
    record = {
        "step_name": step_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "inputs": [],
        "outputs": [],
        "parameters": parameters or {},
        "metadata": metadata or {}
    }

    if input_files:
        for f in input_files:
          record["inputs"].append({
              "path": str(f),
              "hash": compute_file_hash(f)
          })

    if output_files:
        for f in output_files:
          record["outputs"].append({
              "path": str(f),
              "hash": compute_file_hash(f)
          })

    return record

def load_metadata_config() -> Dict[str, Any]:
    """Load the metadata.yaml configuration file."""
    metadata_path = get_metadata_file()
    if not metadata_path.exists():
        return {"datasets": {}, "artifacts": {}, "pipeline_runs": []}
    
    with open(metadata_path, 'r') as f:
        return yaml.safe_load(f) or {"datasets": {}, "artifacts": {}, "pipeline_runs": []}

def save_metadata_config(metadata: Dict[str, Any]) -> None:
    """Save the metadata.yaml configuration file."""
    metadata_path = get_metadata_file()
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

def save_provenance_record(record: Dict[str, Any]) -> None:
    """Append a provenance record to the pipeline_runs in metadata."""
    metadata = load_metadata_config()
    if "pipeline_runs" not in metadata:
        metadata["pipeline_runs"] = []
    
    metadata["pipeline_runs"].append(record)
    save_metadata_config(metadata)

def record_source_info(
    dataset_name: str,
    source_url: str,
    version: str,
    local_path: Path,
    download_date: Optional[str] = None
) -> None:
    """Record source information for a dataset in metadata."""
    metadata = load_metadata_config()
    if "datasets" not in metadata:
        metadata["datasets"] = {}

    if download_date is None:
        download_date = datetime.utcnow().isoformat() + "Z"

    checksum = compute_file_hash(local_path)

    metadata["datasets"][dataset_name] = {
        "source_url": source_url,
        "version": version,
        "download_date": download_date,
        "checksum": checksum,
        "local_path": str(local_path)
    }

    save_metadata_config(metadata)

def log_step(step_name: str, status: str, message: str) -> None:
    """Log a pipeline step execution."""
    logger.info(f"[{step_name}] {status}: {message}")

def verify_data_integrity(file_path: Path, expected_hash: str) -> bool:
    """Verify the integrity of a file against an expected hash."""
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash

def load_provenance_records() -> List[Dict[str, Any]]:
    """Load all pipeline run records from metadata."""
    metadata = load_metadata_config()
    return metadata.get("pipeline_runs", [])

def record_artifact_provenance(
    artifact_name: str,
    file_path: Path,
    description: str,
    step_name: str
) -> None:
    """Record provenance for a specific artifact."""
    metadata = load_metadata_config()
    if "artifacts" not in metadata:
        metadata["artifacts"] = {}

    metadata["artifacts"][artifact_name] = {
        "file_path": str(file_path),
        "hash": compute_file_hash(file_path),
        "description": description,
        "generated_by": step_name,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    save_metadata_config(metadata)

def main():
    """Main entry point for provenance utilities (for testing)."""
    logger.info("Provenance utilities loaded successfully.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())