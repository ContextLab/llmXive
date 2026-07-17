"""
Versioning and state management for data artifacts.
Implements the Constitution Principle V: Write SHA-256 hashes of data artifacts.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from utils.config import get_project_root, get_path, ensure_dir, get_config

def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Computes the SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_artifact(file_path: Union[str, Path]) -> Dict[str, str]:
    """
    Generates a hash record for a single artifact.
    """
    p = get_path(file_path) if isinstance(file_path, str) else file_path
    return {
        "path": str(p),
        "sha256": compute_sha256(p),
        "size_bytes": p.stat().st_size
    }

def hash_directory(dir_path: Union[str, Path], pattern: str = "*") -> List[Dict[str, str]]:
    """
    Generates hash records for all files in a directory.
    """
    p = get_path(dir_path) if isinstance(dir_path, str) else dir_path
    records = []
    if p.exists():
        for file in p.rglob(pattern):
            if file.is_file():
                records.append(hash_artifact(file))
    return records

def verify_artifact(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verifies a file's hash against an expected value.
    """
    return compute_sha256(file_path) == expected_hash

def write_version_manifest(artifacts: List[Dict[str, str]], output_path: Union[str, Path]) -> None:
    """
    Writes a JSON manifest of artifact hashes.
    """
    p = get_path(output_path) if isinstance(output_path, str) else output_path
    ensure_dir(p.parent)
    with open(p, "w") as f:
        json.dump(artifacts, f, indent=2)

def write_project_state_yaml(project_id: str, artifacts: List[Dict[str, str]], output_path: Optional[Union[str, Path]] = None) -> None:
    """
    Writes the project state to a YAML file.
    Format:
    project_id: ...
    artifacts:
      - path: ...
        hash: ...
    """
    import yaml
    
    if output_path is None:
        # Default location based on project ID
        state_dir = get_path("state/projects")
        ensure_dir(state_dir)
        safe_id = project_id.replace("/", "-").replace("\\", "-")
        output_path = state_dir / f"{safe_id}.yaml"
    else:
        output_path = get_path(output_path) if isinstance(output_path, str) else output_path
        ensure_dir(output_path.parent)

    state = {
        "project_id": project_id,
        "artifacts": artifacts
    }
    
    with open(output_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
