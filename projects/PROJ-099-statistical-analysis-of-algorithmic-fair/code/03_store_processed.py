import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.logging_utils import log_warning

PROJECT_ID = "PROJ-099-statistical-analysis-of-algorithmic-fair"
STATE_FILE_PATH = f"state/projects/{PROJECT_ID}.yaml"
PROCESSED_DIR = Path("data/processed")

def log_header():
    """Prints a standardized header to stdout."""
    print("=" * 60)
    print(f"Script: {os.path.basename(__file__)}")
    print(f"Started at: {__import__('datetime').datetime.now().isoformat()}")
    print("=" * 60)

def log_disclaimer():
    """Prints the FR-008 disclaimer."""
    print("\n" + "!" * 60)
    print("DISCLAIMER (FR-008): Findings are associational only; no causal claims are made.")
    print("!" * 60 + "\n")

def load_processed_datasets() -> Dict[str, Path]:
    """
    Scans the data/processed directory and returns a dictionary of dataset_id -> file_path.
    Expects files named like 'dataset_id_processed.csv'.
    """
    if not PROCESSED_DIR.exists():
        log_warning(f"Processed directory {PROCESSED_DIR} does not exist yet.")
        return {}
    
    datasets = {}
    for file_path in PROCESSED_DIR.glob("*_processed.csv"):
        # Extract dataset_id from filename (e.g., 'adult_processed.csv' -> 'adult')
        dataset_id = file_path.stem.replace("_processed", "")
        datasets[dataset_id] = file_path
    return datasets

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        log_warning(f"Error computing checksum for {file_path}: {e}")
        return None

def load_state_file() -> Dict[str, Any]:
    """
    Loads the project state YAML file.
    If it doesn't exist, returns an empty structure.
    """
    state_path = Path(STATE_FILE_PATH)
    if state_path.exists():
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_state_file(state: Dict[str, Any]):
    """
    Saves the project state to the YAML file.
    """
    state_path = Path(STATE_FILE_PATH)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def store_processed_datasets():
    """
    Computes SHA-256 checksums for all processed datasets and records them
    in the project state YAML file under 'processed_checksums'.
    This distinguishes them from raw checksums recorded in T014.
    """
    log_header()
    log_disclaimer()

    datasets = load_processed_datasets()
    if not datasets:
        print("No processed datasets found in data/processed/. Skipping checksum recording.")
        return

    state = load_state_file()
    if 'processed_checksums' not in state:
        state['processed_checksums'] = {}

    print(f"Found {len(datasets)} processed dataset(s). Recording checksums...")
    
    updated = False
    for dataset_id, file_path in datasets.items():
        checksum = compute_file_checksum(file_path)
        if checksum:
            old_checksum = state['processed_checksums'].get(dataset_id)
            state['processed_checksums'][dataset_id] = {
                "file_path": str(file_path),
                "checksum": checksum,
                "recorded_at": __import__('datetime').datetime.now().isoformat()
            }
            if old_checksum != checksum:
                updated = True
                print(f"  - {dataset_id}: Checksum recorded/updated ({checksum[:16]}...)")
            else:
                print(f"  - {dataset_id}: Checksum matches existing record.")
        else:
            print(f"  - {dataset_id}: FAILED to compute checksum.")

    if updated:
        save_state_file(state)
        print(f"\nState file updated at: {STATE_FILE_PATH}")
    else:
        print("\nNo changes to state file.")

def main():
    """
    Entry point for the script.
    """
    store_processed_datasets()

if __name__ == "__main__":
    main()