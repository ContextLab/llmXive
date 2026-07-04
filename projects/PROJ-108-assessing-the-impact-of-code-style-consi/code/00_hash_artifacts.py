"""
Hash Artifacts Script (T005)

Generates content hashes (SHA-256) for data artifacts and updates the project state.
Dependencies: T004 (URL validation) must have run successfully to ensure data integrity.

Outputs:
    - Prints a report of processed files and their hashes.
    - Updates `state/hashes.yaml` with the current artifact hashes.
"""
import os
import hashlib
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"
HASHES_FILE = STATE_DIR / "hashes.yaml"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")

def find_data_artifacts(data_dir: Path) -> List[Path]:
    """
    Recursively find all non-hidden data artifacts.
    Skips .gitkeep and temporary files.
    """
    artifacts = []
    if not data_dir.exists():
        return artifacts

    for root, dirs, files in os.walk(data_dir):
        # Ignore hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.startswith('.'):
                continue
            if file.endswith('.gitkeep'):
                continue
            if file.endswith('.tmp'):
                continue
            
            file_path = Path(root) / file
            # Check if it's a real file and has content
            if file_path.is_file() and file_path.stat().st_size > 0:
                artifacts.append(file_path)
    
    return sorted(artifacts)

def load_current_state() -> Dict[str, Any]:
    """Load existing state file if it exists."""
    if HASHES_FILE.exists():
        try:
            with open(HASHES_FILE, 'r') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError:
            return {}
    return {}

def save_state(state: Dict[str, Any], output_path: Path) -> None:
    """Save state to YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def main():
    """Main execution entry point."""
    print(f"Scanning for data artifacts in: {DATA_DIR}")
    
    if not DATA_DIR.exists():
        print("Error: Data directory does not exist. Please run T001/T007 first.")
        sys.exit(1)

    # Check dependency T004 success indicator (optional but good practice)
    # We assume if we are here, T004 passed. If T004 failed, data might be missing.
    
    artifacts = find_data_artifacts(DATA_DIR)
    
    if not artifacts:
        print("No data artifacts found to hash.")
        # Still save an empty state or update timestamp
        current_state = load_current_state()
        current_state['last_scan'] = datetime.utcnow().isoformat()
        current_state['artifacts'] = {}
        save_state(current_state, HASHES_FILE)
        print(f"Updated state file: {HASHES_FILE}")
        return

    print(f"Found {len(artifacts)} artifacts.")
    
    current_state = load_current_state()
    new_hashes = {}
    
    for artifact in artifacts:
        relative_path = artifact.relative_to(PROJECT_ROOT)
        try:
            file_hash = calculate_sha256(artifact)
            new_hashes[str(relative_path)] = {
                "hash": file_hash,
                "size_bytes": artifact.stat().st_size,
                "last_modified": datetime.utcfromtimestamp(artifact.stat().st_mtime).isoformat()
            }
            print(f"  Hashed: {relative_path} -> {file_hash[:16]}...")
        except Exception as e:
            print(f"  ERROR hashing {relative_path}: {e}")
            # Continue to next file

    # Update state
    current_state['last_scan'] = datetime.utcnow().isoformat()
    current_state['artifacts'] = new_hashes
    
    save_state(current_state, HASHES_FILE)
    
    print(f"\nSuccessfully updated state file: {HASHES_FILE}")
    print(f"Total artifacts processed: {len(new_hashes)}")

if __name__ == "__main__":
    main()