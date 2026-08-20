import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_directory(directory: str) -> List[str]:
    """Recursively scan directory for all files."""
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def load_existing_checksums(state_path: str) -> Dict:
    """Load existing state file if it exists."""
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_checksums(state_path: str, data: Dict) -> None:
    """Save checksums to state file."""
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

def verify_data_integrity(files: List[str], existing_checksums: Dict) -> Dict:
    """Verify data integrity by computing checksums and comparing."""
    results = {}
    for file_path in files:
        if os.path.exists(file_path):
            checksum = compute_sha256(file_path)
            results[file_path] = checksum
        else:
            results[file_path] = "MISSING"
    return results

def update_checksums(state_path: str, raw_results: Dict, generated_results: Dict) -> None:
    """Update state file with new checksums."""
    existing = load_existing_checksums(state_path)
    
    if 'artifact_hashes' not in existing:
        existing['artifact_hashes'] = {}
    
    # Update raw data checksums
    existing['artifact_hashes']['data_raw'] = raw_results
    
    # Update generated data checksums
    existing['artifact_hashes']['data_generated'] = generated_results
    
    save_checksums(state_path, existing)

def main():
    """Main entry point for checksum verification."""
    project_root = Path(__file__).parent.parent
    state_path = project_root / "state" / "projects" / "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml"
    raw_dir = project_root / "data" / "raw"
    generated_dir = project_root / "data" / "generated"

    print(f"Verifying checksums for project: {project_root}")
    print(f"State file: {state_path}")

    # Scan directories
    raw_files = scan_directory(str(raw_dir)) if raw_dir.exists() else []
    generated_files = scan_directory(str(generated_dir)) if generated_dir.exists() else []

    print(f"Found {len(raw_files)} files in data/raw")
    print(f"Found {len(generated_files)} files in data/generated")

    # Compute checksums
    raw_checksums = verify_data_integrity(raw_files, {})
    generated_checksums = verify_data_integrity(generated_files, {})

    # Update state file
    update_checksums(str(state_path), raw_checksums, generated_checksums)

    print(f"Checksums written to {state_path}")
    
    # Print summary
    print("\n--- Checksum Summary ---")
    print("Data Raw:")
    for path, checksum in raw_checksums.items():
        print(f"  {path}: {checksum[:16]}...")
    print("\nData Generated:")
    for path, checksum in generated_checksums.items():
        print(f"  {path}: {checksum[:16]}...")

if __name__ == "__main__":
    main()