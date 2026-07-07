"""
State management utilities for llmXive pipeline.

Computes and stores artifact hashes to ensure reproducibility.
"""
import hashlib
import json
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config import get_config, get_path


def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
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
        raise IOError(f"Could not read file {file_path}: {e}")


def calculate_directory_hash(directory_path: Union[str, Path]) -> Dict[str, str]:
    """
    Calculate SHA-256 hashes for all files in a directory recursively.
    
    Args:
        directory_path: Path to the directory to hash.
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    directory_path = Path(directory_path)
    if not directory_path.exists() or not directory_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    hashes = {}
    for file_path in directory_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(directory_path)
            hashes[str(rel_path)] = calculate_sha256(file_path)
    
    return hashes


def load_saved_hashes(state_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load previously saved artifact hashes from the state file.
    
    Args:
        state_file: Path to the state YAML file. Defaults to 
                    'state/artifact_hashes.yaml'.
                    
    Returns:
        Dictionary of saved hashes, or empty dict if file doesn't exist.
    """
    if state_file is None:
        state_file = get_path("state", "artifact_hashes.yaml")
    
    if not state_file.exists():
        return {}
    
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Could not parse state file {state_file}: {e}")


def save_hashes(hashes: Dict[str, Any], state_file: Optional[Path] = None) -> None:
    """
    Save artifact hashes to the state file.
    
    Args:
        hashes: Dictionary of hashes to save.
        state_file: Path to the state YAML file. Defaults to 
                    'state/artifact_hashes.yaml'.
    """
    if state_file is None:
        state_file = get_path("state", "artifact_hashes.yaml")
    
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(hashes, f, default_flow_style=False, sort_keys=False)


def compute_artifact_hashes(artifact_paths: List[Union[str, Path]]) -> Dict[str, Any]:
    """
    Compute hashes for a list of artifact paths (files or directories).
    
    Args:
        artifact_paths: List of paths to artifacts (files or directories).
                        
    Returns:
        Dictionary mapping artifact path strings to their hashes.
        For directories, the value is a nested dict of file hashes.
    """
    results = {}
    for path in artifact_paths:
        path = Path(path)
        if not path.exists():
            results[str(path)] = None
            continue
        
        if path.is_file():
            results[str(path)] = calculate_sha256(path)
        elif path.is_dir():
            results[str(path)] = calculate_directory_hash(path)
        else:
            results[str(path)] = None
    
    return results


def store_artifact_hashes(
    artifact_paths: List[Union[str, Path]],
    state_file: Optional[Path] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Compute hashes for artifacts and store them in the state file.
    
    This function is typically called after data completion or 
    pipeline steps to ensure reproducibility.
    
    Args:
        artifact_paths: List of paths to artifacts (files or directories)
                        to hash and store.
        state_file: Path to the state YAML file. Defaults to 
                    'state/artifact_hashes.yaml'.
        metadata: Optional metadata to include in the state file 
                  (e.g., timestamp, pipeline version).
    """
    config = get_config()
    hashes = compute_artifact_hashes(artifact_paths)
    
    state_data = {
        "artifacts": hashes,
        "metadata": metadata or {}
    }
    
    # Add pipeline version if available
    if "version" in config:
        state_data["metadata"]["pipeline_version"] = config["version"]
    
    save_hashes(state_data, state_file)


def verify_artifact_integrity(
    artifact_paths: List[Union[str, Path]],
    state_file: Optional[Path] = None
) -> bool:
    """
    Verify that current artifact hashes match stored hashes.
    
    Args:
        artifact_paths: List of paths to artifacts to verify.
        state_file: Path to the state YAML file. Defaults to 
                    'state/artifact_hashes.yaml'.
                    
    Returns:
        True if all artifacts match their stored hashes, False otherwise.
    """
    stored_data = load_saved_hashes(state_file)
    if not stored_data or "artifacts" not in stored_data:
        return False
    
    current_hashes = compute_artifact_hashes(artifact_paths)
    stored_hashes = stored_data.get("artifacts", {})
    
    for path_str, current_hash in current_hashes.items():
        stored_hash = stored_hashes.get(path_str)
        
        # If artifact doesn't exist now but was stored, fail
        if current_hash is None and stored_hash is not None:
            return False
        
        # If artifact exists now but wasn't stored, fail
        if current_hash is not None and stored_hash is None:
            return False
        
        # Compare hashes
        if current_hash != stored_hash:
            return False
    
    return True


def main():
    """
    CLI entry point for state_utils.
    
    Usage:
        python code/state_utils.py compute <path1> [path2 ...]
        python code/state_utils.py verify <path1> [path2 ...]
    """
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python code/state_utils.py <command> <path1> [path2 ...]")
        print("Commands: compute, verify")
        sys.exit(1)
    
    command = sys.argv[1]
    paths = [Path(p) for p in sys.argv[2:]]
    
    if command == "compute":
        hashes = compute_artifact_hashes(paths)
        print(yaml.dump(hashes, default_flow_style=False))
    elif command == "verify":
        is_valid = verify_artifact_integrity(paths)
        print(f"Integrity check: {'PASSED' if is_valid else 'FAILED'}")
        sys.exit(0 if is_valid else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
