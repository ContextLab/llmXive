"""
State management for artifact hashing and integrity verification.
Implements Constitution Principle V: Artifact Hashing and State Tracking.

This module manages a YAML state file that tracks:
- File paths and their SHA-256 hashes
- Last modification times
- Artifact metadata (size, type, description)
- Verification status

Usage:
    python -m code.src.update_state hash <file_path>
    python -m code.src.update_state update <file_path>
    python -m code.src.update_state verify <file_path>
    python -m code.src.update_state verify-all
    python -m code.src.update_state status
"""

import hashlib
import yaml
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (relative to this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = PROJECT_ROOT / "artifacts" / "state.yaml"
CHECKSUMS_DIR = PROJECT_ROOT / "artifacts"

# Ensure artifacts directory exists
CHECKSUMS_DIR.mkdir(parents=True, exist_ok=True)


def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the hash of a file.

    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal hash string

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def load_state_yaml() -> Dict[str, Any]:
    """
    Load the state YAML file.

    Returns:
        State dictionary, or empty state if file doesn't exist
    """
    if not STATE_FILE.exists():
        logger.info(f"State file not found: {STATE_FILE}. Creating new state.")
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'artifacts': {}
        }

    try:
        with open(STATE_FILE, 'r') as f:
            state = yaml.safe_load(f)
            if state is None:
                state = {
                    'version': '1.0',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'artifacts': {}
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse state file: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        raise


def save_state_yaml(state: Dict[str, Any]) -> None:
    """
    Save the state to YAML file.

    Args:
        state: State dictionary to save
    """
    state['updated_at'] = datetime.now().isoformat()

    try:
        with open(STATE_FILE, 'w') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {STATE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")
        raise


def update_state_yaml(file_path: Path, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Update the state with a new or modified artifact.

    Args:
        file_path: Path to the artifact file
        description: Optional description of the artifact

    Returns:
        Updated state dictionary
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")

    state = load_state_yaml()

    # Calculate relative path from project root
    try:
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
    except ValueError:
        relative_path = str(file_path)

    # Calculate hash
    file_hash = calculate_file_hash(file_path)

    # Get file stats
    stat = file_path.stat()

    # Update state
    state['artifacts'][relative_path] = {
        'hash': file_hash,
        'size': stat.st_size,
        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'description': description or f"Auto-tracked: {relative_path}",
        'last_verified': None,
        'verification_status': 'pending'
    }

    save_state_yaml(state)
    logger.info(f"Updated state for: {relative_path}")

    return state


def verify_artifact_integrity(file_path: Path) -> Tuple[bool, str]:
    """
    Verify the integrity of a single artifact against the stored hash.

    Args:
        file_path: Path to the artifact to verify

    Returns:
        Tuple of (is_valid, message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    state = load_state_yaml()

    try:
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
    except ValueError:
        relative_path = str(file_path)

    if relative_path not in state['artifacts']:
        return False, f"Artifact not tracked in state: {relative_path}"

    stored_hash = state['artifacts'][relative_path]['hash']
    current_hash = calculate_file_hash(file_path)

    if stored_hash != current_hash:
        return False, f"Hash mismatch for {relative_path}\n  Expected: {stored_hash}\n  Actual:   {current_hash}"

    # Update verification status
    state['artifacts'][relative_path]['last_verified'] = datetime.now().isoformat()
    state['artifacts'][relative_path]['verification_status'] = 'valid'
    save_state_yaml(state)

    return True, f"Artifact verified: {relative_path}"


def verify_all_artifacts() -> Dict[str, Tuple[bool, str]]:
    """
    Verify all tracked artifacts.

    Returns:
        Dictionary mapping relative paths to (is_valid, message) tuples
    """
    state = load_state_yaml()
    results = {}

    if not state['artifacts']:
        logger.warning("No artifacts tracked in state file.")
        return results

    for relative_path, artifact_info in state['artifacts'].items():
        file_path = PROJECT_ROOT / relative_path
        is_valid, message = verify_artifact_integrity(file_path)
        results[relative_path] = (is_valid, message)

    # Summary
    valid_count = sum(1 for is_valid, _ in results.values() if is_valid)
    total_count = len(results)

    logger.info(f"Verification complete: {valid_count}/{total_count} artifacts valid")

    return results


def get_artifact_status() -> Dict[str, Any]:
    """
    Get the current status of all tracked artifacts.

    Returns:
        Dictionary with status information
    """
    state = load_state_yaml()

    status = {
        'state_file': str(STATE_FILE),
        'total_artifacts': len(state['artifacts']),
        'created_at': state.get('created_at'),
        'updated_at': state.get('updated_at'),
        'artifacts': {}
    }

    for relative_path, artifact_info in state['artifacts'].items():
        file_path = PROJECT_ROOT / relative_path
        exists = file_path.exists()

        status['artifacts'][relative_path] = {
            'exists': exists,
            'size': artifact_info.get('size'),
            'hash': artifact_info.get('hash'),
            'description': artifact_info.get('description'),
            'last_verified': artifact_info.get('last_verified'),
            'verification_status': artifact_info.get('verification_status', 'unknown')
        }

        if exists:
            try:
                current_hash = calculate_file_hash(file_path)
                stored_hash = artifact_info.get('hash')
                status['artifacts'][relative_path]['hash_match'] = (current_hash == stored_hash)
            except Exception as e:
                status['artifacts'][relative_path]['hash_match'] = False
                status['artifacts'][relative_path]['error'] = str(e)
        else:
            status['artifacts'][relative_path]['hash_match'] = False
            status['artifacts'][relative_path]['error'] = 'File not found'

    return status


def main():
    """
    Command-line interface for state management.

    Usage:
        python -m code.src.update_state <command> [arguments]

    Commands:
        hash <file_path>          - Calculate and print hash of a file
        update <file_path>        - Add/update artifact in state
        verify <file_path>        - Verify a single artifact
        verify-all                - Verify all tracked artifacts
        status                    - Show status of all artifacts
    """
    if len(sys.argv) < 2:
        print("Usage: python -m code.src.update_state <command> [arguments]")
        print("\nCommands:")
        print("  hash <file_path>          - Calculate and print hash of a file")
        print("  update <file_path>        - Add/update artifact in state")
        print("  verify <file_path>        - Verify a single artifact")
        print("  verify-all                - Verify all tracked artifacts")
        print("  status                    - Show status of all artifacts")
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        if command == 'hash':
            if len(sys.argv) < 3:
                print("Error: hash command requires a file path")
                sys.exit(1)
            file_path = Path(sys.argv[2])
            file_hash = calculate_file_hash(file_path)
            print(f"SHA-256: {file_hash}")

        elif command == 'update':
            if len(sys.argv) < 3:
                print("Error: update command requires a file path")
                sys.exit(1)
            file_path = Path(sys.argv[2])
            description = sys.argv[3] if len(sys.argv) > 3 else None
            update_state_yaml(file_path, description)
            print(f"State updated for: {file_path}")

        elif command == 'verify':
            if len(sys.argv) < 3:
                print("Error: verify command requires a file path")
                sys.exit(1)
            file_path = Path(sys.argv[2])
            is_valid, message = verify_artifact_integrity(file_path)
            print(message)
            sys.exit(0 if is_valid else 1)

        elif command == 'verify-all':
            results = verify_all_artifacts()
            if not results:
                print("No artifacts to verify.")
                sys.exit(0)

            all_valid = True
            for path, (is_valid, message) in results.items():
                status = "✓" if is_valid else "✗"
                print(f"{status} {path}: {message}")
                if not is_valid:
                    all_valid = False

            sys.exit(0 if all_valid else 1)

        elif command == 'status':
            status = get_artifact_status()
            print(f"State file: {status['state_file']}")
            print(f"Total artifacts: {status['total_artifacts']}")
            print(f"Created: {status['created_at']}")
            print(f"Updated: {status['updated_at']}")
            print("\nArtifacts:")

            for path, info in status['artifacts'].items():
                exists_str = "✓" if info['exists'] else "✗"
                match_str = "✓" if info.get('hash_match') else "✗"
                print(f"\n  {path}")
                print(f"    Exists: {exists_str}")
                print(f"    Size: {info.get('size', 'N/A')} bytes")
                print(f"    Hash match: {match_str}")
                print(f"    Description: {info.get('description', 'N/A')}")
                print(f"    Last verified: {info.get('last_verified', 'Never')}")
                print(f"    Status: {info.get('verification_status', 'unknown')}")
                if info.get('error'):
                    print(f"    Error: {info['error']}")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Unexpected error occurred")
        sys.exit(1)


if __name__ == '__main__':
    main()