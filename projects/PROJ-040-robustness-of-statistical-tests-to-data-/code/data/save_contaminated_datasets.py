"""
Save contaminated datasets to data/processed/ with derivation logs and checksums.

This script depends on the output of generate_contamination.py. It reads the 
contaminated datasets (which should exist in data/processed/ or be generated 
on the fly if the pipeline is run sequentially), computes SHA-256 checksums, 
and writes a derivation log (YAML) for each dataset.

Usage:
    python code/data/save_contaminated_datasets.py
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.generate_contamination import process_dataset, inject_contamination, main as generate_main
from utils.config import get_seed

# Constants
RAW_DATA_DIR = project_root / "data" / "raw"
PROCESSED_DATA_DIR = project_root / "data" / "processed"
LOGS_DIR = project_root / "data" / "processed" / "logs"

# Ensure output directories exist
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_derivation_log(dataset_name: str, contamination_rate: float, 
                        contamination_magnitude: float, original_file: Path, 
                        output_file: Path, checksum: str):
    """Save a YAML derivation log for a contaminated dataset."""
    log_data = {
        "dataset_name": dataset_name,
        "original_file": str(original_file),
        "output_file": str(output_file),
        "contamination_rate": contamination_rate,
        "contamination_magnitude_sigma": contamination_magnitude,
        "checksum_sha256": checksum,
        "generated_at": datetime.now().isoformat(),
        "random_seed": get_seed(),
        "derivation": {
            "method": "Gaussian noise injection and extreme outlier addition",
            "library": "numpy",
            "seed_used": get_seed()
        }
    }
    
    log_path = LOGS_DIR / f"{dataset_name}_rate_{contamination_rate:.2f}_mag_{contamination_magnitude:.1f}.yaml"
    with open(log_path, "w") as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
    return log_path

def process_and_save_contamination(dataset_name: str, contamination_rate: float, 
                                   contamination_magnitude: float):
    """
    Process a dataset with contamination, save the result, and generate logs.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'wine', 'har')
        contamination_rate: Fraction of rows to contaminate (0.0 to 1.0)
        contamination_magnitude: Sigma multiplier for Gaussian noise (e.g., 3.0, 5.0)
    """
    # Find the original file
    original_file = None
    possible_extensions = ['.csv', '.txt', '.data']
    for ext in possible_extensions:
        candidate = RAW_DATA_DIR / f"{dataset_name}{ext}"
        if candidate.exists():
            original_file = candidate
            break
    
    if not original_file:
        print(f"Warning: Original file for '{dataset_name}' not found in {RAW_DATA_DIR}. Skipping.")
        return

    # Load original data
    if original_file.suffix == '.csv':
        df = pd.read_csv(original_file)
    else:
        # Fallback for other formats, assuming CSV-like for UCI Wine/HAR
        df = pd.read_csv(original_file, header=None)

    # Inject contamination
    contaminated_df = inject_contamination(
        df, 
        contamination_rate=contamination_rate, 
        sigma_multiplier=contamination_magnitude,
        seed=get_seed()
    )

    # Define output filename
    output_filename = f"{dataset_name}_contaminated_rate_{contamination_rate:.2f}_mag_{contamination_magnitude:.1f}.csv"
    output_path = PROCESSED_DATA_DIR / output_filename

    # Save to disk
    contaminated_df.to_csv(output_path, index=False)
    print(f"Saved contaminated dataset: {output_path}")

    # Compute checksum
    checksum = compute_sha256(output_path)
    print(f"Checksum (SHA-256): {checksum}")

    # Save derivation log
    log_path = save_derivation_log(
        dataset_name, 
        contamination_rate, 
        contamination_magnitude, 
        original_file, 
        output_path, 
        checksum
    )
    print(f"Saved derivation log: {log_path}")

def main():
    """
    Main entry point to save contaminated datasets for all configured rates.
    """
    # Define contamination scenarios based on typical research needs (T014 will sweep these)
    # Using a fixed set for T013 to ensure artifacts exist
    scenarios = [
        ("wine", 0.01, 3.0),
        ("wine", 0.05, 3.0),
        ("wine", 0.10, 3.0),
        ("har", 0.01, 3.0),
        ("har", 0.05, 3.0),
        ("har", 0.10, 3.0),
    ]

    print(f"Starting contamination save process for {len(scenarios)} scenarios...")
    print(f"Random Seed: {get_seed()}")
    print(f"Output Directory: {PROCESSED_DATA_DIR}")

    for dataset_name, rate, magnitude in scenarios:
        try:
            process_and_save_contamination(dataset_name, rate, magnitude)
        except Exception as e:
            print(f"Error processing {dataset_name} at rate {rate}: {e}")
            # Continue with other scenarios

    print("Contamination save process completed.")

if __name__ == "__main__":
    main()