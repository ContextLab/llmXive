import os
import yaml
from typing import Dict, Optional, Any
from utils import compute_sha256
import logging
from datetime import datetime

# Ensure the state directory exists
def ensure_state_dir(state_path: str = "state") -> str:
    """
    Ensures the state directory exists.
    Returns the path to the state directory.
    """
    if not os.path.exists(state_path):
        os.makedirs(state_path, exist_ok=True)
        logging.info(f"Created state directory: {state_path}")
    return state_path

def get_hash_file_path(state_path: str = "state") -> str:
    """Returns the full path to the artifact_hashes.yaml file."""
    return os.path.join(state_path, "artifact_hashes.yaml")

def load_artifact_hashes(state_path: str = "state") -> Dict[str, Any]:
    """
    Loads the artifact_hashes.yaml file from the state directory.
    If the file does not exist, returns an empty dictionary.
    """
    hash_file = get_hash_file_path(state_path)
    if not os.path.exists(hash_file):
        logging.debug(f"No existing artifact_hashes.yaml found at {hash_file}. Initializing empty state.")
        return {"artifacts": {}, "metadata": {"last_updated": None, "version": 1}}
    
    try:
        with open(hash_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                return {"artifacts": {}, "metadata": {"last_updated": None, "version": 1}}
            return data
    except Exception as e:
        logging.error(f"Failed to load artifact_hashes.yaml: {e}")
        # Return a clean slate on corruption to prevent crashes, logging the error
        return {"artifacts": {}, "metadata": {"last_updated": None, "version": 1}}

def save_artifact_hashes(data: Dict[str, Any], state_path: str = "state") -> None:
    """
    Saves the artifact_hashes data to the YAML file.
    Updates the last_updated timestamp.
    """
    state_dir = ensure_state_dir(state_path)
    hash_file = get_hash_file_path(state_path)
    
    data["metadata"]["last_updated"] = datetime.now().isoformat()
    
    with open(hash_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    logging.info(f"Saved artifact hashes to {hash_file}")

def update_artifact_hash(artifact_path: str, state_path: str = "state") -> Optional[str]:
    """
    Computes the SHA256 hash of a file and updates the artifact_hashes.yaml.
    Returns the computed hash, or None if the file does not exist.
    """
    if not os.path.exists(artifact_path):
        logging.warning(f"Cannot update hash: file {artifact_path} does not exist.")
        return None

    file_hash = compute_sha256(artifact_path)
    if file_hash is None:
        logging.error(f"Failed to compute hash for {artifact_path}")
        return None

    data = load_artifact_hashes(state_path)
    data["artifacts"][artifact_path] = {
        "sha256": file_hash,
        "updated_at": datetime.now().isoformat()
    }
    
    save_artifact_hashes(data, state_path)
    logging.info(f"Updated hash for {artifact_path}: {file_hash}")
    return file_hash

def verify_artifact_integrity(artifact_path: str, state_path: str = "state") -> bool:
    """
    Verifies that the current SHA256 of a file matches the stored hash in artifact_hashes.yaml.
    Returns True if valid, False if mismatch or missing.
    """
    if not os.path.exists(artifact_path):
        logging.warning(f"Verification failed: file {artifact_path} does not exist.")
        return False

    data = load_artifact_hashes(state_path)
    stored_entry = data.get("artifacts", {}).get(artifact_path)
    
    if not stored_entry:
        logging.warning(f"No stored hash found for {artifact_path}. Treating as unverified.")
        return False

    stored_hash = stored_entry.get("sha256")
    if not stored_hash:
        logging.warning(f"Stored hash missing for {artifact_path}.")
        return False

    current_hash = compute_sha256(artifact_path)
    if current_hash is None:
        logging.error(f"Could not compute current hash for {artifact_path}.")
        return False

    if current_hash == stored_hash:
        logging.info(f"Integrity verified for {artifact_path}")
        return True
    else:
        logging.error(f"Integrity check FAILED for {artifact_path}. Expected {stored_hash}, got {current_hash}")
        return False
