"""
Data hashing utility for pipeline state management.

Computes SHA-256 hashes of data artifacts to track changes and ensure
reproducibility. Updates the project state file with new hashes.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from utils.logging import get_logger

logger = get_logger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE_PATTERN = "PROJ-110-*.yaml"

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")

def compute_directory_hashes(directory: Path) -> Dict[str, str]:
    """
    Compute hashes for all files in a directory recursively.
    
    Args:
        directory: Path to the directory to hash.
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist, skipping hash: {directory}")
        return {}
    
    hashes = {}
    for file_path in sorted(directory.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(directory)
            try:
                hashes[str(rel_path)] = compute_file_hash(file_path)
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Skipping file {file_path} due to error: {e}")
    
    return hashes

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load the project state YAML file.
    
    Args:
        state_path: Path to the state file.
        
    Returns:
        Dictionary containing the state data.
    """
    if not state_path.exists():
        logger.info(f"State file not found, creating new: {state_path}")
        return {
            "project_id": "PROJ-110-investigating-the-correlation-between-ci",
            "version": "1.0.0",
            "last_updated": None,
            "artifacts": {}
        }
    
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
            # Ensure required keys exist
            state.setdefault("artifacts", {})
            state.setdefault("project_id", "PROJ-110-investigating-the-correlation-between-ci")
            state.setdefault("version", "1.0.0")
            return state
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse state file {state_path}: {e}")
        raise

def save_state_file(state_path: Path, state: Dict[str, Any]) -> None:
    """
    Save the project state to a YAML file.
    
    Args:
        state_path: Path to the state file.
        state: Dictionary containing the state data.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"State file updated: {state_path}")
    except IOError as e:
        logger.error(f"Failed to write state file {state_path}: {e}")
        raise

def find_state_file() -> Optional[Path]:
    """
    Find the project state file matching the pattern.
    
    Returns:
        Path to the state file if found, None otherwise.
    """
    if not STATE_DIR.exists():
        return None
    
    matches = list(STATE_DIR.glob(STATE_FILE_PATTERN))
    if not matches:
        logger.warning(f"No state file found matching pattern: {STATE_DIR / STATE_FILE_PATTERN}")
        return None
    
    # Return the first match (should be unique)
    return matches[0]

def update_state_hash(
    artifact_paths: List[Path],
    state_file_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Compute hashes for specified artifacts and update the project state file.
    
    Args:
        artifact_paths: List of paths to artifacts to hash.
        state_file_path: Optional explicit path to the state file. 
                         If None, auto-discover using pattern.
                         
    Returns:
        Dictionary of artifact paths to their new hashes.
        
    Raises:
        FileNotFoundError: If the state file is not found and cannot be created.
    """
    if state_file_path is None:
        state_file_path = find_state_file()
        if state_file_path is None:
            # Create a new state file if none exists
            state_file_path = STATE_DIR / "PROJ-110-investigating-the-correlation-between-ci.yaml"
            logger.info(f"Creating new state file: {state_file_path}")
    
    # Load existing state
    state = load_state_file(state_file_path)
    
    # Compute hashes for provided artifacts
    new_hashes = {}
    for artifact_path in artifact_paths:
        if not artifact_path.exists():
            logger.warning(f"Artifact not found, skipping hash: {artifact_path}")
            continue
        
        try:
            file_hash = compute_file_hash(artifact_path)
            rel_path = str(artifact_path.relative_to(PROJECT_ROOT))
            new_hashes[rel_path] = file_hash
            
            # Update state
            state["artifacts"][rel_path] = {
                "hash": file_hash,
                "updated_at": datetime.utcnow().isoformat()
            }
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Failed to hash artifact {artifact_path}: {e}")
    
    # Update timestamp
    state["last_updated"] = datetime.utcnow().isoformat()
    
    # Save updated state
    save_state_file(state_file_path, state)
    
    return new_hashes

def verify_artifact_integrity(
    artifact_paths: List[Path],
    state_file_path: Optional[Path] = None
) -> Dict[str, bool]:
    """
    Verify that artifacts match their recorded hashes in the state file.
    
    Args:
        artifact_paths: List of paths to artifacts to verify.
        state_file_path: Optional explicit path to the state file.
                        
    Returns:
        Dictionary mapping artifact paths to verification status (True if valid).
    """
    if state_file_path is None:
        state_file_path = find_state_file()
    
    if state_file_path is None or not state_file_path.exists():
        logger.warning("No state file found for verification.")
        return {str(p): False for p in artifact_paths}
    
    state = load_state_file(state_file_path)
    recorded_hashes = state.get("artifacts", {})
    
    results = {}
    for artifact_path in artifact_paths:
        rel_path = str(artifact_path.relative_to(PROJECT_ROOT))
        
        if not artifact_path.exists():
            results[rel_path] = False
            logger.warning(f"Artifact missing during verification: {rel_path}")
            continue
        
        if rel_path not in recorded_hashes:
            results[rel_path] = False
            logger.warning(f"No recorded hash for artifact: {rel_path}")
            continue
        
        current_hash = compute_file_hash(artifact_path)
        recorded_hash = recorded_hashes[rel_path].get("hash")
        
        if current_hash == recorded_hash:
            results[rel_path] = True
        else:
            results[rel_path] = False
            logger.warning(f"Hash mismatch for {rel_path}: expected {recorded_hash}, got {current_hash}")
    
    return results

def get_artifact_hash(artifact_path: Path, state_file_path: Optional[Path] = None) -> Optional[str]:
    """
    Retrieve the recorded hash for a specific artifact.
    
    Args:
        artifact_path: Path to the artifact.
        state_file_path: Optional explicit path to the state file.
                        
    Returns:
        The recorded hash string, or None if not found.
    """
    if state_file_path is None:
        state_file_path = find_state_file()
    
    if state_file_path is None or not state_file_path.exists():
        return None
    
    state = load_state_file(state_file_path)
    rel_path = str(artifact_path.relative_to(PROJECT_ROOT))
    
    return state.get("artifacts", {}).get(rel_path, {}).get("hash")
