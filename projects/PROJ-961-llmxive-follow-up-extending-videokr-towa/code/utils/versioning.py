"""Versioning and artifact hashing utilities."""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from utils.config import get_project_root, get_path, ensure_dir, get_config

def compute_sha256(file_path: Union[str, Path]) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_artifact(path: Union[str, Path]) -> Dict[str, str]:
    """Hash a single artifact and return metadata."""
    path = Path(path)
    return {
        "path": str(path),
        "sha256": compute_sha256(path),
        "size": path.stat().st_size
    }

def hash_directory(dir_path: Union[str, Path]) -> List[Dict[str, str]]:
    """Hash all files in a directory recursively."""
    dir_path = Path(dir_path)
    artifacts = []
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            artifacts.append(hash_artifact(file_path))
    return artifacts

def verify_artifact(path: Union[str, Path], expected_hash: str) -> bool:
    """Verify that a file matches an expected hash."""
    actual_hash = compute_sha256(path)
    return actual_hash == expected_hash

def write_version_manifest(artifacts: List[Dict[str, str]], output_path: Union[str, Path]) -> None:
    """Write a version manifest file."""
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    with open(output_path, "w") as f:
        json.dump(artifacts, f, indent=2)

def write_project_state_yaml(project_id: str, artifacts: List[Dict[str, str]], output_path: Optional[Union[str, Path]] = None) -> None:
    """Write a project state YAML file."""
    if output_path is None:
        output_path = get_path(f"state/projects/{project_id}.yaml")
    else:
        output_path = Path(output_path)

    ensure_dir(output_path.parent)

    with open(output_path, "w") as f:
        f.write(f"project_id: {project_id}\n")
        f.write("artifacts:\n")
        for artifact in artifacts:
            f.write(f"  - path: {artifact['path']}\n")
            f.write(f"    sha256: {artifact['sha256']}\n")
            f.write(f"    size: {artifact['size']}\n")
