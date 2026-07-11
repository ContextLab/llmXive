import os
import hashlib
import yaml
from typing import Dict, Any, List, Optional
from data_loader import download_beir_dataset
from config import get_config

STATE_DIR = "state/projects"
STATE_FILE_NAME = "PROJ-873-llmxive-follow-up-extending-active-learn.yaml"

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for checksum calculation: {file_path}")

def ensure_state_file(state_path: str) -> Dict[str, Any]:
    """Ensure the state directory and file exist, loading existing content or creating new."""
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def load_state(state_path: str) -> Dict[str, Any]:
    """Load the state YAML file."""
    return ensure_state_file(state_path)

def save_state(state_path: str, data: Dict[str, Any]) -> None:
    """Save the state data to the YAML file."""
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Main entry point for T005a:
    1. Fetches BEIR datasets (nfcorpus, scifact) via data_loader.
    2. Calculates SHA-256 checksums of the raw downloaded files.
    3. Records them in state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml under artifact_hashes.
    """
    config = get_config()
    state_path = os.path.join(STATE_DIR, STATE_FILE_NAME)
    
    # Ensure state file structure
    state_data = load_state(state_path)
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    # Datasets to process
    datasets = ["nfcorpus", "scifact"]
    downloaded_files: List[str] = []

    print(f"Starting T005a: Calculating checksums for BEIR datasets: {datasets}")

    for dataset_name in datasets:
        try:
            # Download the dataset using the existing data_loader function
            # This function handles fetching and caching in the local cache directory
            local_path = download_beir_dataset(dataset_name)
            
            if local_path and os.path.exists(local_path):
                checksum = calculate_sha256(local_path)
                print(f"Calculated checksum for {dataset_name} ({local_path}): {checksum}")
                
                # Record in state
                state_data["artifact_hashes"][dataset_name] = {
                    "path": local_path,
                    "sha256": checksum
                }
                downloaded_files.append(local_path)
            else:
                print(f"Warning: Downloaded path for {dataset_name} does not exist: {local_path}")
        except Exception as e:
            print(f"Error processing {dataset_name}: {e}")

    # Save the updated state
    save_state(state_path, state_data)
    print(f"State saved to {state_path}")
    print(f"Recorded checksums for {len(downloaded_files)} files.")

if __name__ == "__main__":
    main()
