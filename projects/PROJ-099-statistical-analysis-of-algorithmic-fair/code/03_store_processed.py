"""
Store Processed Data Module for PROJ-099.
Computes checksums for processed files and updates the project state YAML.
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import time

# Add parent to path for imports if running as script
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from utils.validators import compute_sha256
from utils.logging_utils import log_warning

# FR-008 Disclaimer Constant
FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(message: str):
    """
    Logs a formatted header message to stdout and stderr with the FR-008 disclaimer.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    output = f"[{timestamp}] {message}\n{FR008_DISCLAIMER}"
    print(output)
    sys.stderr.write(output + "\n")

def load_processed_datasets(processed_dir: Path) -> Dict[str, Path]:
    """
    Loads list of processed dataset files.
    """
    datasets = {}
    if not processed_dir.exists():
        log_warning(f"Processed directory {processed_dir} does not exist.")
        return datasets
    
    for file in processed_dir.glob("*.csv"):
        # Extract dataset_id from filename (e.g., adult_processed.csv -> adult)
        name = file.stem.replace("_processed", "")
        datasets[name] = file
    return datasets

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes SHA-256 checksum of a file.
    """
    return compute_sha256(file_path)

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Loads the project state YAML.
    """
    if not state_path.exists():
        return {"project_id": "PROJ-099", "artifact_hashes": {}}
    
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def save_state_file(state_path: Path, state: Dict[str, Any]):
    """
    Saves the project state YAML.
    """
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def store_processed_datasets(processed_dir: Path, state_path: Path):
    """
    Computes checksums for all processed datasets and updates state file.
    """
    log_header("Storing processed datasets and computing checksums")
    
    datasets = load_processed_datasets(processed_dir)
    if not datasets:
        log_warning("No processed datasets found to store.")
        return

    state = load_state_file(state_path)
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}

    for ds_id, file_path in datasets.items():
        checksum = compute_file_checksum(file_path)
        log_header(f"Dataset {ds_id}: SHA-256 = {checksum}")
        state["artifact_hashes"][f"{ds_id}_processed"] = checksum

    save_state_file(state_path, state)
    log_header(f"State file updated at {state_path}")

def main():
    """
    Main entry point for storing processed data.
    """
    log_header("=== Starting Store Processed Data Pipeline ===")
    log_header(FR008_DISCLAIMER)
    
    processed_dir = Path("data/processed")
    state_path = Path("state/projects/PROJ-099-statistical-analysis-of-algorithmic-fair.yaml")
    
    store_processed_datasets(processed_dir, state_path)
    
    log_header("=== Store Processed Data Pipeline Complete ===")
    log_header(FR008_DISCLAIMER)

if __name__ == "__main__":
    main()
