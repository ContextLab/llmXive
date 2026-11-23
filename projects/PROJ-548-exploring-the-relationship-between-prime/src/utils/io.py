import hashlib
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import yaml

from .config import get_project_paths

# Constants for state file paths
STATE_DIR = "state/projects"
STATE_FILENAME = "PROJ-548-exploring-the-relationship-between-prime.yaml"

def _get_state_path() -> Path:
    """Returns the absolute path to the project state file."""
    root = get_project_paths()["root"]
    return Path(root) / STATE_DIR / STATE_FILENAME

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_directory_checksum(dir_path: Path, pattern: Optional[str] = None) -> Dict[str, str]:
    """
    Computes checksums for all files in a directory (recursively).
    
    Args:
        dir_path: Path to the directory.
        pattern: Optional glob pattern to filter files (e.g., "*.csv").
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    checksums = {}
    files = list(dir_path.rglob("*")) if not pattern else list(dir_path.rglob(pattern))
    
    for file_path in files:
        if file_path.is_file():
            rel_path = str(file_path.relative_to(dir_path))
            checksums[rel_path] = compute_file_checksum(file_path)
    
    return checksums

def load_state() -> Dict[str, Any]:
    """
    Loads the project state file.
    
    Returns:
        Dictionary containing the state data.
        
    Raises:
        FileNotFoundError: If the state file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    state_path = _get_state_path()
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}. "
                                "Run T008a to initialize the state file first.")
    
    with open(state_path, "r") as f:
        return yaml.safe_load(f)

def save_state(state: Dict[str, Any]) -> None:
    """
    Saves the project state to the state file.
    
    Args:
        state: Dictionary containing the state data to save.
    """
    state_path = _get_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Update timestamp
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_state_checksums(artifact_paths: List[str], state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Updates the artifact_hashes in the state file for the given artifact paths.
    
    This function computes checksums for the specified files and updates the
    state's artifact_hashes map. It satisfies Constitution Principle III (Integrity)
    by ensuring the state file accurately reflects the current state of artifacts.
    
    Args:
        artifact_paths: List of relative paths (from project root) to artifacts to checksum.
        state: Optional existing state dictionary. If None, loads from disk.
        
    Returns:
        Updated state dictionary.
        
    Raises:
        FileNotFoundError: If any artifact path does not exist.
    """
    if state is None:
        state = load_state()
    
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    root = get_project_paths()["root"]
    
    for rel_path in artifact_paths:
        full_path = Path(root) / rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found for checksum update: {full_path}")
        
        # Compute checksum
        checksum = compute_file_checksum(full_path)
        
        # Update state
        state["artifact_hashes"][rel_path] = checksum
    
    # Save updated state
    save_state(state)
    return state

def verify_data_integrity(artifact_paths: List[str], state: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    Verifies that the checksums of given artifacts match those stored in the state file.
    
    Args:
        artifact_paths: List of relative paths to artifacts to verify.
        state: Optional existing state dictionary. If None, loads from disk.
        
    Returns:
        Tuple of (is_valid, list_of_mismatched_paths).
        is_valid is True if all checksums match, False otherwise.
    """
    if state is None:
        state = load_state()
    
    stored_hashes = state.get("artifact_hashes", {})
    mismatches = []
    
    root = get_project_paths()["root"]
    
    for rel_path in artifact_paths:
        full_path = Path(root) / rel_path
        
        if rel_path not in stored_hashes:
            mismatches.append(f"{rel_path} (no stored hash)")
            continue
        
        if not full_path.exists():
            mismatches.append(f"{rel_path} (file missing)")
            continue
        
        current_checksum = compute_file_checksum(full_path)
        stored_checksum = stored_hashes[rel_path]
        
        if current_checksum != stored_checksum:
            mismatches.append(f"{rel_path} (hash mismatch)")
    
    return len(mismatches) == 0, mismatches

def get_data_change_summary(state: Dict[str, Any], new_artifact_paths: List[str]) -> str:
    """
    Generates a human-readable summary of changes for the given artifacts.
    
    Args:
        state: Current state dictionary.
        new_artifact_paths: List of relative paths to artifacts to summarize.
        
    Returns:
        Formatted string describing the changes.
    """
    lines = ["Data Change Summary", "=" * 40]
    
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    stored_hashes = state.get("artifact_hashes", {})
    root = get_project_paths()["root"]
    
    for rel_path in new_artifact_paths:
        full_path = Path(root) / rel_path
        
        if not full_path.exists():
            lines.append(f"[MISSING] {rel_path}")
            continue
        
        current_checksum = compute_file_checksum(full_path)
        stored_checksum = stored_hashes.get(rel_path)
        
        if stored_checksum is None:
            lines.append(f"[NEW] {rel_path}")
            lines.append(f"      SHA256: {current_checksum}")
        elif stored_checksum != current_checksum:
            lines.append(f"[MODIFIED] {rel_path}")
            lines.append(f"      Old SHA256: {stored_checksum}")
            lines.append(f"      New SHA256: {current_checksum}")
        else:
            lines.append(f"[UNCHANGED] {rel_path}")
    
    return "\n".join(lines)

def commit_state(artifact_paths: List[str], description: str, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Commits a new state snapshot after updating artifact checksums.
    
    This function updates the checksums for the given artifacts, adds a commit
    entry to the state history, and saves the state. It implements the
    versioning aspect of Constitution Principle V (Audit Trail).
    
    Args:
        artifact_paths: List of relative paths to artifacts to checksum and commit.
        description: Description of the changes being committed.
        state: Optional existing state dictionary. If None, loads from disk.
        
    Returns:
        Updated state dictionary.
    """
    if state is None:
        state = load_state()
    
    # Update checksums
    state = update_state_checksums(artifact_paths, state)
    
    # Add commit entry
    if "commit_history" not in state:
        state["commit_history"] = []
    
    commit_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "description": description,
        "artifacts": artifact_paths,
        "updated_hashes": {
            path: state["artifact_hashes"][path] 
            for path in artifact_paths 
            if path in state["artifact_hashes"]
        }
    }
    
    state["commit_history"].append(commit_entry)
    
    # Save
    save_state(state)
    return state
