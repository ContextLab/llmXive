import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Optional
import time
import yaml
import requests

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.validators import compute_sha256, verify_checksum
from utils.logging_utils import log_warning
from utils.dataset_loaders import get_dataset_info, load_adult, load_compas, load_bank, load_german, load_lawschool

# Constants
RAW_DATA_DIR = project_root / "data" / "raw"
STATE_FILE = project_root / "state" / "projects" / "PROJ-099-statistical-analysis-of-algorithmic-fair.yaml"
FR_008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(message: str):
    """Print a formatted header to stdout."""
    print(f"\n{'='*60}")
    print(f" {message}")
    print(f"{'='*60}\n")

def log_disclaimer():
    """Print the FR-008 disclaimer."""
    print(f"\n[DISCLAIMER] {FR_008_DISCLAIMER}\n")

def get_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state_file(state_path: Path) -> Dict:
    """Load the project state YAML file."""
    if not state_path.exists():
        # Initialize with empty structure if not exists
        return {
            "project_id": "PROJ-099-statistical-analysis-of-algorithmic-fair",
            "artifact_hashes": {}
        }
    
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def save_state_file(state_path: Path, state: Dict):
    """Save the project state to YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)

def download_and_verify_dataset(dataset_name: str, info: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Download a dataset, verify its checksum, and record it in state.
    
    Returns:
        Tuple[success, file_path, checksum]
    """
    log_header(f"Processing Dataset: {dataset_name}")
    
    # Ensure raw data directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    output_file = RAW_DATA_DIR / f"{dataset_name}.csv"
    
    # If file already exists, verify it first
    if output_file.exists():
        print(f"File already exists: {output_file}")
        current_checksum = get_file_checksum(output_file)
        expected_checksum = info.get('checksum')
        
        if expected_checksum and not verify_checksum(current_checksum, expected_checksum):
            log_warning(f"Checksum mismatch for {dataset_name}. Re-downloading...")
            # Remove corrupted file
            output_file.unlink()
        else:
            print(f"Checksum verified: {current_checksum}")
            # Record in state immediately
            state = load_state_file(STATE_FILE)
            state['artifact_hashes'][f"raw_{dataset_name}"] = current_checksum
            save_state_file(STATE_FILE, state)
            return True, str(output_file), current_checksum
    
    # Attempt to download/load the dataset
    try:
        print(f"Loading dataset: {dataset_name}")
        
        # Dispatch to appropriate loader based on dataset name
        if dataset_name == "adult":
            df = load_adult()
        elif dataset_name == "compas":
            df = load_compas()
        elif dataset_name == "bank":
            df = load_bank()
        elif dataset_name == "german":
            df = load_german()
        elif dataset_name == "lawschool":
            df = load_lawschool()
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        if df is None or df.empty:
            log_warning(f"Failed to load data for {dataset_name}")
            return False, None, None
        
        # Save to raw directory
        df.to_csv(output_file, index=False)
        print(f"Saved raw data to: {output_file}")
        
        # Calculate checksum
        checksum = get_file_checksum(output_file)
        print(f"Calculated SHA-256 checksum: {checksum}")
        
        # IMMEDIATELY record in state file before any processing
        state = load_state_file(STATE_FILE)
        state['artifact_hashes'][f"raw_{dataset_name}"] = checksum
        save_state_file(STATE_FILE, state)
        print(f"Recorded checksum in state file: {STATE_FILE}")
        
        return True, str(output_file), checksum
        
    except Exception as e:
        log_warning(f"Error processing {dataset_name}: {str(e)}")
        return False, None, None

def main():
    """Main execution function for data acquisition."""
    log_header("DATA ACQUISITION PIPELINE")
    log_disclaimer()
    
    # Initialize state file if it doesn't exist
    if not STATE_FILE.exists():
        print(f"Initializing state file: {STATE_FILE}")
        save_state_file(STATE_FILE, {
            "project_id": "PROJ-099-statistical-analysis-of-algorithmic-fair",
            "artifact_hashes": {}
        })
    
    # Define datasets to process
    # Note: Checksums are not hardcoded; we calculate them after download
    # and store them in the state file.
    datasets = [
        ("adult", get_dataset_info("adult")),
        ("compas", get_dataset_info("compas")),
        ("bank", get_dataset_info("bank")),
        ("german", get_dataset_info("german")),
        ("lawschool", get_dataset_info("lawschool"))
    ]
    
    results = []
    success_count = 0
    
    for name, info in datasets:
        success, file_path, checksum = download_and_verify_dataset(name, info)
        if success:
            success_count += 1
            results.append({
                "dataset": name,
                "status": "success",
                "file_path": file_path,
                "checksum": checksum
            })
        else:
            results.append({
                "dataset": name,
                "status": "failed",
                "file_path": None,
                "checksum": None
            })
    
    # Summary
    log_header("ACQUISITION SUMMARY")
    print(f"Total datasets attempted: {len(datasets)}")
    print(f"Successful downloads: {success_count}")
    print(f"Failed downloads: {len(datasets) - success_count}")
    
    # Print state file location
    print(f"\nState file updated at: {STATE_FILE}")
    
    # Load and display current state
    current_state = load_state_file(STATE_FILE)
    print("\nCurrent artifact hashes in state:")
    for key, value in current_state.get('artifact_hashes', {}).items():
        print(f"  {key}: {value[:16]}...")
        
    log_disclaimer()
    
    return success_count == len(datasets)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
