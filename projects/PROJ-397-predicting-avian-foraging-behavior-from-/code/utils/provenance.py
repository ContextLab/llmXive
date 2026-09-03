"""
Provenance module for llmXive automated science pipeline.

This module implements Constitution Principle VI (Habitat Data Provenance) by:
1. Generating SHA-256 hashes for all data artifacts
2. Recording source URLs, versions, and extraction dates for external datasets
3. Managing a centralized metadata.yaml file for reproducibility
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
import yaml

from utils.config import get_project_root, get_data_dir, get_metadata_file


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal SHA-256 hash string
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")


def compute_data_hash(data: Any) -> str:
    """
    Compute SHA-256 hash of arbitrary data (serializable objects).
    
    Args:
        data: Any JSON-serializable data structure
        
    Returns:
        Hexadecimal SHA-256 hash string
    """
    serialized = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()


def generate_provenance_record(
    artifact_path: Union[str, Path],
    source_url: Optional[str] = None,
    version: Optional[str] = None,
    extraction_date: Optional[datetime] = None,
    artifact_type: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a provenance record for a data artifact.
    
    Args:
        artifact_path: Path to the artifact
        source_url: URL where the data was sourced from (for external datasets)
        version: Version identifier of the source data
        extraction_date: Date/time when data was extracted (defaults to now)
        artifact_type: Type of artifact (e.g., 'raw_data', 'processed_data', 'model')
        description: Human-readable description of the artifact
        
    Returns:
        Dictionary containing the provenance record
    """
    artifact_path = Path(artifact_path)
    
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
        
    file_hash = compute_file_hash(artifact_path)
    file_size = artifact_path.stat().st_size
    
    record = {
        "artifact_path": str(artifact_path),
        "file_hash": file_hash,
        "file_size_bytes": file_size,
        "created_at": datetime.now().isoformat(),
        "source_url": source_url,
        "version": version,
        "extraction_date": extraction_date.isoformat() if extraction_date else None,
        "artifact_type": artifact_type,
        "description": description
    }
    
    return record


def save_provenance_record(
    record: Dict[str, Any],
    metadata_file: Optional[Path] = None
) -> Path:
    """
    Save a provenance record to the centralized metadata.yaml file.
    
    Args:
        record: The provenance record dictionary to save
        metadata_file: Optional path to metadata file (defaults to project metadata)
        
    Returns:
        Path to the updated metadata file
    """
    if metadata_file is None:
        metadata_file = get_metadata_file()
        
    metadata_file = Path(metadata_file)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing metadata or create new structure
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = yaml.safe_load(f) or {}
    else:
        metadata = {
            "pipeline_version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "artifacts": [],
            "external_sources": []
        }
    
    # Categorize record
    if record.get("source_url"):
        # External dataset record
        source_entry = {
            "name": record.get("artifact_path", "unknown"),
            "source_url": record.get("source_url"),
            "version": record.get("version"),
            "extraction_date": record.get("extraction_date"),
            "file_hash": record.get("file_hash"),
            "retrieved_at": datetime.now().isoformat()
        }
        
        # Check if this source is already recorded
        existing_sources = metadata.get("external_sources", [])
        existing_names = [s.get("name") for s in existing_sources]
        
        if record.get("artifact_path") not in existing_names:
            metadata.setdefault("external_sources", []).append(source_entry)
    else:
        # Internal artifact record
        artifact_entry = {
            "path": record.get("artifact_path"),
            "file_hash": record.get("file_hash"),
            "file_size_bytes": record.get("file_size_bytes"),
            "created_at": record.get("created_at"),
            "artifact_type": record.get("artifact_type"),
            "description": record.get("description")
        }
        metadata.setdefault("artifacts", []).append(artifact_entry)
    
    # Write updated metadata
    with open(metadata_file, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        
    return metadata_file


def log_step(
    step_name: str,
    status: str,
    message: Optional[str] = None,
    metadata_file: Optional[Path] = None
) -> Path:
    """
    Log a pipeline step execution to metadata.
    
    Args:
        step_name: Name of the pipeline step
        status: Status of the step (e.g., 'started', 'completed', 'failed')
        message: Optional message describing the step outcome
        metadata_file: Optional path to metadata file
        
    Returns:
        Path to the updated metadata file
    """
    if metadata_file is None:
        metadata_file = get_metadata_file()
        
    metadata_file = Path(metadata_file)
    
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = yaml.safe_load(f) or {}
    else:
        metadata = {"pipeline_execution_log": []}
    
    log_entry = {
        "step_name": step_name,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "message": message
    }
    
    metadata.setdefault("pipeline_execution_log", []).append(log_entry)
    
    with open(metadata_file, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        
    return metadata_file


def verify_data_integrity(
    artifact_path: Union[str, Path],
    expected_hash: str,
    metadata_file: Optional[Path] = None
) -> bool:
    """
    Verify the integrity of an artifact by comparing its hash to an expected value.
    
    Args:
        artifact_path: Path to the artifact to verify
        expected_hash: Expected SHA-256 hash
        metadata_file: Optional path to metadata file for logging
        
    Returns:
        True if hash matches, False otherwise
        
    Raises:
        FileNotFoundError: If the artifact does not exist
    """
    actual_hash = compute_file_hash(artifact_path)
    is_valid = actual_hash == expected_hash
    
    if metadata_file:
        status = "verified" if is_valid else "mismatch"
        message = f"Hash verification {'passed' if is_valid else 'failed'} for {artifact_path}"
        log_step(f"verify_{Path(artifact_path).name}", status, message, metadata_file)
        
    return is_valid


def load_provenance_records(
    metadata_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load all provenance records from the metadata file.
    
    Args:
        metadata_file: Optional path to metadata file
        
    Returns:
        Dictionary containing all provenance records
    """
    if metadata_file is None:
        metadata_file = get_metadata_file()
        
    metadata_file = Path(metadata_file)
    
    if not metadata_file.exists():
        return {
            "artifacts": [],
            "external_sources": [],
            "pipeline_execution_log": []
        }
        
    with open(metadata_file, 'r') as f:
        return yaml.safe_load(f) or {}


def record_artifact_provenance(
    artifact_path: Union[str, Path],
    source_url: Optional[str] = None,
    version: Optional[str] = None,
    artifact_type: Optional[str] = None,
    description: Optional[str] = None,
    metadata_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate and save a provenance record in one step.
    
    Args:
        artifact_path: Path to the artifact
        source_url: Source URL (for external datasets)
        version: Version identifier
        artifact_type: Type of artifact
        description: Description of the artifact
        metadata_file: Path to metadata file
        
    Returns:
        The generated provenance record
    """
    record = generate_provenance_record(
        artifact_path=artifact_path,
        source_url=source_url,
        version=version,
        artifact_type=artifact_type,
        description=description
    )
    
    save_provenance_record(record, metadata_file)
    return record
