import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging_utils import log_warning
from utils.validators import compute_sha256
from data_model import Dataset, FairnessMetric

def log_header(message: str) -> None:
    """Log a formatted header message to stdout."""
    print(f"\n{'='*60}")
    print(f" {message}")
    print(f"{'='*60}\n")

def load_processed_datasets() -> Dict[str, Path]:
    """
    Load the list of processed dataset files from the data/processed directory.
    
    Returns:
        Dict mapping dataset_id to Path object.
    """
    processed_dir = PROJECT_ROOT / "data" / "processed"
    if not processed_dir.exists():
        log_warning(f"Processed directory does not exist: {processed_dir}")
        return {}
    
    datasets = {}
    for file_path in processed_dir.glob("*.csv"):
        # Expect filename format: {dataset_id}_processed.csv
        dataset_id = file_path.stem.replace("_processed", "")
        datasets[dataset_id] = file_path
    
    return datasets

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load the project state YAML file.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        Dictionary containing state data.
    """
    if not state_path.exists():
        return {
            "project_id": "PROJ-099-statistical-analysis-of-algorithmic-fair",
            "artifact_hashes": {}
        }
    
    with open(state_path, "r") as f:
        return yaml.safe_load(f) or {"artifact_hashes": {}}

def save_state_file(state_path: Path, state: Dict[str, Any]) -> None:
    """
    Save the project state to a YAML file.
    
    Args:
        state_path: Path to the state YAML file.
        state: Dictionary containing state data.
    """
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def store_processed_datasets() -> None:
    """
    Main workflow to store preprocessed datasets and update checksums in state.
    
    This function:
    1. Loads all processed datasets from data/processed/
    2. Computes SHA-256 checksums for each file
    3. Updates the project state YAML file with the new checksums
    4. Logs the operation results
    """
    log_header("STORING PROCESSED DATASETS AND UPDATING CHECKSUMS")
    
    # Define paths
    state_file_path = PROJECT_ROOT / "state" / "projects" / "PROJ-099-statistical-analysis-of-algorithmic-fair.yaml"
    processed_datasets = load_processed_datasets()
    
    if not processed_datasets:
        log_warning("No processed datasets found to store.")
        return
    
    # Load current state
    state = load_state_file(state_file_path)
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    # Update checksums for each processed dataset
    updated_count = 0
    for dataset_id, file_path in processed_datasets.items():
        checksum = compute_file_checksum(file_path)
        state["artifact_hashes"][f"processed_{dataset_id}"] = {
            "file": str(file_path.relative_to(PROJECT_ROOT)),
            "sha256": checksum,
            "size_bytes": file_path.stat().st_size
        }
        updated_count += 1
        print(f"Stored checksum for {dataset_id}: {checksum[:16]}...")
    
    # Save updated state
    save_state_file(state_file_path, state)
    
    print(f"\nSuccessfully updated checksums for {updated_count} processed datasets.")
    print(f"State file updated at: {state_file_path}")

def main():
    """Entry point for the script."""
    store_processed_datasets()

if __name__ == "__main__":
    main()
