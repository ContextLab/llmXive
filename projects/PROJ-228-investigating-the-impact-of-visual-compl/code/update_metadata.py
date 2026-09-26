import os
import yaml
import json
from datetime import datetime
from pathlib import Path
import hashlib

def ensure_dir(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def init_metadata():
    """Initialize metadata.yaml file."""
    metadata_path = Path("data/metadata.yaml")
    ensure_dir(metadata_path.parent)
    
    data = {
        "dataset_id": "",
        "version": "",
        "checksum": "",
        "download_date": ""
    }
    
    with open(metadata_path, 'w') as f:
        yaml.dump(data, f)
    
    return metadata_path

def init_project_state():
    """Initialize project state file."""
    state_dir = Path("state/projects")
    ensure_dir(state_dir)
    
    state_path = state_dir / "PROJ-228-investigating-the-impact-of-visual-compl.yaml"
    
    data = {
        "artifact_hashes": {}
    }
    
    with open(state_path, 'w') as f:
        yaml.dump(data, f)
        
    return state_path

def update_metadata_with_download(dataset_id: str, checksum: str):
    """Update metadata with download information."""
    metadata_path = Path("data/metadata.yaml")
    
    if not metadata_path.exists():
        init_metadata()
    
    with open(metadata_path, 'r') as f:
        data = yaml.safe_load(f)
    
    data["dataset_id"] = dataset_id
    data["version"] = "latest"
    data["checksum"] = checksum
    data["download_date"] = datetime.now().isoformat()
    
    with open(metadata_path, 'w') as f:
        yaml.dump(data, f)

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main entry point."""
    init_metadata()
    init_project_state()
    print("Metadata and project state initialized.")

if __name__ == "__main__":
    main()