import os
import hashlib
import json
from typing import Dict, Optional, List
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
METADATA_FILE = os.path.join(PROJECT_ROOT, 'data', 'simulation_metadata.json')

def compute_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(filepath: str, expected_checksum: str) -> bool:
    """Verify file checksum matches expected."""
    actual = compute_file_checksum(filepath)
    return actual == expected_checksum

def ensure_metadata_file_exists():
    """Ensure metadata file exists, create if not."""
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'w') as f:
            json.dump({
                "project_id": "PROJ-341-evaluating-the-sensitivity-of-common-sta",
                "created_at": datetime.now().isoformat(),
                "runs": [],
                "datasets": [],
                "seeds": {"base_seed": 42, "strategy": "linear_increment"},
                "config": {"max_memory_gb": 7.0, "chunk_size": 1000}
            }, f, indent=2)

def load_simulation_metadata() -> Dict:
    """Load simulation metadata."""
    ensure_metadata_file_exists()
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)

def save_simulation_metadata(data: Dict):
    """Save simulation metadata."""
    ensure_metadata_file_exists()
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def register_dataset_checksum(dataset_name: str, filepath: str, checksum: str):
    """Register a dataset and its checksum in metadata."""
    metadata = load_simulation_metadata()
    existing = next((d for d in metadata['datasets'] if d['name'] == dataset_name), None)
    if existing:
        existing['checksum'] = checksum
        existing['last_verified'] = datetime.now().isoformat()
    else:
        metadata['datasets'].append({
            'name': dataset_name,
            'filepath': filepath,
            'checksum': checksum,
            'registered_at': datetime.now().isoformat()
        })
    save_simulation_metadata(metadata)

def main():
    """Main entry point for checksum utilities."""
    print("Checksum Utility - Use functions programmatically.")

if __name__ == '__main__':
    main()
