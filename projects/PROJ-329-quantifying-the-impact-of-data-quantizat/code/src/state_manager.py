"""
State Manager Module for llmXive Automated Science Pipeline.

Implements Constitution V: Record artifact hashes after each phase to ensure
reproducibility and integrity tracking.

This module provides functions to:
- Calculate SHA-256 hashes for files and directories
- Load and save state files (YAML format)
- Record phase states with timestamps
- Verify artifact integrity against recorded hashes
"""

import hashlib
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_directory_hash(dir_path: Path, exclude_patterns: Optional[List[str]] = None) -> str:
    """
    Calculate a combined hash for all files in a directory.
    
    The hash is computed by:
    1. Collecting all files (sorted by path for reproducibility)
    2. Computing individual file hashes
    3. Combining them into a final hash
    
    Args:
        dir_path: Path to the directory to hash
        exclude_patterns: List of glob patterns to exclude (e.g., ['*.pyc', '__pycache__'])
        
    Returns:
        Hexadecimal string of the combined SHA-256 hash
        
    Raises:
        FileNotFoundError: If the directory does not exist
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
    
    exclude_patterns = exclude_patterns or []
    combined_hash = hashlib.sha256()
    
    # Collect all files, sorted for reproducibility
    all_files = []
    for root, dirs, files in os.walk(dir_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not any(
            Path(root, d).match(pattern) or d == pattern for pattern in exclude_patterns
        )]
        
        for file in sorted(files):
            file_path = Path(root) / file
            # Check if file matches any exclude pattern
            if any(file_path.match(pattern) for pattern in exclude_patterns):
                continue
            all_files.append(file_path)
    
    # Sort all files by relative path
    all_files.sort(key=lambda p: str(p.relative_to(dir_path)))
    
    for file_path in all_files:
        # Include relative path in hash for structure awareness
        rel_path = str(file_path.relative_to(dir_path))
        combined_hash.update(rel_path.encode('utf-8'))
        
        # Include file content hash
        file_hash = calculate_file_hash(file_path)
        combined_hash.update(file_hash.encode('utf-8'))
    
    return combined_hash.hexdigest()


def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load state from a YAML file.
    
    Args:
        state_path: Path to the state file
        
    Returns:
        Dictionary containing the state data
        
    Raises:
        FileNotFoundError: If the state file does not exist
        yaml.YAMLError: If the file is not valid YAML
    """
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_state_file(state_path: Path, state: Dict[str, Any]) -> None:
    """
    Save state to a YAML file.
    
    Args:
        state_path: Path to the state file
        state: Dictionary containing the state data
    """
    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def record_phase_state(
    phase_name: str,
    artifacts: List[Path],
    state_path: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Record the state of artifacts after a phase completion.
    
    This function:
    1. Calculates hashes for all provided artifacts
    2. Loads the existing state file (or creates a new one)
    3. Appends a new phase entry with timestamp and artifact hashes
    4. Saves the updated state
    
    Args:
        phase_name: Name of the phase (e.g., 'Phase 1: Setup')
        artifacts: List of file paths to record
        state_path: Optional path to state file (defaults to project_root/state.yaml)
        project_root: Optional project root (defaults to current working directory)
        
    Returns:
        The updated state dictionary
        
    Raises:
        FileNotFoundError: If any artifact does not exist
    """
    if project_root is None:
        project_root = Path.cwd()
    
    if state_path is None:
        state_path = project_root / "state.yaml"
    
    # Load existing state or initialize new
    try:
        state = load_state_file(state_path)
    except FileNotFoundError:
        state = {
            "project": str(project_root),
            "phases": [],
            "last_updated": None
        }
    
    # Calculate hashes for all artifacts
    artifact_records = []
    for artifact in artifacts:
        if not artifact.exists():
            raise FileNotFoundError(f"Artifact not found: {artifact}")
        
        artifact_path = artifact.relative_to(project_root) if artifact.is_absolute() else artifact
        
        if artifact.is_file():
            file_hash = calculate_file_hash(artifact)
            artifact_records.append({
                "path": str(artifact_path),
                "type": "file",
                "hash": file_hash
            })
        elif artifact.is_dir():
            dir_hash = calculate_directory_hash(artifact)
            artifact_records.append({
                "path": str(artifact_path),
                "type": "directory",
                "hash": dir_hash
            })
    
    # Create phase entry
    phase_entry = {
        "phase_name": phase_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "artifacts": artifact_records
    }
    
    # Append to state
    state["phases"].append(phase_entry)
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    # Save updated state
    save_state_file(state_path, state)
    
    return state


def get_latest_phase_state(state_path: Optional[Path] = None, project_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Get the most recent phase entry from the state file.
    
    Args:
        state_path: Optional path to state file
        project_root: Optional project root
        
    Returns:
        Dictionary containing the latest phase entry, or None if no phases exist
    """
    if project_root is None:
        project_root = Path.cwd()
    
    if state_path is None:
        state_path = project_root / "state.yaml"
    
    if not state_path.exists():
        return None
    
    state = load_state_file(state_path)
    phases = state.get("phases", [])
    
    if not phases:
        return None
    
    return phases[-1]


def verify_artifact_integrity(
    artifacts: List[Path],
    state_path: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Verify that artifacts match their recorded hashes in the state file.
    
    Args:
        artifacts: List of file paths to verify
        state_path: Optional path to state file
        project_root: Optional project root
        
    Returns:
        Dictionary with verification results:
        - "valid": True if all artifacts match
        - "details": List of verification results per artifact
    """
    if project_root is None:
        project_root = Path.cwd()
    
    if state_path is None:
        state_path = project_root / "state.yaml"
    
    result = {
        "valid": True,
        "details": []
    }
    
    if not state_path.exists():
        result["valid"] = False
        result["details"].append({
            "status": "error",
            "message": "State file not found"
        })
        return result
    
    state = load_state_file(state_path)
    phases = state.get("phases", [])
    
    if not phases:
        result["valid"] = False
        result["details"].append({
            "status": "error",
            "message": "No phases recorded in state file"
        })
        return result
    
    # Get the most recent phase
    latest_phase = phases[-1]
    recorded_artifacts = {
        art["path"]: art for art in latest_phase.get("artifacts", [])
    }
    
    for artifact in artifacts:
        rel_path = str(artifact.relative_to(project_root)) if artifact.is_absolute() else str(artifact)
        
        if rel_path not in recorded_artifacts:
            result["details"].append({
                "path": rel_path,
                "status": "missing",
                "message": "Artifact not found in state record"
            })
            result["valid"] = False
            continue
        
        recorded = recorded_artifacts[rel_path]
        
        try:
            if artifact.is_file():
                current_hash = calculate_file_hash(artifact)
            elif artifact.is_dir():
                current_hash = calculate_directory_hash(artifact)
            else:
                result["details"].append({
                    "path": rel_path,
                    "status": "error",
                    "message": "Path does not exist"
                })
                result["valid"] = False
                continue
            
            if current_hash == recorded["hash"]:
                result["details"].append({
                    "path": rel_path,
                    "status": "valid",
                    "message": "Hash matches"
                })
            else:
                result["details"].append({
                    "path": rel_path,
                    "status": "invalid",
                    "message": f"Hash mismatch. Expected: {recorded['hash']}, Got: {current_hash}"
                })
                result["valid"] = False
        except Exception as e:
            result["details"].append({
                "path": rel_path,
                "status": "error",
                "message": str(e)
            })
            result["valid"] = False
    
    return result
