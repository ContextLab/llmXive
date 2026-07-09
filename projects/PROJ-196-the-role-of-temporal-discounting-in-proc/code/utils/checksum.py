"""
Checksum verification utility.
Implements T009: Data checksum verification and state tracking.
"""
import os
import hashlib
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

# Import PROJECT_ROOT from config
try:
    from ..config import PROJECT_ROOT
except ImportError:
    # Fallback for direct execution or different import context
    from config import get_project_root
    PROJECT_ROOT = get_project_root()

STATE_FILE = os.path.join(PROJECT_ROOT, "state", "projects", "PROJ-196-the-role-of-temporal-discounting-in-proc.yaml")

def ensure_state_file():
    """
    Ensures the state file exists and has the correct structure.
    Creates the directory and initial file if missing.
    """
    state_dir = os.path.dirname(STATE_FILE)
    os.makedirs(state_dir, exist_ok=True)
    
    if not os.path.exists(STATE_FILE):
        initial_state = {
            "project_id": "PROJ-196-the-role-of-temporal-discounting-in-proc",
            "artifact_hashes": {},
            "status": "initialized"
        }
        with open(STATE_FILE, "w") as f:
            yaml.dump(initial_state, f)

def calculate_file_hash(filepath: str) -> str:
    """
    Calculates SHA-256 hash of a file content.
    
    Args:
        filepath: Absolute or relative path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found for hashing: {filepath}")
        
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_artifact_hash(filepath: str, description: Optional[str] = None) -> None:
    """
    Updates the artifact_hashes map in the state file for a given file.
    Computes the hash of the current file and writes it to the state YAML.
    
    Args:
        filepath: Path to the artifact file (relative to project root or absolute).
        description: Optional description of the artifact.
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
        yaml.YAMLError: If the state file is corrupted.
    """
    ensure_state_file()
    
    # Resolve path relative to PROJECT_ROOT if not absolute
    if not os.path.isabs(filepath):
        full_path = os.path.join(PROJECT_ROOT, filepath)
    else:
        full_path = filepath
        
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Artifact not found: {full_path}")
        
    rel_path = os.path.relpath(full_path, PROJECT_ROOT)
    file_hash = calculate_file_hash(full_path)
    
    with open(STATE_FILE, "r") as f:
        state = yaml.safe_load(f)
    
    if state is None:
        state = {"artifact_hashes": {}}
        
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    state["artifact_hashes"][rel_path] = {
        "hash": file_hash,
        "description": description or rel_path
    }
    
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f)

def verify_artifacts() -> Dict[str, bool]:
    """
    Verifies all tracked artifacts against their stored hashes in the state file.
    
    Returns:
        Dict mapping relative file paths to boolean validity (True if hash matches).
        Files missing from disk are marked False.
    """
    ensure_state_file()
    with open(STATE_FILE, "r") as f:
        state = yaml.safe_load(f)
    
    results = {}
    artifact_map = state.get("artifact_hashes", {})
    
    if not artifact_map:
        return results
        
    for rel_path, info in artifact_map.items():
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        
        if not os.path.exists(full_path):
            results[rel_path] = False
            continue
        
        try:
            current_hash = calculate_file_hash(full_path)
            expected_hash = info.get("hash")
            results[rel_path] = (current_hash == expected_hash)
        except Exception:
            results[rel_path] = False
    
    return results

def update_all_artifacts_in_directory(directory: str, pattern: str = "*.csv", description_prefix: str = "") -> int:
    """
    Scans a directory for files matching a pattern and updates their hashes in the state file.
    
    Args:
        directory: Relative path from project root to scan (e.g., "data/raw").
        pattern: Glob pattern for files (e.g., "*.csv", "*.parquet").
        description_prefix: Optional prefix for the description field.
        
    Returns:
        Number of artifacts updated.
    """
    import glob
    
    full_dir = os.path.join(PROJECT_ROOT, directory)
    if not os.path.isdir(full_dir):
        return 0
        
    search_pattern = os.path.join(full_dir, pattern)
    files = glob.glob(search_pattern)
    
    updated_count = 0
    for filepath in files:
        try:
            rel_path = os.path.relpath(filepath, PROJECT_ROOT)
            desc = f"{description_prefix}{rel_path}" if description_prefix else rel_path
            update_artifact_hash(filepath, desc)
            updated_count += 1
        except FileNotFoundError:
            continue
            
    return updated_count

def get_state() -> Dict[str, Any]:
    """
    Loads and returns the entire state file content.
    """
    ensure_state_file()
    with open(STATE_FILE, "r") as f:
        return yaml.safe_load(f)

def clear_artifact_hashes() -> None:
    """
    Clears all artifact hashes from the state file.
    Useful for resetting state before a fresh pipeline run.
    """
    ensure_state_file()
    with open(STATE_FILE, "r") as f:
        state = yaml.safe_load(f)
    
    state["artifact_hashes"] = {}
    state["status"] = "cleared"
    
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f)
