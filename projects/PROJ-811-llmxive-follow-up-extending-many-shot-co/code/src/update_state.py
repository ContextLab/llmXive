"""
update_state.py - Constitution Principle V Implementation

This module handles artifact hashing and state YAML updates to ensure
data integrity and reproducibility throughout the research pipeline.

Constitution Principle V: All artifacts must be versioned and checksummed.
"""

import hashlib
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default state file name
DEFAULT_STATE_FILE = "artifacts/state.yaml"

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the cryptographic hash of a file.

    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal string representation of the file hash

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)

    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise

def load_state_yaml(state_file: Path) -> Dict[str, Any]:
    """
    Load the state YAML file, creating it if it doesn't exist.

    Args:
        state_file: Path to the state YAML file

    Returns:
        Dictionary containing the state data
    """
    if not isinstance(state_file, Path):
        state_file = Path(state_file)

    if not state_file.exists():
        # Ensure directory exists
        state_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created new state file: {state_file}")
        return {
            "version": "1.0",
            "artifacts": {},
            "last_updated": None
        }

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = yaml.safe_load(f)
            if state is None:
                state = {
                    "version": "1.0",
                    "artifacts": {},
                    "last_updated": None
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {state_file}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading state file {state_file}: {e}")
        raise

def save_state_yaml(state: Dict[str, Any], state_file: Path) -> None:
    """
    Save the state dictionary to a YAML file.

    Args:
        state: Dictionary containing the state data
        state_file: Path to the state YAML file
    """
    if not isinstance(state_file, Path):
        state_file = Path(state_file)

    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved state to {state_file}")
    except Exception as e:
        logger.error(f"Error writing state file {state_file}: {e}")
        raise

def update_state_yaml(
    artifact_path: Path,
    state_file: Optional[Path] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the state YAML with a new artifact entry.

    This function:
    1. Calculates the hash of the artifact
    2. Loads the current state
    3. Updates the artifact entry with hash and metadata
    4. Saves the updated state

    Args:
        artifact_path: Path to the artifact file
        state_file: Optional path to the state YAML (defaults to DEFAULT_STATE_FILE)
        metadata: Optional dictionary of additional metadata to store

    Returns:
        Updated state dictionary
    """
    if not isinstance(artifact_path, Path):
        artifact_path = Path(artifact_path)

    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    if state_file is None:
        state_file = Path(DEFAULT_STATE_FILE)

    # Calculate hash
    file_hash = calculate_file_hash(artifact_path)

    # Load current state
    state = load_state_yaml(state_file)

    # Prepare artifact entry
    artifact_key = str(artifact_path.relative_to(Path.cwd()))
    artifact_entry = {
        "path": str(artifact_path),
        "hash": file_hash,
        "algorithm": "sha256",
        "size_bytes": artifact_path.stat().st_size,
        "metadata": metadata or {}
    }

    # Update state
    state["artifacts"][artifact_key] = artifact_entry
    state["last_updated"] = artifact_path.stat().st_mtime

    # Save state
    save_state_yaml(state, state_file)

    logger.info(f"Updated state for artifact: {artifact_key}")
    return state

def verify_artifact_integrity(
    artifact_path: Path,
    state_file: Optional[Path] = None,
    strict: bool = True
) -> bool:
    """
    Verify the integrity of an artifact against the stored state.

    Args:
        artifact_path: Path to the artifact file to verify
        state_file: Optional path to the state YAML (defaults to DEFAULT_STATE_FILE)
        strict: If True, raise exceptions on missing state or artifact.
               If False, return False on errors.

    Returns:
        True if the artifact hash matches the stored hash, False otherwise
    """
    if not isinstance(artifact_path, Path):
        artifact_path = Path(artifact_path)

    if state_file is None:
        state_file = Path(DEFAULT_STATE_FILE)

    try:
        # Check if state file exists
        if not state_file.exists():
            if strict:
                raise FileNotFoundError(f"State file not found: {state_file}")
            logger.warning(f"State file not found: {state_file}")
            return False

        # Check if artifact exists
        if not artifact_path.exists():
            if strict:
                raise FileNotFoundError(f"Artifact not found: {artifact_path}")
            logger.warning(f"Artifact not found: {artifact_path}")
            return False

        # Load state
        state = load_state_yaml(state_file)

        # Get artifact key
        try:
            artifact_key = str(artifact_path.relative_to(Path.cwd()))
        except ValueError:
            # If relative path fails, use absolute path string
            artifact_key = str(artifact_path)

        # Check if artifact is in state
        if artifact_key not in state.get("artifacts", {}):
            if strict:
                raise KeyError(f"Artifact not found in state: {artifact_key}")
            logger.warning(f"Artifact not found in state: {artifact_key}")
            return False

        # Get stored hash
        stored_entry = state["artifacts"][artifact_key]
        stored_hash = stored_entry.get("hash")

        if not stored_hash:
            if strict:
                raise ValueError(f"Stored hash missing for artifact: {artifact_key}")
            logger.warning(f"Stored hash missing for artifact: {artifact_key}")
            return False

        # Calculate current hash
        current_hash = calculate_file_hash(artifact_path)

        # Compare hashes
        if current_hash == stored_hash:
            logger.info(f"Artifact integrity verified: {artifact_key}")
            return True
        else:
            logger.error(f"Artifact integrity check FAILED for {artifact_key}")
            logger.error(f"  Stored hash:   {stored_hash}")
            logger.error(f"  Current hash:  {current_hash}")
            if strict:
                raise ValueError(f"Hash mismatch for artifact: {artifact_key}")
            return False

    except Exception as e:
        logger.error(f"Error verifying artifact integrity: {e}")
        if strict:
            raise
        return False

def verify_all_artifacts(state_file: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verify the integrity of all artifacts listed in the state file.

    Args:
        state_file: Optional path to the state YAML

    Returns:
        Dictionary mapping artifact paths to verification status (True/False)
    """
    if state_file is None:
        state_file = Path(DEFAULT_STATE_FILE)

    results = {}

    if not state_file.exists():
        logger.warning(f"State file not found: {state_file}")
        return results

    state = load_state_yaml(state_file)

    for artifact_key, entry in state.get("artifacts", {}).items():
        artifact_path = Path(entry.get("path", artifact_key))
        try:
            results[artifact_key] = verify_artifact_integrity(
                artifact_path, state_file, strict=False
            )
        except Exception as e:
            logger.error(f"Error verifying {artifact_key}: {e}")
            results[artifact_key] = False

    return results

def main():
    """
    Command-line interface for the update_state module.

    Usage:
        python -m code.src.update_state <command> [arguments]

    Commands:
        hash <file>          Calculate hash of a file
        update <file>        Update state with a file
        verify <file>        Verify a file's integrity
        verify-all           Verify all files in state
        status               Show current state summary
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m code.src.update_state <command> [arguments]")
        print("Commands: hash, update, verify, verify-all, status")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "hash":
        if len(sys.argv) < 3:
            print("Usage: python -m code.src.update_state hash <file>")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        try:
            file_hash = calculate_file_hash(file_path)
            print(f"Hash for {file_path}: {file_hash}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "update":
        if len(sys.argv) < 3:
            print("Usage: python -m code.src.update_state update <file>")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        try:
            state = update_state_yaml(file_path)
            print(f"State updated for {file_path}")
            print(f"Hash: {state['artifacts'][str(file_path.relative_to(Path.cwd()))]['hash']}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "verify":
        if len(sys.argv) < 3:
            print("Usage: python -m code.src.update_state verify <file>")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        try:
            is_valid = verify_artifact_integrity(file_path)
            status = "VALID" if is_valid else "INVALID"
            print(f"Artifact {file_path}: {status}")
            sys.exit(0 if is_valid else 1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "verify-all":
        try:
            results = verify_all_artifacts()
            valid_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            print(f"Verified {valid_count}/{total_count} artifacts")
            for path, is_valid in results.items():
                status = "OK" if is_valid else "FAIL"
                print(f"  [{status}] {path}")
            sys.exit(0 if valid_count == total_count else 1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "status":
        try:
            state_file = Path(DEFAULT_STATE_FILE)
            if not state_file.exists():
                print("No state file found.")
                sys.exit(0)

            state = load_state_yaml(state_file)
            artifact_count = len(state.get("artifacts", {}))
            last_updated = state.get("last_updated", "Never")

            print(f"State file: {state_file}")
            print(f"Artifacts: {artifact_count}")
            print(f"Last updated: {last_updated}")

            for key, entry in state.get("artifacts", {}).items():
                print(f"  - {key}: {entry.get('hash', 'N/A')[:16]}...")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print("Commands: hash, update, verify, verify-all, status")
        sys.exit(1)

if __name__ == "__main__":
    main()
