"""
Data Hygiene Module for llmXive Project.

Computes SHA-256 hashes for all files in `data/raw/*`, `data/derived/*`,
and `data/results/*` (Phase 6 inclusion) and updates the project state
YAML file with the computed checksums.

This module ensures data integrity by verifying that artifacts have not
been modified since their creation or download.
"""
import os
import hashlib
import yaml
import json
from pathlib import Path
from datetime import datetime

# Project Root (assumed to be the parent of 'code')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE_NAME = "PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml"

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOError(f"Failed to read file {file_path} for hashing: {e}")

def scan_directory_for_hashes(directory: Path, relative_base: Path) -> dict:
    """
    Recursively scans a directory and computes SHA-256 hashes for all files.

    Args:
        directory: The directory to scan.
        relative_base: The base path to strip from file paths for relative keys.

    Returns:
        A dictionary mapping relative file paths to their SHA-256 hashes.
    """
    hashes = {}
    if not directory.exists():
        print(f"Warning: Directory {directory} does not exist. Skipping.")
        return hashes

    for root, _, files in os.walk(directory):
        for file in files:
            full_path = Path(root) / file
            # Calculate relative path from the data root (e.g., data/raw/...)
            try:
                rel_path = full_path.relative_to(relative_base)
            except ValueError:
                # Should not happen if relative_base is correct, but safe fallback
                rel_path = full_path.relative_to(directory)
            
            hash_value = compute_sha256(full_path)
            hashes[str(rel_path)] = hash_value

    return hashes

def load_state_yaml(state_file: Path) -> dict:
    """
    Loads the existing state YAML file if it exists, otherwise returns a new structure.

    Args:
        state_file: Path to the state YAML file.

    Returns:
        Dictionary representing the state.
    """
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise RuntimeError(f"Failed to parse existing state file {state_file}: {e}")
    else:
        # Initialize a new state structure
        return {
            "project_id": "PROJ-893-llmxive-follow-up-extending-s-agent-spat",
            "last_updated": None,
            "data_hygiene": {
                "raw": {},
                "derived": {},
                "results": {}
            }
        }

def save_state_yaml(state_file: Path, state: dict) -> None:
    """
    Saves the state dictionary to the YAML file.

    Args:
        state_file: Path to the state YAML file.
        state: The state dictionary to save.
    """
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def main():
    """
    Main execution function for data hygiene checks (Phase 6).
    Includes data/results in the scan.
    """
    print(f"Starting Data Hygiene Check for project: {PROJECT_ROOT}")
    
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / STATE_FILE_NAME

    # Load existing state
    state = load_state_yaml(state_file)

    # Update timestamp
    state["last_updated"] = datetime.now().isoformat()

    # Initialize data_hygiene section if missing
    if "data_hygiene" not in state:
        state["data_hygiene"] = {"raw": {}, "derived": {}, "results": {}}

    # Scan data/raw
    print(f"Scanning {DATA_RAW_DIR}...")
    raw_hashes = scan_directory_for_hashes(DATA_RAW_DIR, DATA_RAW_DIR)
    state["data_hygiene"]["raw"] = raw_hashes
    print(f"  Found {len(raw_hashes)} files in raw data.")

    # Scan data/derived
    print(f"Scanning {DATA_DERIVED_DIR}...")
    derived_hashes = scan_directory_for_hashes(DATA_DERIVED_DIR, DATA_DERIVED_DIR)
    state["data_hygiene"]["derived"] = derived_hashes
    print(f"  Found {len(derived_hashes)} files in derived data.")

    # Scan data/results (Phase 6 addition)
    print(f"Scanning {DATA_RESULTS_DIR}...")
    results_hashes = scan_directory_for_hashes(DATA_RESULTS_DIR, DATA_RESULTS_DIR)
    state["data_hygiene"]["results"] = results_hashes
    print(f"  Found {len(results_hashes)} files in results data.")

    # Save updated state
    save_state_yaml(state_file, state)
    print(f"State updated successfully at {state_file}")

    # Summary
    print("\n--- Hygiene Summary ---")
    print(f"Raw files hashed: {len(raw_hashes)}")
    print(f"Derived files hashed: {len(derived_hashes)}")
    print(f"Results files hashed: {len(results_hashes)}")
    total = len(raw_hashes) + len(derived_hashes) + len(results_hashes)
    print(f"Total files processed: {total}")
    
    if total == 0:
        print("Warning: No data files found in 'data/raw', 'data/derived', or 'data/results'.")
        print("Ensure data has been downloaded or generated before running hygiene checks.")

if __name__ == "__main__":
    main()