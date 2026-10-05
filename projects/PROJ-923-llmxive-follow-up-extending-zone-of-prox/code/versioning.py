import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logging import get_logger, info

def compute_file_checksum(file_path: str) -> str:
    """Computes SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_all_data_files(data_dir: str) -> List[str]:
    """Recursively gets all files in a directory."""
    files = []
    for root, _, filenames in os.walk(data_dir):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def generate_data_manifest(data_dir: str) -> Dict[str, Any]:
    """Generates a manifest of all data files and their checksums."""
    files = get_all_data_files(data_dir)
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "files": {}
    }
    for f in files:
        manifest["files"][f] = compute_file_checksum(f)
    return manifest

def update_state_file(project_id: str, manifest: Dict[str, Any]):
    """Updates the project state file with the new manifest."""
    state_file = f"state/projects/{project_id}.yaml"
    Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {"project_id": project_id}
    
    state["data_manifest"] = manifest
    state["last_updated"] = datetime.now().isoformat()
    
    with open(state_file, 'w') as f:
        yaml.safe_dump(state, f)
    info(f"Updated state file: {state_file}")

def run_versioning(project_id: str, data_dir: str):
    """Runs the versioning process."""
    manifest = generate_data_manifest(data_dir)
    update_state_file(project_id, manifest)

def main():
    # Example usage
    run_versioning("PROJ-923-llmxive-follow-up-extending-zone-of-prox", "data")

if __name__ == "__main__":
    main()