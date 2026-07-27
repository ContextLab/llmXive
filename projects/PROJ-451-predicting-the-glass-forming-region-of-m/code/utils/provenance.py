"""
Utilities for managing and updating the data provenance record.
Handles checksum computation and schema validation.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from config import get_data_path


def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_provenance() -> Dict[str, Any]:
    """
    Load the current provenance.json file.
    If it doesn't exist, return a minimal valid structure.
    
    Returns:
        Dictionary containing the provenance data.
    """
    provenance_path = get_data_path() / "provenance.json"
    if not provenance_path.exists():
        return {
            "sources": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "processing_history": []
        }
    
    with open(provenance_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_provenance(data: Dict[str, Any]) -> None:
    """
    Save the provenance data to disk.
    
    Args:
        data: The provenance dictionary to save.
    """
    provenance_path = get_data_path() / "provenance.json"
    # Ensure directory exists
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(provenance_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def register_source(
    source_id: str,
    source_type: str,
    url: str,
    description: str,
    status: str = "pending_download"
) -> None:
    """
    Register a new source in the provenance record.
    If the source_id already exists, it updates the entry.
    
    Args:
        source_id: Unique identifier for the source.
        source_type: Type of source (dataset, api, file, synthetic).
        url: URL or DOI of the source.
        description: Human-readable description.
        status: Initial status.
    """
    data = load_provenance()
    
    # Check if source exists
    source_exists = False
    for source in data["sources"]:
        if source["id"] == source_id:
            source["url"] = url
            source["description"] = description
            source["type"] = source_type
            source["status"] = status
            source_exists = True
            break
    
    if not source_exists:
        new_source = {
            "id": source_id,
            "type": source_type,
            "url": url,
            "description": description,
            "checksum": None,
            "checksum_algorithm": None,
            "status": status,
            "downloaded_at": None,
            "size_bytes": None
        }
        data["sources"].append(new_source)
    
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_provenance(data)


def update_source_checksum(source_id: str, file_path: str) -> None:
    """
    Compute and update the checksum for a specific source.
    
    Args:
        source_id: The ID of the source to update.
        file_path: Path to the downloaded file.
        
    Raises:
        ValueError: If the source_id is not found.
        FileNotFoundError: If the file_path does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    checksum = compute_sha256(file_path)
    file_size = os.path.getsize(file_path)
    
    data = load_provenance()
    found = False
    
    for source in data["sources"]:
        if source["id"] == source_id:
            source["checksum"] = checksum
            source["checksum_algorithm"] = "sha256"
            source["status"] = "downloaded"
            source["downloaded_at"] = datetime.now(timezone.utc).isoformat()
            source["size_bytes"] = file_size
            found = True
            break
    
    if not found:
        raise ValueError(f"Source ID '{source_id}' not found in provenance record.")
    
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_provenance(data)


def add_processing_step(
    step_id: str,
    action: str,
    parameters: Optional[Dict[str, Any]] = None,
    output_checksum: Optional[str] = None
) -> None:
    """
    Add a new step to the processing history.
    
    Args:
        step_id: Unique ID for this step.
        action: Description of the action.
        parameters: Parameters used.
        output_checksum: Checksum of the output.
    """
    data = load_provenance()
    
    if "processing_history" not in data:
        data["processing_history"] = []
        
    new_step = {
        "step_id": step_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "parameters": parameters or {},
        "output_checksum": output_checksum
    }
    
    data["processing_history"].append(new_step)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_provenance(data)
