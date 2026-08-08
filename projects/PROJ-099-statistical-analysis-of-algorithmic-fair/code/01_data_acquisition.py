import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Optional

# Ensure utils are importable relative to code/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.dataset_loaders import (
    load_adult,
    load_compas,
    load_bank,
    load_german,
    load_lawschool,
    get_dataset_info
)
from utils.validators import compute_sha256, verify_checksum
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

def download_and_verify_dataset(
    dataset_name: str,
    raw_dir: Path,
    checksums: Dict[str, str]
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Download a dataset, verify its checksum, and return the path.
    Returns (path, checksum) on success, (None, None) on failure.
    """
    log_header(raw_dir, f"Downloading {dataset_name}")
    
    info = get_dataset_info(dataset_name)
    if not info:
        print(f"ERROR: Dataset {dataset_name} not found in registry.")
        return None, None

    try:
        # Load dataset (this handles download/fetching internally)
        df = info['loader'](raw_dir)
        
        if df is None:
            print(f"ERROR: Failed to load {dataset_name}.")
            return None, None

        # Save to raw directory
        output_path = raw_dir / f"{dataset_name}_raw.csv"
        df.to_csv(output_path, index=False)
        
        # Compute checksum
        current_checksum = compute_sha256(output_path)
        
        # Verify against known checksum if available
        if dataset_name in checksums:
            if not verify_checksum(output_path, checksums[dataset_name]):
                print(f"ERROR: Checksum mismatch for {dataset_name}.")
                print(f"Expected: {checksums[dataset_name]}")
                print(f"Got: {current_checksum}")
                return None, None
            print(f"Checksum verified for {dataset_name}.")
        else:
            print(f"WARNING: No known checksum for {dataset_name}. Skipping verification.")
        
        print(f"Successfully downloaded and saved {dataset_name} to {output_path}")
        print(f"SHA-256: {current_checksum}")
        return output_path, current_checksum

    except Exception as e:
        print(f"ERROR: Failed to download/verify {dataset_name}: {e}")
        return None, None

def main():
    """
    Main entry point for data acquisition.
    Downloads all configured datasets to data/raw/
    """
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'#'*60}")
    print(f"# DATA ACQUISITION PIPELINE")
    print(f"# {FR008_DISCLAIMER}")
    print(f"{'#'*60}\n")

    # Define datasets to download
    # Note: Checksums are placeholders; real project would have verified hashes
    known_checksums = {
        "adult": "", 
        "compas": "",
        "bank": "",
        "german": "",
        "lawschool": ""
    }

    datasets = ["adult", "compas", "bank", "german", "lawschool"]
    downloaded = []

    for ds in datasets:
        path, checksum = download_and_verify_dataset(ds, raw_dir, known_checksums)
        if path:
            downloaded.append((ds, path, checksum))

    print(f"\n{'='*60}")
    print("ACQUISITION SUMMARY")
    print(f"{'='*60}")
    if downloaded:
        print(f"Successfully acquired {len(downloaded)} datasets:")
        for ds, p, c in downloaded:
            print(f"  - {ds}: {p} (SHA: {c[:16]}...)")
    else:
        print("No datasets were successfully acquired.")
    
    print(f"\nNOTE: {FR008_DISCLAIMER}")

if __name__ == "__main__":
    main()
