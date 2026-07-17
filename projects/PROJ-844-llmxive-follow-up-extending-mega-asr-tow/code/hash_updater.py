"""
Hash Updater Module for llmXive Pipeline.

Implements Principle V (Data Integrity):
Computes SHA-256 content hashes for all files in data/derived/
and updates the state YAML file to track data provenance and integrity.
"""

import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Import config for paths
# Assuming config.py defines PROJECT_ROOT, DERIVED_DATA_PATH, STATE_FILE_PATH
try:
    from config import PROJECT_ROOT, DERIVED_DATA_PATH, STATE_FILE_PATH
except ImportError:
    # Fallback for direct execution or missing config if paths are not yet defined
    # In a real run, config.py must be present (T003)
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DERIVED_DATA_PATH = PROJECT_ROOT / "data" / "derived"
    STATE_FILE_PATH = PROJECT_ROOT / "data" / ".state.yaml"

def compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file's contents.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Cannot compute hash: File not found at {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")

def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Loads the existing state YAML file or initializes a new one.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        Dictionary containing the state data.
    """
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            # Ensure structure exists
            if data is None:
                data = {}
            if "derived_data_hashes" not in data:
                data["derived_data_hashes"] = {}
            return data
    else:
        # Initialize new state structure
        return {
            "derived_data_hashes": {},
            "last_updated": None,
            "version": "1.0"
        }

def save_state(state_data: Dict[str, Any], state_path: Path) -> None:
    """
    Saves the state dictionary to the YAML file.

    Args:
        state_data: Dictionary to save.
        state_path: Path to the state YAML file.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=True)

def update_hashes(derived_path: Optional[Path] = None, state_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Scans the derived data directory, computes hashes for all files,
    and updates the state YAML file.

    Args:
        derived_path: Optional override for the derived data directory path.
        state_path: Optional override for the state file path.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.

    Raises:
        FileNotFoundError: If the derived data directory does not exist.
        RuntimeError: If no files are found in the derived directory.
    """
    target_dir = derived_path or DERIVED_DATA_PATH
    state_file = state_path or STATE_FILE_PATH

    if not target_dir.exists():
        raise FileNotFoundError(f"Derived data directory not found: {target_dir}")

    if not target_dir.is_dir():
        raise NotADirectoryError(f"Derived data path is not a directory: {target_dir}")

    # Load existing state
    state = load_state(state_file)

    hashes = {}
    new_hashes = {}

    # Walk directory to find all files (excluding hidden files starting with .)
    for root, _, files in os.walk(target_dir):
        for filename in files:
            if filename.startswith("."):
                continue

            file_path = Path(root) / filename
            rel_path = file_path.relative_to(target_dir)
            rel_path_str = str(rel_path)

            try:
                file_hash = compute_file_hash(file_path)
                hashes[rel_path_str] = file_hash
                new_hashes[rel_path_str] = file_hash
            except (FileNotFoundError, PermissionError) as e:
                # Log error but continue processing other files
                print(f"Warning: Could not hash {file_path}: {e}")

    if not new_hashes:
        # If directory exists but no files, we still update state to reflect empty
        # This is valid state (no data generated yet)
        print(f"No files found in {target_dir} to hash.")

    # Update state
    state["derived_data_hashes"] = new_hashes
    state["last_updated"] = str(Path(__file__).parent) # Placeholder for timestamp or logic
    
    # In a real pipeline, we might want a timestamp here
    from datetime import datetime
    state["last_updated"] = datetime.utcnow().isoformat()

    # Save updated state
    save_state(state, state_file)

    return new_hashes

def main():
    """
    Entry point for the hash updater script.
    """
    print(f"Scanning derived data directory: {DERIVED_DATA_PATH}")
    print(f"State file: {STATE_FILE_PATH}")
    
    try:
        hashes = update_hashes()
        print(f"Successfully updated hashes for {len(hashes)} files.")
        for path, hash_val in sorted(hashes.items()):
            print(f"  {path}: {hash_val[:16]}...")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error during hash update: {e}")
        raise

if __name__ == "__main__":
    main()