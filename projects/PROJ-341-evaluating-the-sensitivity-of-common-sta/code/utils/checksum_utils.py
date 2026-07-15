"""
Checksum and metadata management utilities.
"""
import os
import json
import hashlib
from typing import Dict, Optional, List
from datetime import datetime
import uuid

from code.simulation.logging_config import get_logger

logger = get_logger("checksum_utils")

METADATA_FILE = "data/simulation_metadata.json"

def ensure_metadata_file_exists():
    """Ensure the metadata file exists, creating it if necessary."""
    if not os.path.exists(METADATA_FILE):
        logger.log("creating_metadata_file", path=METADATA_FILE)
        with open(METADATA_FILE, 'w') as f:
            json.dump({
                "runs": [],
                "datasets": [],
                "created_at": datetime.utcnow().isoformat()
            }, f, indent=2)
    return METADATA_FILE

def load_simulation_metadata() -> Dict:
    """Load the simulation metadata file."""
    ensure_metadata_file_exists()
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)

def save_simulation_metadata(data: Dict):
    """Save the simulation metadata file."""
    ensure_metadata_file_exists()
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(filepath: str, expected_checksum: str) -> bool:
    """Verify a file's checksum against an expected value."""
    try:
        actual = compute_file_checksum(filepath)
        return actual == expected_checksum
    except Exception:
        return False

def register_run(run_type: str, parameters: Optional[Dict] = None):
    """
    Register a new run in the metadata file.
    Supports both old signature (run_type) and new signature (run_type, parameters).
    """
    data = load_simulation_metadata()
    
    run_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    run_entry = {
        "id": run_id,
        "type": run_type,
        "timestamp": timestamp,
        "parameters": parameters or {}
    }
    
    data["runs"].append(run_entry)
    save_simulation_metadata(data)
    logger.log("run_registered", run_id=run_id, type=run_type)
    return run_id

def update_run_status(run_id: str, status: str, details: Optional[Dict] = None):
    """Update the status of a run."""
    data = load_simulation_metadata()
    for run in data["runs"]:
        if run["id"] == run_id:
            run["status"] = status
            run["updated_at"] = datetime.utcnow().isoformat()
            if details:
                run["details"] = details
            save_simulation_metadata(data)
            return
    logger.log("run_not_found", run_id=run_id)

def get_run_history(run_type: Optional[str] = None) -> List[Dict]:
    """Get the history of runs, optionally filtered by type."""
    data = load_simulation_metadata()
    if run_type:
        return [r for r in data["runs"] if r["type"] == run_type]
    return data["runs"]

def register_dataset_checksum(dataset_name: str, filepath: str, checksum: Optional[str] = None):
    """Register a dataset and its checksum."""
    if checksum is None:
        checksum = compute_file_checksum(filepath)
    
    data = load_simulation_metadata()
    
    dataset_entry = {
        "name": dataset_name,
        "filepath": filepath,
        "checksum": checksum,
        "registered_at": datetime.utcnow().isoformat()
    }
    
    # Check if already exists
    for i, ds in enumerate(data["datasets"]):
        if ds["name"] == dataset_name:
            data["datasets"][i] = dataset_entry
            break
    else:
        data["datasets"].append(dataset_entry)
    
    save_simulation_metadata(data)
    logger.log("dataset_registered", name=dataset_name, checksum=checksum)

def main():
    """Main entry point for testing."""
    logger.log("checksum_utils_main")
    # Example usage
    ensure_metadata_file_exists()
    run_id = register_run("test", {"test": "value"})
    print(f"Registered run: {run_id}")

if __name__ == "__main__":
    main()
