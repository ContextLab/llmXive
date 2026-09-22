import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
import yaml

# Import config to get paths
from utils.config import get_metadata_file, get_project_root

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_data_hash(data: Any) -> str:
    """Compute SHA-256 hash of a data object (dict, list, etc)."""
    json_str = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(json_str).hexdigest()

def generate_provenance_record(
    artifact_name: str,
    source_url: Optional[str] = None,
    version: Optional[str] = None,
    extraction_date: Optional[str] = None,
    checksum: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate a provenance record dictionary."""
    return {
        "artifact_name": artifact_name,
        "source_url": source_url,
        "version": version,
        "extraction_date": extraction_date or datetime.now().isoformat(),
        "checksum": checksum,
        "metadata": metadata or {},
        "generated_at": datetime.now().isoformat()
    }

def load_metadata_config() -> Dict[str, Any]:
    """Load the metadata.yaml file."""
    metadata_file = get_metadata_file()
    if not metadata_file.exists():
        return {"datasets": {}, "artifacts": {}, "pipeline_runs": []}
    
    with open(metadata_file, 'r') as f:
        return yaml.safe_load(f) or {"datasets": {}, "artifacts": {}, "pipeline_runs": []}

def save_metadata_config(metadata: Dict[str, Any]) -> None:
    """Save the metadata dictionary to metadata.yaml."""
    metadata_file = get_metadata_file()
    with open(metadata_file, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)

def save_provenance_record(record: Dict[str, Any]) -> None:
    """Append a provenance record to the metadata file."""
    metadata = load_metadata_config()
    if "artifacts" not in metadata:
        metadata["artifacts"] = {}
    
    artifact_name = record.get("artifact_name", "unknown")
    metadata["artifacts"][artifact_name] = record
    
    save_metadata_config(metadata)

def record_source_info(
    dataset_name: str,
    source_url: str,
    version: str,
    checksum: str,
    local_path: str
) -> None:
    """Record source information for a dataset in metadata.yaml."""
    metadata = load_metadata_config()
    if "datasets" not in metadata:
        metadata["datasets"] = {}
    
    metadata["datasets"][dataset_name] = {
        "source_url": source_url,
        "version": version,
        "download_date": datetime.now().isoformat(),
        "checksum": checksum,
        "local_path": local_path
    }
    
    save_metadata_config(metadata)

def log_step(step_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log a pipeline step execution."""
    metadata = load_metadata_config()
    if "pipeline_runs" not in metadata:
        metadata["pipeline_runs"] = []
    
    run_record = {
        "step_name": step_name,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    
    metadata["pipeline_runs"].append(run_record)
    save_metadata_config(metadata)

def verify_data_integrity(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """Verify the checksum of a file against an expected value."""
    actual_checksum = compute_file_hash(file_path)
    return actual_checksum == expected_checksum

def load_provenance_records() -> Dict[str, Any]:
    """Load all provenance records from metadata.yaml."""
    metadata = load_metadata_config()
    return metadata.get("artifacts", {})

def record_artifact_provenance(
    artifact_name: str,
    file_path: Union[str, Path],
    source_url: Optional[str] = None,
    version: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Record provenance for an artifact file."""
    file_path = Path(file_path)
    checksum = compute_file_hash(file_path)
    
    record = generate_provenance_record(
        artifact_name=artifact_name,
        source_url=source_url,
        version=version,
        checksum=checksum,
        metadata=metadata
    )
    
    save_provenance_record(record)

def main():
    """Example usage for testing provenance functions."""
    print("Provenance module loaded successfully.")
    # Example: record a dummy dataset
    # record_source_info("test_dataset", "http://example.com", "1.0", "abc123", "data/raw/test.csv")

if __name__ == "__main__":
    main()