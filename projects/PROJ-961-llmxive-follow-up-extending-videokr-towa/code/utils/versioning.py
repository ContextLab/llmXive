"""
Versioning module for writing SHA-256 hashes of data artifacts.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from utils.config import get_project_root, get_path, ensure_dir, get_config

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_artifact(file_path: Path) -> Dict[str, Any]:
    """Hash a single artifact and return metadata."""
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")

    return {
        "path": str(file_path),
        "sha256": compute_sha256(file_path),
        "size_bytes": file_path.stat().st_size
    }

def hash_directory(dir_path: Path) -> List[Dict[str, Any]]:
    """Hash all files in a directory recursively."""
    artifacts = []
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            artifacts.append(hash_artifact(file_path))
    return artifacts

def verify_artifact(file_path: Path, expected_hash: str) -> bool:
    """Verify an artifact against an expected hash."""
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def write_version_manifest(artifacts: List[Dict[str, Any]], output_path: Path):
    """Write a version manifest JSON file."""
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(artifacts, f, indent=2)

def write_project_state_yaml(project_id: str, artifacts: List[Dict[str, Any]], output_path: Path):
    """Write project state to a YAML file (simplified as JSON for compatibility)."""
    ensure_dir(output_path.parent)
    state = {
        "project_id": project_id,
        "artifacts": artifacts
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

def main():
    """Main entry point for versioning tests."""
    project_root = get_project_root()
    processed_dir = get_path(project_root, "processed_data")

    # Test hashing
    if processed_dir.exists():
        artifacts = hash_directory(processed_dir)
        print(f"Hashed {len(artifacts)} artifacts")

        # Write manifest
        manifest_path = processed_dir / "version_manifest.json"
        write_version_manifest(artifacts, manifest_path)
        print(f"Manifest written to {manifest_path}")
    else:
        print(f"Processed directory not found: {processed_dir}")

if __name__ == "__main__":
    main()