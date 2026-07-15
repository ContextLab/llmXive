import os
import json
import hashlib
from typing import Dict, Optional, List
from datetime import datetime

METADATA_PATH = "data/simulation_metadata.json"

def ensure_metadata_file_exists():
    """Ensure the simulation metadata file exists with a basic structure."""
    if not os.path.exists(METADATA_PATH):
        # Ensure directory exists
        os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
        initial_data = {
            "project": "PROJ-341-evaluating-the-sensitivity-of-common-sta",
            "created_at": datetime.now().isoformat(),
            "datasets": {},
            "runs": []
        }
        with open(METADATA_PATH, 'w') as f:
            json.dump(initial_data, f, indent=2)
    return METADATA_PATH

def load_simulation_metadata() -> Dict:
    """Load the simulation metadata from disk."""
    ensure_metadata_file_exists()
    with open(METADATA_PATH, 'r') as f:
        return json.load(f)

def save_simulation_metadata(data: Dict):
    """Save the simulation metadata to disk."""
    with open(METADATA_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def compute_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.
    Reads the file in chunks to handle large files efficiently.
    """
    hasher = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_checksum(filepath: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify the checksum of a file against an expected value."""
    actual = compute_file_checksum(filepath, algorithm)
    return actual == expected_checksum

def register_run(run_info: Dict):
    """Register a new run in the metadata."""
    metadata = load_simulation_metadata()
    if "runs" not in metadata:
        metadata["runs"] = []
    metadata["runs"].append({
        "timestamp": datetime.now().isoformat(),
        **run_info
    })
    save_simulation_metadata(metadata)

def update_run_status(run_id: str, status: str):
    """Update the status of a specific run."""
    metadata = load_simulation_metadata()
    for run in metadata.get("runs", []):
        if run.get("id") == run_id:
            run["status"] = status
            break
    save_simulation_metadata(metadata)

def get_run_history() -> List[Dict]:
    """Get the history of all runs."""
    metadata = load_simulation_metadata()
    return metadata.get("runs", [])

def register_dataset_checksum(dataset_name: str, checksum: str, filepath: str):
    """
    Register a dataset checksum in the simulation metadata.
    This is the core function for T029d.
    """
    metadata = load_simulation_metadata()
    if "datasets" not in metadata:
        metadata["datasets"] = {}
    
    metadata["datasets"][dataset_name] = {
        "path": filepath,
        "checksum": checksum,
        "algorithm": "sha256",
        "registered_at": datetime.now().isoformat()
    }
    save_simulation_metadata(metadata)

def main():
    """CLI entry point for checksum utilities."""
    import argparse
    parser = argparse.ArgumentParser(description="Checksum Utilities")
    parser.add_argument("--compute", help="Compute checksum for a file", required=False)
    parser.add_argument("--verify", help="Verify checksum for a file (format: path:expected_checksum)", required=False)
    parser.add_argument("--register", help="Register dataset checksum (format: name:checksum:filepath)", required=False)
    
    args = parser.parse_args()
    
    if args.compute:
        print(compute_file_checksum(args.compute))
    elif args.verify:
        path, expected = args.verify.split(":")
        if verify_checksum(path, expected):
            print("Checksum matches.")
        else:
            print("Checksum mismatch.")
    elif args.register:
        name, checksum, filepath = args.register.split(":")
        register_dataset_checksum(name, checksum, filepath)
        print(f"Registered {name} with checksum {checksum}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()