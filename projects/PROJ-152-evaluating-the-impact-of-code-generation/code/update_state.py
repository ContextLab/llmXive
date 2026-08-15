"""
update_state.py - Manages state.yaml and artifact hashing per Constitution Principle V.

This module provides utilities to track the state of project artifacts,
compute their hashes, and maintain a persistent state file.
"""

import hashlib
import os
import sys
import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import config

# Constants
STATE_FILE_PATH = Path(config.PROJECT_ROOT) / "state.yaml"
EXCLUDE_PATTERNS = {
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".git",
    ".pytest_cache",
    "*.log",
    "venv",
    ".venv",
    "node_modules",
}


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file's contents.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def calculate_directory_hash(dir_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate a deterministic hash for a directory's contents.

    The hash is computed by sorting all files by relative path and
    concatenating their individual hashes.

    Args:
        dir_path: Path to the directory to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal hash string representing the directory state.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    hasher = hashlib.new(algorithm)
    files = []

    for root, dirs, filenames in os.walk(dir_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_PATTERNS]

        for filename in filenames:
            # Skip excluded file patterns
            if any(filename.endswith(ext) for ext in EXCLUDE_PATTERNS):
                continue

            file_path = Path(root) / filename
            if file_path.is_file():
                files.append((str(file_path.relative_to(dir_path)), file_path))

    # Sort by relative path for determinism
    files.sort(key=lambda x: x[0])

    for rel_path, file_path in files:
        # Include relative path in the hash
        hasher.update(rel_path.encode("utf-8"))
        hasher.update(b":")
        try:
            file_hash = calculate_file_hash(file_path, algorithm)
            hasher.update(file_hash.encode("utf-8"))
            hasher.update(b"\n")
        except (FileNotFoundError, IOError) as e:
            # Log but continue with other files
            print(f"Warning: Could not hash {file_path}: {e}", file=sys.stderr)

    return hasher.hexdigest()


def load_state() -> Dict[str, Any]:
    """
    Load the current state from state.yaml.

    Returns:
        Dictionary containing the state data, or an empty dict if file doesn't exist.
    """
    if not STATE_FILE_PATH.exists():
        return {
            "version": "1.0",
            "updated_at": None,
            "artifacts": {},
            "directories": {},
        }

    try:
        with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            return state if state else {}
    except yaml.YAMLError as e:
        print(f"Error parsing state.yaml: {e}", file=sys.stderr)
        return {}


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to state.yaml.

    Args:
        state: The state dictionary to save.
    """
    # Ensure state has required structure
    if "version" not in state:
        state["version"] = "1.0"
    if "updated_at" not in state:
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
    if "artifacts" not in state:
        state["artifacts"] = {}
    if "directories" not in state:
        state["directories"] = {}

    # Update timestamp
    state["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Write to file with proper formatting
    with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=True, allow_unicode=True)


def update_artifact_state(
    artifact_path: Path, state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the state entry for a specific artifact file.

    Args:
        artifact_path: Path to the artifact file.
        state: Optional existing state dict (if None, loads from disk).

    Returns:
        Updated state dictionary.
    """
    if state is None:
        state = load_state()

    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    relative_path = str(artifact_path.relative_to(config.PROJECT_ROOT))
    file_hash = calculate_file_hash(artifact_path)

    state["artifacts"][relative_path] = {
        "hash": file_hash,
        "size_bytes": artifact_path.stat().st_size,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    return state


def update_state_for_directory(
    dir_path: Path, state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the state entry for a directory's contents.

    Args:
        dir_path: Path to the directory.
        state: Optional existing state dict (if None, loads from disk).

    Returns:
        Updated state dictionary.
    """
    if state is None:
        state = load_state()

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    relative_path = str(dir_path.relative_to(config.PROJECT_ROOT))
    dir_hash = calculate_directory_hash(dir_path)

    # Count files
    file_count = sum(
        1
        for _ in dir_path.rglob("*")
        if _.is_file()
        and _.parts[-1] not in EXCLUDE_PATTERNS
        and not any(_.parts[-1].endswith(ext) for ext in EXCLUDE_PATTERNS)
    )

    state["directories"][relative_path] = {
        "hash": dir_hash,
        "file_count": file_count,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    return state


def verify_artifacts(
    artifacts: Optional[List[str]] = None, state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Verify that tracked artifacts match their recorded hashes.

    Args:
        artifacts: Optional list of artifact paths to verify (relative to project root).
                   If None, verifies all tracked artifacts.
        state: Optional existing state dict (if None, loads from disk).

    Returns:
        Dictionary with verification results:
        {
            "verified": List of successfully verified paths,
            "failed": List of paths with hash mismatches or missing files,
            "missing": List of paths recorded in state but not on disk,
            "unchanged": List of paths matching their recorded hash
        }
    """
    if state is None:
        state = load_state()

    tracked = state.get("artifacts", {})

    if artifacts is None:
        artifacts_to_verify = list(tracked.keys())
    else:
        artifacts_to_verify = artifacts

    results = {
        "verified": [],
        "failed": [],
        "missing": [],
        "unchanged": [],
    }

    for artifact_path_str in artifacts_to_verify:
        artifact_path = config.PROJECT_ROOT / artifact_path_str

        if not artifact_path.exists():
            results["missing"].append(artifact_path_str)
            results["failed"].append(artifact_path_str)
            continue

        try:
            current_hash = calculate_file_hash(artifact_path)
            recorded_hash = tracked.get(artifact_path_str, {}).get("hash")

            if recorded_hash is None:
                # Not tracked or missing hash entry
                results["failed"].append(artifact_path_str)
            elif current_hash == recorded_hash:
                results["verified"].append(artifact_path_str)
                results["unchanged"].append(artifact_path_str)
            else:
                results["failed"].append(artifact_path_str)
        except Exception as e:
            print(f"Error verifying {artifact_path_str}: {e}", file=sys.stderr)
            results["failed"].append(artifact_path_str)

    return results


def main() -> int:
    """
    CLI entry point for state management operations.

    Usage:
        python code/update_state.py [command] [args...]

    Commands:
        init              - Initialize state.yaml with current artifacts
        update [path]     - Update state for specific artifact or directory
        verify [paths...] - Verify artifacts against recorded hashes
        status            - Show current state summary

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if len(sys.argv) < 2:
        print("Usage: python code/update_state.py <command> [args...]")
        print("Commands: init, update, verify, status")
        return 1

    command = sys.argv[1].lower()

    try:
        if command == "init":
            state = {"artifacts": {}, "directories": {}}
            # Scan code/, data/, tests/
            for scan_dir in ["code", "data", "tests"]:
                dir_path = config.PROJECT_ROOT / scan_dir
                if dir_path.exists():
                    state = update_state_for_directory(dir_path, state)
            save_state(state)
            print(f"Initialized state.yaml with {len(state['artifacts'])} artifacts")

        elif command == "update":
            if len(sys.argv) < 3:
                print("Error: update requires a path argument")
                return 1

            target_path = config.PROJECT_ROOT / sys.argv[2]
            state = load_state()

            if target_path.is_file():
                state = update_artifact_state(target_path, state)
                print(f"Updated artifact: {target_path}")
            elif target_path.is_dir():
                state = update_state_for_directory(target_path, state)
                print(f"Updated directory: {target_path}")
            else:
                print(f"Error: Path not found: {target_path}")
                return 1

            save_state(state)

        elif command == "verify":
            state = load_state()
            artifacts = sys.argv[2:] if len(sys.argv) > 2 else None
            results = verify_artifacts(artifacts, state)

            print(f"Verification Results:")
            print(f"  Verified: {len(results['verified'])}")
            print(f"  Unchanged: {len(results['unchanged'])}")
            print(f"  Failed: {len(results['failed'])}")
            print(f"  Missing: {len(results['missing'])}")

            if results["failed"]:
                print("\nFailed artifacts:")
                for path in results["failed"]:
                    print(f"  - {path}")

            if results["missing"]:
                print("\nMissing artifacts:")
                for path in results["missing"]:
                    print(f"  - {path}")

            return 0 if not results["failed"] and not results["missing"] else 1

        elif command == "status":
            state = load_state()
            print(f"State File: {STATE_FILE_PATH}")
            print(f"Version: {state.get('version', 'unknown')}")
            print(f"Updated At: {state.get('updated_at', 'never')}")
            print(f"Tracked Artifacts: {len(state.get('artifacts', {}))}")
            print(f"Tracked Directories: {len(state.get('directories', {}))}")

            # Show recent changes
            artifacts = state.get("artifacts", {})
            if artifacts:
                print("\nRecent artifacts:")
                for path, info in list(artifacts.items())[:5]:
                    print(f"  - {path} ({info.get('size_bytes', 0)} bytes)")

        else:
            print(f"Unknown command: {command}")
            print("Commands: init, update, verify, status")
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
