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

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
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


def generate_checksums_for_directory(
    directory_path: Union[str, Path],
    recursive: bool = True,
    extensions: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for all files in a directory.

    Args:
        directory_path: Path to the directory to scan.
        recursive: If True, scan subdirectories recursively.
        extensions: Optional list of file extensions to include (e.g., ['.json', '.csv']).
                   If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    directory_path = Path(directory_path)
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory_path}")

    checksums = {}
    pattern = "**/*" if recursive else "*"

    for file_path in directory_path.glob(pattern):
        if file_path.is_file():
            # Filter by extension if specified
            if extensions is not None:
                if file_path.suffix not in extensions:
                    continue

            # Calculate relative path from the directory
            rel_path = file_path.relative_to(directory_path)
            try:
                checksums[str(rel_path)] = calculate_sha256(file_path)
            except (FileNotFoundError, IOError):
                # Skip files that cannot be read
                continue

    return checksums


def update_project_state_manifest(
    project_state_path: Union[str, Path],
    data_directory: Union[str, Path],
    manifest_key: str = "data_checksums",
) -> Dict:
    """
    Update the project state YAML file with checksums for files in a data directory.

    Args:
        project_state_path: Path to the project state YAML file.
        data_directory: Path to the data directory to checksum.
        manifest_key: Key under which to store the checksums in the manifest.

    Returns:
        The updated project state dictionary.
    """
    project_state_path = Path(project_state_path)
    data_directory = Path(data_directory)

    if not project_state_path.exists():
        raise FileNotFoundError(f"Project state file not found: {project_state_path}")

    if not data_directory.exists():
        raise FileNotFoundError(f"Data directory not found: {data_directory}")

    # Load existing state
    with open(project_state_path, "r") as f:
        state = yaml.safe_load(f) or {}

    # Generate checksums
    checksums = generate_checksums_for_directory(data_directory, recursive=True)

    # Update state
    state[manifest_key] = checksums

    # Write back
    with open(project_state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    return state


def verify_checksums(
    manifest_path: Union[str, Path],
    base_directory: Optional[Union[str, Path]] = None,
) -> Dict[str, bool]:
    """
    Verify file checksums against a manifest.

    Args:
        manifest_path: Path to the YAML file containing checksums.
        base_directory: Base directory for relative paths in the manifest.
                       If None, assumes paths are relative to the manifest's directory.

    Returns:
        Dictionary mapping file paths to verification status (True/False).
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

    # Assume checksums are under 'data_checksums' or similar key
    # Try to find the key that contains file paths
    checksums = {}
    for key, value in manifest.items():
        if isinstance(value, dict):
            # Heuristic: if values look like hex strings, assume it's a checksum dict
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
    """
    CLI entry point for checksum operations.
    Usage:
        python -m utils.checksums generate <directory>
        python -m utils.checksums verify <manifest_file> [base_directory]
        python -m utils.checksums update <project_state_file> <data_directory>
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python -m utils.checksums generate <directory>")
        print("  python -m utils.checksums verify <manifest_file> [base_directory]")
        print("  python -m utils.checksums update <project_state_file> <data_directory>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "generate":
        directory = sys.argv[2]
        checksums = generate_checksums_for_directory(directory)
        print(json.dumps(checksums, indent=2))

    elif command == "verify":
        manifest_file = sys.argv[2]
        base_dir = sys.argv[3] if len(sys.argv) > 3 else None
        results = verify_checksums(manifest_file, base_dir)
        all_valid = all(results.values())
        for path, valid in results.items():
            status = "OK" if valid else "FAILED"
            print(f"{status}: {path}")
        sys.exit(0 if all_valid else 1)

    elif command == "update":
        state_file = sys.argv[2]
        data_dir = sys.argv[3]
        updated_state = update_project_state_manifest(state_file, data_dir)
        print(f"Updated manifest at {state_file}")
        print(f"Checksums updated for {len(updated_state.get('data_checksums', {}))} files")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
