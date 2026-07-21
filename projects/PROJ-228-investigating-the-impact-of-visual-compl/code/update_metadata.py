"""
Utility to initialize or update metadata files for the project.
This script ensures `data/metadata.yaml` and `state/projects/...yaml` exist
with the correct skeleton structure as required by T005a.
"""
import os
import yaml
from datetime import datetime
from pathlib import Path

# Ensure we are running from the project root or can find the paths relative to it
# Assuming this script is run from the root or code/ directory
project_root = Path(__file__).resolve().parent.parent
data_dir = project_root / "data"
state_dir = project_root / "state" / "projects"

metadata_path = data_dir / "metadata.yaml"
project_state_path = state_dir / "PROJ-228-investigating-the-impact-of-visual-compl.yaml"

def ensure_dir(path: Path):
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

def init_metadata():
    """Initialize or update data/metadata.yaml."""
    ensure_dir(metadata_path)
    
    data = {
        "dataset_id": "ds000246",
        "version": "1.0.0",
        "checksum": "",
        "download_date": ""
    }
    
    if metadata_path.exists():
        # Load existing to preserve any future fields if needed, but enforce structure
        with open(metadata_path, 'r') as f:
            existing = yaml.safe_load(f) or {}
            data.update(existing)
    
    with open(metadata_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)
    
    print(f"Updated {metadata_path}")

def init_project_state():
    """Initialize or update state/projects/PROJ-228-investigating-the-impact-of-visual-compl.yaml."""
    ensure_dir(project_state_path)
    
    data = {
        "project_id": "PROJ-228-investigating-the-impact-of-visual-compl",
        "title": "Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity",
        "status": "in_progress",
        "artifact_hashes": {}
    }
    
    if project_state_path.exists():
        with open(project_state_path, 'r') as f:
            existing = yaml.safe_load(f) or {}
            data.update(existing)
    
    with open(project_state_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)
    
    print(f"Updated {project_state_path}")

if __name__ == "__main__":
    init_metadata()
    init_project_state()
    print("T005a implementation complete: Metadata and Project State files initialized.")