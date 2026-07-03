"""
update_state.py

Manages the project's state.yaml file and artifact hashing.
Implements Constitution Principle V: Reproducibility via artifact checksums.

This module provides utilities to:
1. Calculate SHA-256 hashes for files.
2. Update the `state.yaml` file with current artifact hashes and timestamps.
3. Verify the integrity of previously recorded artifacts.
"""

import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Import path constants from config
try:
    from config import PROJECT_ROOT, STATE_FILE
except ImportError:
    # Fallback for standalone execution or if config is not yet fully linked
    # This block ensures the script can be run directly for testing
    _project_root = Path(__file__).resolve().parent.parent
    PROJECT_ROOT = _project_root
    STATE_FILE = PROJECT_ROOT / "state.yaml"


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except PermissionError as e:
        raise PermissionError(f"Permission denied reading file: {file_path}") from e


def load_state() -> Dict[str, Any]:
    """
    Load the current state from state.yaml.
    If the file does not exist, returns an empty state structure.

    Returns:
        Dictionary containing the current state.
    """
    if not STATE_FILE.exists():
        return {
            "project": "PROJ-152-evaluating-the-impact-of-code-generation",
            "version": "1.0.0",
            "last_updated": None,
            "artifacts": {}
        }

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "project": "PROJ-152-evaluating-the-impact-of-code-generation",
                    "version": "1.0.0",
                    "last_updated": None,
                    "artifacts": {}
                }
            return state
    except yaml.YAMLError as e:
        print(f"Error parsing state.yaml: {e}", file=sys.stderr)
        return {
            "project": "PROJ-152-evaluating-the-impact-of-code-generation",
            "version": "1.0.0",
            "last_updated": None,
            "artifacts": {}
        }


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to state.yaml.

    Args:
        state: The state dictionary to save.
    """
    # Ensure parent directory exists
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def update_artifact_state(
    artifact_path: Path,
    relative_to: Optional[Path] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate hash for a single artifact and update the state.

    Args:
        artifact_path: Absolute path to the artifact.
        relative_to: Base path for the relative key in state.yaml (defaults to PROJECT_ROOT).
        description: Optional description of the artifact.

    Returns:
        The updated artifact entry dictionary.
    """
    if relative_to is None:
        relative_to = PROJECT_ROOT

    if not artifact_path.is_absolute():
        artifact_path = PROJECT_ROOT / artifact_path

    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found during state update: {artifact_path}")

    file_hash = calculate_file_hash(artifact_path)
    relative_path = str(artifact_path.relative_to(relative_to))

    state = load_state()
    state["artifacts"][relative_path] = {
        "hash": file_hash,
        "size_bytes": artifact_path.stat().st_size,
        "description": description or "Auto-tracked artifact",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    return state["artifacts"][relative_path]


def update_state_for_directory(
    directory_path: Path,
    extensions: Optional[List[str]] = None,
    relative_to: Optional[Path] = None
) -> int:
    """
    Recursively hash all files in a directory and update state.

    Args:
        directory_path: Path to the directory to scan.
        extensions: List of file extensions to include (e.g., ['.py', '.csv']). 
                    If None, all files are included.
        relative_to: Base path for relative keys.

    Returns:
        Number of files processed.
    """
    if relative_to is None:
        relative_to = PROJECT_ROOT

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    count = 0
    for file_path in directory_path.rglob("*"):
        if file_path.is_file():
            if extensions is None or file_path.suffix in extensions:
                try:
                    update_artifact_state(file_path, relative_to)
                    count += 1
                except (FileNotFoundError, PermissionError) as e:
                    print(f"Skipping {file_path}: {e}", file=sys.stderr)
    return count


def verify_artifacts() -> bool:
    """
    Verify that all artifacts recorded in state.yaml match their current hashes.

    Returns:
        True if all artifacts match, False otherwise.
    """
    state = load_state()
    all_valid = True

    for relative_path, metadata in state.get("artifacts", {}).items():
        full_path = PROJECT_ROOT / relative_path
        if not full_path.exists():
            print(f"MISSING: {relative_path}", file=sys.stderr)
            all_valid = False
            continue

        current_hash = calculate_file_hash(full_path)
        if current_hash != metadata.get("hash"):
            print(f"MISMATCH: {relative_path} (Expected: {metadata.get('hash')}, Got: {current_hash})", file=sys.stderr)
            all_valid = False
        else:
            print(f"OK: {relative_path}")

    return all_valid


def main():
    """
    CLI entry point for state management.
    Usage:
      python code/update_state.py update [path]  -> Update state for specific path or all code/data
      python code/update_state.py verify         -> Verify all recorded artifacts
      python code/update_state.py show           -> Display current state
    """
    if len(sys.argv) < 2:
        print("Usage: python code/update_state.py <command> [args]")
        print("Commands: update, verify, show")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "update":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        if target:
            target_path = PROJECT_ROOT / target
            if target_path.is_file():
                update_artifact_state(target_path)
                print(f"Updated state for: {target}")
            elif target_path.is_dir():
                count = update_state_for_directory(target_path)
                print(f"Updated state for {count} files in: {target}")
            else:
                print(f"Path not found: {target}")
                sys.exit(1)
        else:
            # Default: update code, data, and figures directories if they exist
            dirs_to_scan = ["code", "data", "figures"]
            total = 0
            for d in dirs_to_scan:
                p = PROJECT_ROOT / d
                if p.exists():
                    count = update_state_for_directory(p)
                    total += count
            print(f"Updated state for {total} files in default directories.")

    elif command == "verify":
        if verify_artifacts():
            print("All artifacts verified successfully.")
        else:
            print("Verification failed. Check logs above.")
            sys.exit(1)

    elif command == "show":
        state = load_state()
        print(yaml.dump(state, default_flow_style=False))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()