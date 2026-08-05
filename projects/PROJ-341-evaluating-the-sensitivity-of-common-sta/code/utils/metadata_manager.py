"""Metadata manager for simulation runs and dataset checksums."""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

METADATA_FILE_PATH = "data/simulation_metadata.json"

def ensure_metadata_file_exists() -> str:
    """Ensure the metadata file exists, creating it with an empty structure if not."""
    os.makedirs(os.path.dirname(METADATA_FILE_PATH), exist_ok=True)
    if not os.path.exists(METADATA_FILE_PATH):
        initial_data = {
            "runs": [],
            "datasets": [],
            "config": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        with open(METADATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
    return METADATA_FILE_PATH

def load_simulation_metadata() -> Dict[str, Any]:
    """Load the current simulation metadata from disk."""
    ensure_metadata_file_exists()
    with open(METADATA_FILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_simulation_metadata(data: Dict[str, Any]) -> None:
    """Save the simulation metadata to disk."""
    data["last_updated"] = datetime.utcnow().isoformat()
    ensure_metadata_file_exists()
    with open(METADATA_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def compute_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """Compute the checksum of a file."""
    hasher = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_checksum(filepath: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify a file's checksum against an expected value."""
    actual_checksum = compute_file_checksum(filepath, algorithm)
    return actual_checksum == expected_checksum

def register_run(run_id: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None, status: str = "started") -> str:
    """Register a new simulation run in the metadata file."""
    metadata = load_simulation_metadata()
    run_id = run_id or str(uuid.uuid4())
    run_entry = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "parameters": parameters or {},
        "status": status,
        "checksums": []
    }
    metadata["runs"].append(run_entry)
    save_simulation_metadata(metadata)
    return run_id

def update_run_status(run_id: str, status: str, output_files: Optional[List[str]] = None) -> None:
    """Update the status of a specific run."""
    metadata = load_simulation_metadata()
    for run in metadata["runs"]:
        if run["run_id"] == run_id:
            run["status"] = status
            if output_files:
                run["output_files"] = output_files
            break
    save_simulation_metadata(metadata)

def get_run_history() -> List[Dict[str, Any]]:
    """Retrieve the history of all registered runs."""
    metadata = load_simulation_metadata()
    return metadata.get("runs", [])

def register_dataset_checksum(dataset_name: str, filepath: str, checksum: Optional[str] = None, source: Optional[str] = None) -> None:
    """Register a dataset and its checksum in the metadata file."""
    metadata = load_simulation_metadata()
    if checksum is None:
        checksum = compute_file_checksum(filepath)
    
    dataset_entry = {
        "name": dataset_name,
        "filepath": filepath,
        "checksum": checksum,
        "source": source or "unknown",
        "registered_at": datetime.utcnow().isoformat()
    }
    
    # Check if dataset already exists and update, otherwise append
    found = False
    for ds in metadata["datasets"]:
        if ds["name"] == dataset_name:
            ds.update(dataset_entry)
            found = True
            break
    
    if not found:
        metadata["datasets"].append(dataset_entry)
    
    save_simulation_metadata(metadata)

def main() -> None:
    """Main entry point for CLI usage."""
    import argparse
    parser = argparse.ArgumentParser(description="Manage simulation metadata")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Register run
    p_run = subparsers.add_parser("register_run", help="Register a new run")
    p_run.add_argument("--id", type=str, help="Custom run ID")
    p_run.add_argument("--params", type=str, help="JSON string of parameters")

    # Register dataset
    p_ds = subparsers.add_parser("register_dataset", help="Register a dataset")
    p_ds.add_argument("--name", type=str, required=True, help="Dataset name")
    p_ds.add_argument("--path", type=str, required=True, help="Filepath to dataset")
    p_ds.add_argument("--source", type=str, help="Source URL or description")

    args = parser.parse_args()

    if args.command == "register_run":
        params = json.loads(args.params) if args.params else {}
        rid = register_run(run_id=args.id, parameters=params)
        print(f"Registered run: {rid}")
    elif args.command == "register_dataset":
        register_dataset_checksum(args.name, args.path, source=args.source)
        print(f"Registered dataset: {args.name}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
