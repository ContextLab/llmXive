"""
State management utility for llmXive project PROJ-405.

Handles SHA-256 hashing of artifacts and updates state/*.yaml files
to ensure reproducibility and traceability (Constitution Principle V).
"""
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

from config import get_path, ensure_dirs
from utils.logging_config import get_logger

logger = get_logger(__name__)

STATE_DIR = "state"


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal SHA-256 hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files without loading entirely into memory
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Failed to read file {file_path} for hashing: {e}")
        raise


def compute_data_hash(data: bytes) -> str:
    """
    Compute SHA-256 hash of raw bytes.
    
    Args:
        data: Raw bytes to hash.
        
    Returns:
        Hexadecimal SHA-256 hash string.
    """
    return hashlib.sha256(data).hexdigest()


def load_state_file(state_file: Path) -> Dict:
    """
    Load an existing state YAML file or return an empty structure if it doesn't exist.
    
    Args:
        state_file: Path to the state YAML file.
        
    Returns:
        Dictionary containing state data.
    """
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = yaml.safe_load(f)
                return state if state else {}
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse existing state file {state_file}: {e}. Starting fresh.")
            return {}
    return {}


def save_state_file(state_file: Path, state: Dict) -> None:
    """
    Save the state dictionary to a YAML file.
    
    Args:
        state_file: Path to the state YAML file.
        state: Dictionary to save.
    """
    ensure_dirs(state_file.parent)
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(
            state,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2
        )
    logger.info(f"State saved to {state_file}")


def update_artifact_state(
    artifact_path: Union[str, Path],
    state_key: Optional[str] = None,
    state_file_name: str = "pipeline_state.yaml"
) -> Dict:
    """
    Compute hash for an artifact and update the corresponding state file.
    
    This function:
    1. Computes the SHA-256 hash of the artifact.
    2. Loads the existing state file (or creates a new one).
    3. Updates the entry for the artifact with the new hash and timestamp.
    4. Saves the updated state file.
    
    Args:
        artifact_path: Path to the artifact file.
        state_key: Optional key to use in the state file. Defaults to the artifact's relative path.
        state_file_name: Name of the state file in the state directory.
        
    Returns:
        Dictionary containing the updated state entry for this artifact.
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    artifact_path = Path(artifact_path)
    state_file = get_path(STATE_DIR, state_file_name)
    
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    # Determine the key for this artifact in the state file
    if state_key is None:
        state_key = str(artifact_path.relative_to(get_path("")))
    
    # Compute hash
    file_hash = compute_file_hash(artifact_path)
    
    # Load existing state
    state = load_state_file(state_file)
    
    # Ensure 'artifacts' section exists
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    # Update entry
    state["artifacts"][state_key] = {
        "hash": file_hash,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "path": str(artifact_path)
    }
    
    # Save state
    save_state_file(state_file, state)
    
    logger.info(f"Updated state for artifact: {state_key} (hash: {file_hash[:16]}...)")
    return state["artifacts"][state_key]


def verify_artifact_integrity(
    artifact_path: Union[str, Path],
    expected_hash: str,
    state_file_name: str = "pipeline_state.yaml"
) -> bool:
    """
    Verify that an artifact's current hash matches the expected hash.
    
    Args:
        artifact_path: Path to the artifact file.
        expected_hash: The expected SHA-256 hash.
        state_file_name: Name of the state file (used for logging).
        
    Returns:
        True if the hash matches, False otherwise.
    """
    artifact_path = Path(artifact_path)
    if not artifact_path.exists():
        logger.error(f"Artifact not found for verification: {artifact_path}")
        return False
    
    current_hash = compute_file_hash(artifact_path)
    
    if current_hash == expected_hash:
        logger.debug(f"Integrity verified for {artifact_path}")
        return True
    else:
        logger.error(
            f"Integrity check FAILED for {artifact_path}. "
            f"Expected: {expected_hash}, Got: {current_hash}"
        )
        return False


def get_artifact_hash(
    artifact_path: Union[str, Path],
    state_file_name: str = "pipeline_state.yaml"
) -> Optional[str]:
    """
    Retrieve the stored hash for an artifact from the state file.
    
    Args:
        artifact_path: Path to the artifact file.
        state_file_name: Name of the state file.
        
    Returns:
        The stored hash string, or None if not found.
    """
    state_file = get_path(STATE_DIR, state_file_name)
    if not state_file.exists():
        return None
        
    state = load_state_file(state_file)
    state_key = str(Path(artifact_path).relative_to(get_path("")))
    
    if "artifacts" in state and state_key in state["artifacts"]:
        return state["artifacts"][state_key].get("hash")
    
    return None


def batch_update_state(
    artifacts: List[Union[str, Path]],
    state_file_name: str = "pipeline_state.yaml"
) -> Dict:
    """
    Update state for multiple artifacts in a single operation.
    
    Args:
        artifacts: List of artifact paths.
        state_file_name: Name of the state file.
        
    Returns:
        Dictionary containing all updated state entries.
    """
    state_file = get_path(STATE_DIR, state_file_name)
    state = load_state_file(state_file)
    
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    updated_entries = {}
    
    for artifact_path in artifacts:
        artifact_path = Path(artifact_path)
        if not artifact_path.exists():
            logger.warning(f"Skipping non-existent artifact: {artifact_path}")
            continue
        
        state_key = str(artifact_path.relative_to(get_path("")))
        file_hash = compute_file_hash(artifact_path)
        
        state["artifacts"][state_key] = {
            "hash": file_hash,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "path": str(artifact_path)
        }
        updated_entries[state_key] = state["artifacts"][state_key]
        logger.info(f"Updated state for: {state_key}")
    
    save_state_file(state_file, state)
    return updated_entries
