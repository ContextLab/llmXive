import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from utils.config import get_project_root, get_path, ensure_dir, get_config

def compute_sha256(file_path: Union[str, Path]) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_artifact(file_path: Union[str, Path]) -> Dict[str, str]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    return {
        'path': str(path),
        'sha256': compute_sha256(path),
        'size_bytes': path.stat().st_size
    }

def hash_directory(dir_path: Union[str, Path]) -> Dict[str, Any]:
    path = Path(dir_path)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    artifacts = []
    for file in path.rglob('*'):
        if file.is_file():
            artifacts.append(hash_artifact(file))
    
    return {
        'directory': str(path),
        'artifacts': artifacts,
        'total_files': len(artifacts)
    }

def verify_artifact(file_path: Union[str, Path], expected_hash: str) -> bool:
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def write_version_manifest(artifacts: List[Dict], output_path: Optional[str] = None) -> None:
    if output_path is None:
        output_path = get_path("state/version_manifest.json")
    
    ensure_dir(output_path)
    with open(output_path, 'w') as f:
        json.dump(artifacts, f, indent=2)

def write_project_state_yaml(project_id: str, artifacts: List[Dict], output_path: Optional[str] = None) -> None:
    if output_path is None:
        output_path = get_path(f"state/projects/{project_id}.yaml")
    
    ensure_dir(output_path)
    
    # Simple YAML-like format
    with open(output_path, 'w') as f:
        f.write(f"project_id: {project_id}\n")
        f.write("artifacts:\n")
        for artifact in artifacts:
            f.write(f"  - path: {artifact['path']}\n")
            f.write(f"    sha256: {artifact['sha256']}\n")
            f.write(f"    size_bytes: {artifact['size_bytes']}\n")

def main():
    # Example usage
    test_file = get_path("README.md")
    if test_file.exists():
        info = hash_artifact(test_file)
        print(f"Hashed file: {info}")
    else:
        print("Test file not found")

if __name__ == "__main__":
    main()
