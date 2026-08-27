import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

def calculate_file_hash(file_path: str) -> str:
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_with_manifest(manifest_path: str, state_file_path: str) -> None:
    """
    Reads a manifest JSON file and updates the project state YAML file
    with the checksums of the artifacts.
    """
    manifest_path = Path(manifest_path)
    state_file_path = Path(state_file_path)

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)

    files = manifest_data.get("files", {})
    
    # Prepare state structure
    state = {
        "project_id": "PROJ-829-llmxive-follow-up-extending-fashionchame",
        "artifacts": {}
    }

    # Populate artifacts from manifest
    for rel_path, info in files.items():
        state["artifacts"][rel_path] = {
            "hash": info.get("hash"),
            "size": info.get("size")
        }

    # Ensure state directory exists
    state_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state if present to preserve other fields (like seeds, previous runs)
    if state_file_path.exists():
        try:
            with open(state_file_path, 'r') as f:
                existing_state = yaml.safe_load(f) or {}
            # Merge new artifact data into existing state
            existing_state.setdefault("artifacts", {}).update(state["artifacts"])
            # Keep other metadata (e.g., seeds, timestamps)
            state = existing_state
        except yaml.YAMLError as e:
            print(f"Warning: Could not parse existing state file {state_file_path}: {e}. Overwriting.")
            # Fallback to new state if parsing fails

    # Write updated state
    with open(state_file_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    print(f"State updated successfully at {state_file_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update State with Manifest")
    parser.add_argument('--manifest', type=str, default='data/processed/manifest.json', help='Path to manifest JSON')
    parser.add_argument('--state', type=str, default='state/projects/PROJ-829-llmxive-follow-up-extending-fashionchame.yaml', help='Path to state YAML')
    args = parser.parse_args()

    update_state_with_manifest(args.manifest, args.state)

if __name__ == '__main__':
    main()