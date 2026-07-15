"""
Metadata manager for simulation runs and dataset checksums.
Provides schema and utilities for data/simulation_metadata.json.
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

METADATA_FILE_PATH = "data/simulation_metadata.json"

def ensure_metadata_file_exists() -> str:
    """
    Ensures the metadata JSON file exists. If not, creates it with an empty schema.
    Returns the path to the file.
    """
    os.makedirs(os.path.dirname(METADATA_FILE_PATH), exist_ok=True)
    if not os.path.exists(METADATA_FILE_PATH):
        initial_schema = {
            "schema_version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "runs": [],
            "datasets": [],
            "config": {}
        }
        with open(METADATA_FILE_PATH, 'w') as f:
            json.dump(initial_schema, f, indent=2)
    return METADATA_FILE_PATH

def load_simulation_metadata() -> Dict[str, Any]:
    """Loads the current metadata file content."""
    ensure_metadata_file_exists()
    with open(METADATA_FILE_PATH, 'r') as f:
        return json.load(f)

def save_simulation_metadata(data: Dict[str, Any]) -> None:
    """Saves the metadata dictionary back to the file."""
    ensure_metadata_file_exists()
    with open(METADATA_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Computes the checksum of a file."""
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """Verifies a file's checksum against an expected value."""
    if not os.path.exists(file_path):
        return False
    actual = compute_file_checksum(file_path, algorithm)
    return actual == expected_checksum

def register_run(run_params: Dict[str, Any]) -> str:
    """
    Registers a new simulation run in the metadata file.
    Returns the run_id.
    """
    data = load_simulation_metadata()
    run_id = str(uuid.uuid4())
    run_record = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "params": run_params,
        "status": "started",
        "outputs": []
    }
    data["runs"].append(run_record)
    save_simulation_metadata(data)
    return run_id

def update_run_status(run_id: str, status: str, outputs: Optional[List[str]] = None) -> None:
    """Updates the status of a specific run."""
    data = load_simulation_metadata()
    for run in data["runs"]:
        if run["run_id"] == run_id:
            run["status"] = status
            if outputs:
                run["outputs"] = outputs
            run["completed_at"] = datetime.utcnow().isoformat()
            break
    save_simulation_metadata(data)

def get_run_history() -> List[Dict[str, Any]]:
    """Returns the list of all registered runs."""
    data = load_simulation_metadata()
    return data.get("runs", [])

def register_dataset_checksum(dataset_name: str, file_path: str, algorithm: str = 'sha256') -> None:
    """
    Registers a dataset checksum in the metadata file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    checksum = compute_file_checksum(file_path, algorithm)
    data = load_simulation_metadata()
    
    # Check if dataset already registered
    for ds in data.get("datasets", []):
        if ds["name"] == dataset_name:
            ds["checksum"] = checksum
            ds["last_verified"] = datetime.utcnow().isoformat()
            ds["file_path"] = file_path
            break
    else:
        data["datasets"].append({
            "name": dataset_name,
            "file_path": file_path,
            "checksum": checksum,
            "algorithm": algorithm,
            "registered_at": datetime.utcnow().isoformat(),
            "last_verified": datetime.utcnow().isoformat()
        })
    
    save_simulation_metadata(data)

def main() -> None:
    """
    CLI entry point to initialize or inspect metadata.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Manage simulation metadata")
    parser.add_argument('--init', action='store_true', help='Initialize metadata file')
    parser.add_argument('--show', action='store_true', help='Show current metadata')
    args = parser.parse_args()

    if args.init:
        ensure_metadata_file_exists()
        print(f"Metadata file initialized at {METADATA_FILE_PATH}")
    elif args.show:
        data = load_simulation_metadata()
        print(json.dumps(data, indent=2))
    else:
        # Default to init if no args
        ensure_metadata_file_exists()
        print(f"Metadata file ready at {METADATA_FILE_PATH}")

if __name__ == "__main__":
    main()
