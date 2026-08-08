import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure utils are importable relative to code/
sys.path.insert(0, str(Path(__file__).parent))

from utils.validators import compute_sha256
from utils.logging_utils import log_warning

# FR-008 Disclaimer Constant
FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(file_path: Path, operation: str) -> None:
    """
    Log a header for the operation with the FR-008 disclaimer.
    """
    print(f"\n{'='*60}")
    print(f"OPERATION: {operation}")
    print(f"FILE: {file_path}")
    print(f"NOTE: {FR008_DISCLAIMER}")
    print(f"{'='*60}\n")

def load_processed_datasets(proc_dir: Path) -> Dict[str, Path]:
    """
    Loads list of processed datasets from the directory.
    """
    datasets = {}
    if not proc_dir.exists():
        return datasets
    
    for f in proc_dir.glob("*.csv"):
        name = f.stem.replace("_processed", "")
        datasets[name] = f
    return datasets

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes SHA-256 checksum of a file.
    """
    return compute_sha256(file_path)

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Loads the project state YAML file.
    """
    if not state_path.exists():
        return {"artifact_hashes": {}}
    
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def save_state_file(state_path: Path, state: Dict[str, Any]) -> None:
    """
    Saves the project state YAML file.
    """
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def store_processed_datasets(proc_dir: Path, state_path: Path) -> None:
    """
    Computes checksums for all processed datasets and updates state file.
    """
    log_header(state_path, "Storing Processed Datasets & Checksums")
    
    datasets = load_processed_datasets(proc_dir)
    if not datasets:
        print("No processed datasets found.")
        return

    state = load_state_file(state_path)
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}

    updated = False
    for name, path in datasets.items():
        checksum = compute_file_checksum(path)
        if name not in state["artifact_hashes"] or state["artifact_hashes"][name] != checksum:
            state["artifact_hashes"][name] = checksum
            updated = True
            print(f"Updated checksum for {name}: {checksum[:16]}...")

    if updated:
        save_state_file(state_path, state)
        print(f"State file updated: {state_path}")
    else:
        print("No changes in checksums. State file not updated.")

    print(f"\nNOTE: {FR008_DISCLAIMER}")

def main():
    """
    Main entry point for storing processed datasets.
    """
    proc_dir = Path("data/processed")
    state_path = Path("state/projects/PROJ-099-statistical-analysis-of-algorithmic-fair.yaml")
    
    store_processed_datasets(proc_dir, state_path)

if __name__ == "__main__":
    main()