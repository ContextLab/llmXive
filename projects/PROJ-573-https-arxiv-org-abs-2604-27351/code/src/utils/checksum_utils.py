import hashlib
import os
from pathlib import Path
from typing import Dict, Any

def compute_file_sha256(file_path: str) -> str:
    """
    Compute the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state_file(state_path: str) -> Dict[str, Any]:
    """
    Load the state YAML file, creating it with default structure if it doesn't exist.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        Dictionary containing the state data.
    """
    import yaml
    state_path_obj = Path(state_path)
    
    if not state_path_obj.exists():
        # Ensure directory exists
        state_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Create default structure
        default_state = {
            "project_id": state_path_obj.stem,
            "updated_at": None,
            "artifact_hashes": {}
        }
        
        with open(state_path_obj, 'w', encoding='utf-8') as f:
            yaml.dump(default_state, f, default_flow_style=False, sort_keys=False)
        
        return default_state
    
    with open(state_path_obj, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def save_state_file(state_path: str, data: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the YAML file.
    
    Args:
        state_path: Path to the state YAML file.
        data: Dictionary to save.
    """
    import yaml
    state_path_obj = Path(state_path)
    state_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path_obj, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def update_artifact_hash(state_path: str, artifact_path: str) -> None:
    """
    Compute the SHA256 hash of an artifact and update the state file.
    
    Args:
        state_path: Path to the state YAML file (e.g., state/projects/PROJ-573-...yaml).
        artifact_path: Path to the artifact file to hash.
    """
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    state_data = load_state_file(state_path)
    hash_value = compute_file_sha256(artifact_path)
    
    # Ensure artifact_hashes exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    state_data["artifact_hashes"][artifact_path] = {
        "sha256": hash_value
    }
    
    save_state_file(state_path, state_data)

def main():
    """
    CLI entry point to demonstrate checksum tracking.
    Usage: python -m src.utils.checksum_utils --state <state_file> --artifact <file_to_hash>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Checksum tracking utility")
    parser.add_argument("--state", required=True, help="Path to state YAML file")
    parser.add_argument("--artifact", required=True, help="Path to artifact to hash")
    
    args = parser.parse_args()
    
    try:
        update_artifact_hash(args.state, args.artifact)
        print(f"Successfully updated hash for {args.artifact} in {args.state}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
