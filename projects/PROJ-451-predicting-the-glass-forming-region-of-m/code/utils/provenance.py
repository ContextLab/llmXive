"""
Provenance tracking utilities for the llmXive pipeline.
Handles schema validation, checksum computation, and registry updates.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

PROVENANCE_PATH = Path("data/provenance.json")

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_provenance() -> Dict[str, Any]:
    """Load the provenance JSON file. Creates a default structure if missing."""
    if not PROVENANCE_PATH.exists():
        # Initialize with default schema structure
        default_schema = {
            "schema_version": "1.0.0",
            "description": "Schema and instance for tracking data provenance.",
            "sources": [],
            "processing_steps": [],
            "artifacts": [],
            "created_at": None,
            "updated_at": None
        }
        save_provenance(default_schema)
        return default_schema
    
    with open(PROVENANCE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_provenance(data: Dict[str, Any]) -> None:
    """Save the provenance data to JSON."""
    # Ensure directory exists
    PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Update timestamps
    now = datetime.now(timezone.utc).isoformat()
    data["updated_at"] = now
    if not data.get("created_at"):
        data["created_at"] = now
        
    with open(PROVENANCE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def register_source(source_id: str, source_type: str, url: str, description: str) -> None:
    """Register a new data source in the provenance tracker."""
    data = load_provenance()
    
    # Check if source already exists
    existing = next((s for s in data["sources"] if s["source_id"] == source_id), None)
    if existing:
        raise ValueError(f"Source {source_id} already exists. Use update_source_checksum instead.")
    
    new_source = {
        "source_id": source_id,
        "source_type": source_type,
        "url": url,
        "description": description,
        "checksum_algorithm": "sha256",
        "checksum": None,
        "retrieved_at": None,
        "status": "pending"
    }
    
    data["sources"].append(new_source)
    save_provenance(data)

def update_source_checksum(source_id: str, file_path: Optional[str] = None, checksum: Optional[str] = None) -> None:
    """Update the checksum and status for a specific source."""
    data = load_provenance()
    
    source = next((s for s in data["sources"] if s["source_id"] == source_id), None)
    if not source:
        raise ValueError(f"Source {source_id} not found in provenance registry.")
    
    if checksum:
        source["checksum"] = checksum
        source["status"] = "verified"
    elif file_path and os.path.exists(file_path):
        source["checksum"] = compute_sha256(file_path)
        source["status"] = "verified"
    
    source["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    
    save_provenance(data)

def add_processing_step(step_name: str, input_artifacts: List[str], output_artifacts: List[str], parameters: Optional[Dict[str, Any]] = None) -> None:
    """Record a processing step in the provenance chain."""
    data = load_provenance()
    
    step = {
        "step_id": f"step_{len(data['processing_steps']) + 1}",
        "step_name": step_name,
        "input_artifacts": input_artifacts,
        "output_artifacts": output_artifacts,
        "parameters": parameters or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed"
    }
    
    data["processing_steps"].append(step)
    save_provenance(data)