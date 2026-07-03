"""
Artifact versioning and state tracking.
Implements Constitution Principle V: Track artifact hashes in state.yaml.
"""
import hashlib
import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

STATE_FILE = "state.yaml"

def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict:
    """Load the current state from state.yaml."""
    if not os.path.exists(STATE_FILE):
        return {"artifacts": {}}
    
    with open(STATE_FILE, "r") as f:
        content = yaml.safe_load(f)
        return content if isinstance(content, dict) else {"artifacts": {}}

def save_state(state: Dict) -> None:
    """Save the state to state.yaml."""
    with open(STATE_FILE, "w") as f:
        yaml.safe_dump(state, f, sort_keys=False, default_flow_style=False)

def update_artifact_state(file_path: str, description: str = "") -> None:
    """
    Calculate hash of an artifact and update state.yaml.
    
    Args:
        file_path: Relative path to the artifact.
        description: Optional description of the artifact.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    
    state = load_state()
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    abs_path = os.path.abspath(file_path)
    hash_value = calculate_sha256(abs_path)
    
    state["artifacts"][file_path] = {
        "hash": hash_value,
        "description": description,
        "updated_at": datetime.now().isoformat()
    }
    
    save_state(state)

def verify_artifacts(expected_hashes: Dict[str, str]) -> bool:
    """
    Verify that existing artifacts match expected hashes.
    
    Args:
        expected_hashes: Dict mapping file paths to expected hashes.
        
    Returns:
        True if all match, False otherwise.
    """
    state = load_state()
    current_hashes = {k: v["hash"] for k, v in state.get("artifacts", {}).items()}
    
    for path, expected_hash in expected_hashes.items():
        if path not in current_hashes:
            return False
        if current_hashes[path] != expected_hash:
            return False
    return True

def main():
    """
    Main entry point to hash all final artifacts and update state.yaml.
    Scans common output directories and updates state.yaml.
    """
    print("Starting artifact versioning update...")
    
    # Define directories to scan for artifacts
    scan_dirs = [
        "data/processed",
        "data/raw",
        "data/reports",
        "figures"
    ]
    
    artifacts_to_hash = []
    
    for dir_path in scan_dirs:
        if os.path.exists(dir_path):
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(('.csv', '.json', '.html', '.png', '.pdf', '.yaml', '.yml')):
                        full_path = os.path.join(root, file)
                        artifacts_to_hash.append(full_path)
    
    if not artifacts_to_hash:
        print("No artifacts found to hash in specified directories.")
        return
    
    print(f"Found {len(artifacts_to_hash)} artifacts to hash.")
    
    # Update state for each artifact
    for artifact in artifacts_to_hash:
        try:
            update_artifact_state(artifact, "Auto-tracked artifact")
            print(f"Updated: {artifact}")
        except Exception as e:
            print(f"Error processing {artifact}: {e}")
    
    print("Artifact versioning update complete.")
    print(f"State saved to {STATE_FILE}")

if __name__ == "__main__":
    main()
