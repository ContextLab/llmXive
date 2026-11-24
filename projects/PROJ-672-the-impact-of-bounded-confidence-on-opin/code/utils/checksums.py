"""
Utility module for generating and verifying SHA-256 checksums for data files.
Supports updating the project state manifest with new checksums.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 hash of a file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def sha256(file_path: Union[str, Path]) -> str:
    """Alias for calculate_sha256 to satisfy verification requirements."""
    return calculate_sha256(file_path)

def generate_checksums_for_directory(
    directory_path: Union[str, Path],
    recursive: bool = True,
    extensions: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for all files in a directory.
    """
    directory_path = Path(directory_path)
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory_path}")

    checksums = {}
    pattern = "**/*" if recursive else "*"

    for file_path in directory_path.glob(pattern):
        if file_path.is_file():
            if extensions is not None and file_path.suffix not in extensions:
                continue
            rel_path = file_path.relative_to(directory_path)
            try:
                checksums[str(rel_path)] = calculate_sha256(file_path)
            except (FileNotFoundError, IOError):
                continue
    return checksums

def update_project_state_manifest(
    project_state_path: Union[str, Path],
    data_directory: Union[str, Path],
    manifest_key: str = "data_checksums",
) -> Dict:
    """
    Update the project state YAML file with checksums for files in a data directory.
    """
    project_state_path = Path(project_state_path)
    data_directory = Path(data_directory)

    if not project_state_path.exists():
        raise FileNotFoundError(f"Project state file not found: {project_state_path}")
    if not data_directory.exists():
        raise FileNotFoundError(f"Data directory not found: {data_directory}")

    with open(project_state_path, "r") as f:
        state = yaml.safe_load(f) or {}

    checksums = generate_checksums_for_directory(data_directory, recursive=True)
    state[manifest_key] = checksums

    with open(project_state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    return state

def verify_checksums(
    manifest_path: Union[str, Path],
    base_directory: Optional[Union[str, Path]] = None,
) -> Dict[str, bool]:
    """
    Verify file checksums against a manifest.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    if base_directory is None:
        base_directory = manifest_path.parent
    else:
        base_directory = Path(base_directory)

    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)

    checksums = {}
    for key, value in manifest.items():
        if isinstance(value, dict):
            if all(isinstance(v, str) and len(v) == 64 for v in value.values()):
                checksums = value
                break

    if not checksums:
        raise ValueError("No checksum data found in manifest")

    results = {}
    for rel_path, expected_hash in checksums.items():
        full_path = base_directory / rel_path
        if full_path.exists():
            try:
                actual_hash = calculate_sha256(full_path)
                results[rel_path] = actual_hash == expected_hash
            except (FileNotFoundError, IOError):
                results[rel_path] = False
        else:
            results[rel_path] = False
    return results

def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m utils.checksums <generate|verify|update> ...")
        sys.exit(1)
    command = sys.argv[1]
    if command == "generate":
        print(json.dumps(generate_checksums_for_directory(sys.argv[2]), indent=2))
    elif command == "verify":
        results = verify_checksums(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        sys.exit(0 if all(results.values()) else 1)
    elif command == "update":
        update_project_state_manifest(sys.argv[2], sys.argv[3])
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
