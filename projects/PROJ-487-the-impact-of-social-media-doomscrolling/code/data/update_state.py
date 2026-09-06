import os
import sys
import json
import logging
import hashlib
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_state(state_path: str) -> dict:
    """Load the state YAML file."""
    if not os.path.exists(state_path):
        # Initialize new state if not exists
        return {
            "project_id": "PROJ-487",
            "branch": "001-news-volume-anxiety",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "artifact_hashes": {},
            "status": "active"
        }
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def save_state(state_path: str, state: dict):
    """Save the state to the YAML file."""
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def update_artifact_hashes(state_path: str, files: list):
    """Update the artifact_hashes in the state file with MD5 checksums."""
    state = load_state(state_path)
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    for file_path in files:
        if os.path.exists(file_path):
            md5 = calculate_md5(file_path)
            file_name = os.path.basename(file_path)
            state['artifact_hashes'][file_name] = md5
            logger.info(f"Updated checksum for {file_name}: {md5}")
        else:
            logger.warning(f"File not found, skipping: {file_path}")
    
    state['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    save_state(state_path, state)
    logger.info("State file updated successfully.")

def main():
    """Main entry point for T037: Update State File."""
    project_root = Path(__file__).resolve().parent.parent.parent
    state_file = project_root / "state" / "projects" / "PROJ-487-the-impact-of-social-media-doomscrolling.yaml"
    
    gdelt_file = project_root / "data" / "raw" / "gdelt_events.csv"
    trends_file = project_root / "data" / "raw" / "google_trends.csv"
    
    files_to_hash = [str(gdelt_file), str(trends_file)]
    
    if not os.path.exists(state_file):
        logger.info(f"Creating new state file at {state_file}")
    
    update_artifact_hashes(str(state_file), files_to_hash)

if __name__ == "__main__":
    main()