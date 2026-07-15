import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List

def ensure_metadata_file_exists(filepath: str = "data/simulation_metadata.json") -> None:
    """Ensure the simulation metadata file exists."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump({
                'created_at': str(datetime.now()),
                'runs': [],
                'datasets': [],
                'checksums': {}
            }, f, indent=2)

def load_simulation_metadata(filepath: str = "data/simulation_metadata.json") -> Dict[str, Any]:
    """Load simulation metadata from JSON file."""
    if not os.path.exists(filepath):
        return {'created_at': str(datetime.now()), 'runs': [], 'datasets': [], 'checksums': {}}
    
    with open(filepath, 'r') as f:
        return json.load(f)

def save_simulation_metadata(metadata: Dict[str, Any], filepath: str = "data/simulation_metadata.json") -> None:
    """Save simulation metadata to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)

def register_run(metadata: Dict[str, Any], run_info: Dict[str, Any]) -> Dict[str, Any]:
    """Register a new simulation run in metadata."""
    if 'runs' not in metadata:
        metadata['runs'] = []
    
    run_info['timestamp'] = str(datetime.now())
    metadata['runs'].append(run_info)
    return metadata

def update_run_status(metadata: Dict[str, Any], run_id: str, status: str) -> Dict[str, Any]:
    """Update the status of a specific run."""
    for run in metadata.get('runs', []):
        if run.get('run_id') == run_id:
            run['status'] = status
            run['updated_at'] = str(datetime.now())
            break
    return metadata

def get_run_history(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get history of all runs."""
    return metadata.get('runs', [])

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def register_dataset_checksum(metadata: Dict[str, Any], dataset_name: str, filepath: str, checksum: str) -> Dict[str, Any]:
    """Register a dataset checksum in metadata."""
    if 'datasets' not in metadata:
        metadata['datasets'] = []
    
    metadata['datasets'].append({
        'name': dataset_name,
        'filepath': filepath,
        'checksum': checksum,
        'registered_at': str(datetime.now())
    })
    
    if 'checksums' not in metadata:
        metadata['checksums'] = {}
    metadata['checksums'][filepath] = checksum
    
    return metadata

def main():
    """Main function for metadata management."""
    print("Metadata manager utility")
    pass

if __name__ == "__main__":
    main()
