import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from utils.config import get_project_root, get_path, ensure_dir, get_config

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_artifact(file_path: Path) -> str:
    """
    Hash an artifact file.
    
    Args:
        file_path: Path to the artifact.
        
    Returns:
        Hex digest of the hash.
    """
    return compute_sha256(file_path)

def hash_directory(directory: Path) -> Dict[str, str]:
    """
    Hash all files in a directory.
    
    Args:
        directory: Path to the directory.
        
    Returns:
        Dictionary of file paths to hashes.
    """
    hashes = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(directory)
            hashes[str(rel_path)] = compute_sha256(file_path)
    return hashes

def verify_artifact(file_path: Path, expected_hash: str) -> bool:
    """
    Verify an artifact's hash.
    
    Args:
        file_path: Path to the artifact.
        expected_hash: Expected hash string.
        
    Returns:
        True if hash matches.
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def write_version_manifest(manifest_path: Path, artifacts: Dict[str, str]) -> None:
    """
    Write a version manifest file.
    
    Args:
        manifest_path: Path to the manifest file.
        artifacts: Dictionary of artifact paths to hashes.
    """
    ensure_dir(manifest_path.parent)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(artifacts, f, indent=2)

def write_project_state_yaml(
    state_path: Path, 
    project_id: str, 
    task_id: str, 
    artifact_path: Path
) -> None:
    """
    Write a project state YAML file.
    
    Args:
        state_path: Path to the state file.
        project_id: Project identifier.
        task_id: Task identifier.
        artifact_path: Path to the artifact.
    """
    ensure_dir(state_path.parent)
    
    if artifact_path.exists():
        artifact_hash = compute_sha256(artifact_path)
    else:
        artifact_hash = "missing"
        
    yaml_content = f"""project_id: {project_id}
task_id: {task_id}
artifact_path: {str(artifact_path)}
artifact_hash: {artifact_hash}
"""
    with open(state_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)