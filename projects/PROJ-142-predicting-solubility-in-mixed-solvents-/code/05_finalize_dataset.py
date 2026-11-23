"""
Finalize the processed dataset: load features, write to CSV, and generate checksum.

This script implements T018: Write final processed dataset to 
data/processed/solubility_features.csv with checksum.

Dependencies:
- T016: add_interaction_terms (generates data/processed/solubility_features.csv)
- code/utils/checksums.py: generate_checksums
- code/utils/constants.py: DATA_DIR
"""
import os
import sys
import json
import hashlib
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.constants import DATA_DIR
from utils.checksums import generate_checksums
from utils.errors import CustomDataError

import pandas as pd

# Define paths
INPUT_FILE = DATA_DIR / "processed" / "solubility_features.csv"
OUTPUT_FILE = DATA_DIR / "processed" / "solubility_features.csv"
CHECKSUM_FILE = DATA_DIR / ".checksums.json"
ARTIFACTS_DIR = DATA_DIR / "artifacts"

def calculate_file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def finalize_dataset():
    """
    Main logic for T018:
    1. Verify input file exists (produced by T016).
    2. Load the data to ensure it's valid.
    3. Write the final CSV (overwriting if necessary to ensure freshness).
    4. Generate checksums for the dataset.
    5. Update the global checksum file.
    """
    # 1. Verify input exists
    if not INPUT_FILE.exists():
        raise CustomDataError(
            f"Input file not found: {INPUT_FILE}. "
            "Ensure T016 (add_interaction_terms) has been executed successfully."
        )

    # 2. Load and validate data
    try:
        df = pd.read_csv(INPUT_FILE)
    except Exception as e:
        raise CustomDataError(f"Failed to read input CSV: {e}")

    if df.empty:
        raise CustomDataError("Input dataset is empty. Cannot finalize an empty dataset.")

    print(f"Loaded {len(df)} rows from {INPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 3. Write final CSV
    # Use index=False to avoid saving row indices
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Finalized dataset written to: {OUTPUT_FILE}")

    # 4. Generate checksums for the dataset
    # We calculate the hash of the specific output file
    file_hash = calculate_file_hash(OUTPUT_FILE)
    
    checksum_entry = {
        "file": str(OUTPUT_FILE.relative_to(DATA_DIR)),
        "sha256": file_hash,
        "rows": len(df),
        "columns": len(df.columns),
        "timestamp": pd.Timestamp.now().isoformat()
    }

    # 5. Update global checksums file
    # Load existing checksums or create new
    if CHECKSUM_FILE.exists():
        try:
            with open(CHECKSUM_FILE, "r") as f:
                all_checksums = json.load(f)
        except json.JSONDecodeError:
            all_checksums = {}
    else:
        all_checksums = {}

    # Update or add the entry for this file
    # We use the relative path as the key for consistency
    rel_path = str(OUTPUT_FILE.relative_to(DATA_DIR))
    all_checksums[rel_path] = checksum_entry

    # Write updated checksums
    with open(CHECKSUM_FILE, "w") as f:
        json.dump(all_checksums, f, indent=2)
    
    print(f"Checksums updated in: {CHECKSUM_FILE}")
    print(f"SHA256: {file_hash}")
    
    # Log success to artifacts
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = ARTIFACTS_DIR / "finalization_log.txt"
    with open(log_file, "a") as f:
        f.write(f"{pd.Timestamp.now()}: T018 Completed. Rows: {len(df)}, Hash: {file_hash}\n")

    return True

def main():
    """Entry point for the script."""
    try:
        success = finalize_dataset()
        if success:
            print("T018: Finalization successful.")
            sys.exit(0)
    except Exception as e:
        print(f"ERROR: T018 Failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()