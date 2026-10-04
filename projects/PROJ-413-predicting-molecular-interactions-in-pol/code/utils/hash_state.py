import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Constants
STATE_FILE_PATH = Path("state/projects/PROJ-413-predicting-molecular-interactions-in-pol.yaml")
DATA_DIR = Path("data")
RESULTS_DIR = Path("results")
CODE_DIR = Path("code")

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def hash_directory(dir_path: Path, extensions: Optional[list] = None) -> Dict[str, str]:
    """
    Compute SHA256 hashes for all files in a directory (recursive).

    Args:
        dir_path: Path to the directory.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.pt']).
                   If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    hashes = {}
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            if extensions is None or file_path.suffix in extensions:
                try:
                    rel_path = file_path.relative_to(dir_path)
                    hashes[str(rel_path)] = compute_sha256(file_path)
                except ValueError:
                    # Skip files that are not relative to dir_path
                    continue
    return hashes

def update_state_yaml(artifact_hashes: Dict[str, str], state_file: Optional[Path] = None) -> None:
    """
    Update the project state YAML file with new artifact hashes.

    Args:
        artifact_hashes: Dictionary mapping artifact keys to their SHA256 hashes.
        state_file: Optional path to the state file. Defaults to STATE_FILE_PATH.
    """
    if state_file is None:
        state_file = STATE_FILE_PATH

    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state or create new
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    # Update artifact_hashes section
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}

    state['artifact_hashes'].update(artifact_hashes)

    # Write back to file
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def verify_artifacts(artifact_paths: Dict[str, Path], state_file: Optional[Path] = None) -> bool:
    """
    Verify that the current SHA256 hashes of artifacts match those stored in the state file.

    Args:
        artifact_paths: Dictionary mapping artifact keys to their file paths.
        state_file: Optional path to the state file. Defaults to STATE_FILE_PATH.

    Returns:
        True if all artifacts match their stored hashes, False otherwise.

    Raises:
        FileNotFoundError: If the state file or any artifact file is missing.
    """
    if state_file is None:
        state_file = STATE_FILE_PATH

    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")

    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)

    if 'artifact_hashes' not in state:
        raise ValueError("No artifact_hashes found in state file")

    all_match = True
    for key, path in artifact_paths.items():
        if not path.exists():
            print(f"Artifact missing: {path} (key: {key})")
            all_match = False
            continue

        current_hash = compute_sha256(path)
        stored_hash = state['artifact_hashes'].get(key)

        if stored_hash is None:
            print(f"No stored hash for artifact: {key}")
            all_match = False
        elif current_hash != stored_hash:
            print(f"Hash mismatch for {key}: expected {stored_hash}, got {current_hash}")
            all_match = False
        else:
            print(f"Hash verified for {key}: {current_hash}")

    return all_match

def get_state_hash(state_file: Optional[Path] = None) -> Optional[str]:
    """
    Compute a SHA256 hash of the entire state file content.

    Args:
        state_file: Optional path to the state file. Defaults to STATE_FILE_PATH.

    Returns:
        Hexadecimal string of the SHA256 hash of the state file, or None if file doesn't exist.
    """
    if state_file is None:
        state_file = STATE_FILE_PATH

    if not state_file.exists():
        return None

    return compute_sha256(state_file)

def main():
    """
    Main function to demonstrate hash state utilities.
    This script can be run to verify artifacts or update the state file.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Utility for checksumming and state hashing.")
    parser.add_argument("--action", choices=["verify", "update", "hash_dir"], required=True,
                        help="Action to perform: verify artifacts, update state, or hash directory.")
    parser.add_argument("--artifacts", nargs="+", help="Space-separated list of 'key:path' pairs for update/verify.")
    parser.add_argument("--dir", type=str, help="Directory to hash (for hash_dir action).")
    parser.add_argument("--extensions", nargs="+", help="File extensions to include (for hash_dir action).")
    parser.add_argument("--state", type=str, help="Path to state file (optional).")

    args = parser.parse_args()
    state_file = Path(args.state) if args.state else STATE_FILE_PATH

    if args.action == "verify":
        if not args.artifacts:
            print("Error: --artifacts required for verify action")
            return 1
        artifact_paths = {}
        for item in args.artifacts:
            if ':' not in item:
                print(f"Error: Invalid artifact format '{item}'. Expected 'key:path'")
                return 1
            key, path = item.split(':', 1)
            artifact_paths[key] = Path(path)
        try:
            if verify_artifacts(artifact_paths, state_file):
                print("All artifacts verified successfully.")
                return 0
            else:
                print("Verification failed.")
                return 1
        except Exception as e:
            print(f"Verification error: {e}")
            return 1

    elif args.action == "update":
        if not args.artifacts:
            print("Error: --artifacts required for update action")
            return 1
        artifact_hashes = {}
        for item in args.artifacts:
            if ':' not in item:
                print(f"Error: Invalid artifact format '{item}'. Expected 'key:path'")
                return 1
            key, path = item.split(':', 1)
            path_obj = Path(path)
            if not path_obj.exists():
                print(f"Error: Artifact not found: {path}")
                return 1
            try:
                artifact_hashes[key] = compute_sha256(path_obj)
            except Exception as e:
                print(f"Error computing hash for {path}: {e}")
                return 1
        try:
            update_state_yaml(artifact_hashes, state_file)
            print(f"State file updated successfully at {state_file}")
            return 0
        except Exception as e:
            print(f"Update error: {e}")
            return 1

    elif args.action == "hash_dir":
        if not args.dir:
            print("Error: --dir required for hash_dir action")
            return 1
        dir_path = Path(args.dir)
        extensions = args.extensions if args.extensions else None
        try:
            hashes = hash_directory(dir_path, extensions)
            print(json.dumps(hashes, indent=2))
            return 0
        except Exception as e:
            print(f"Hash directory error: {e}")
            return 1

    return 1

if __name__ == "__main__":
    exit(main())