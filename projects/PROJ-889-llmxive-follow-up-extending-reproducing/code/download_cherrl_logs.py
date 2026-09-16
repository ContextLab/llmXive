import os
import sys
import hashlib
import shutil
from pathlib import Path
from typing import Optional

# Ensure we can import from the code directory
sys.path.insert(0, str(Path(__file__).parent))

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' package is required. Install it with: pip install datasets")
    sys.exit(1)

from utils.io_utils import ensure_dir
from config import get_project_root

# Verified source constants
VERIFIED_DATASET_NAME = "cherrl-repo/logs"
VERIFIED_SPLIT = "train"
EXPECTED_CHECKSUM = None  # Optional: Define if a specific checksum is known for the artifact

def verify_arxiv_source() -> bool:
    """
    Validates that the CHERRL repository source is accessible and matches expectations.
    Currently, this checks if the dataset can be loaded from the verified HuggingFace source.
    
    Returns:
        bool: True if source is valid, False otherwise.
    """
    try:
        # Attempt a lightweight load to verify connectivity and source validity
        # We use streaming=False to force an immediate check if the dataset exists
        # However, for a quick validation, we might just try to get the info
        ds_info = load_dataset(VERIFIED_DATASET_NAME, split=VERIFIED_SPLIT, streaming=True)
        # If we can iterate even one item, the source is likely valid
        iterator = iter(ds_info)
        next(iterator)
        return True
    except Exception as e:
        print(f"ERROR: Data source unreachable or mismatch: {e}")
        return False

def download_from_huggingface(output_dir: Path) -> bool:
    """
    Fetches real data from the verified CHERRL repository using HuggingFace datasets.
    Saves extracted logs to the specified output directory.
    
    Args:
        output_dir: Path to the directory where logs will be saved.
        
    Returns:
        bool: True if download and save were successful, False otherwise.
    """
    try:
        print(f"Fetching data from HuggingFace: {VERIFIED_DATASET_NAME} (split={VERIFIED_SPLIT})...")
        
        # Load the dataset
        # Note: Using streaming=False to ensure we get the full data if feasible, 
        # or we can iterate if it's massive. For this implementation, we assume 
        # we need to process it into files.
        dataset = load_dataset(VERIFIED_DATASET_NAME, split=VERIFIED_SPLIT)
        
        if not dataset:
            print("ERROR: Dataset is empty.")
            return False

        print(f"Dataset loaded with {len(dataset)} examples.")

        # Ensure output directory exists
        ensure_dir(output_dir)

        # Save the dataset to Parquet or CSV files in the output directory
        # The task requires saving to `data/raw/cherrl_logs/`
        # We will save as parquet for efficiency, or csv if preferred. 
        # Given the schema, parquet is robust.
        output_file = output_dir / "cherrl_logs.parquet"
        
        # Save to parquet
        dataset.to_parquet(str(output_file))
        
        # Verify the file was created
        if not output_file.exists():
            print("ERROR: Failed to write output file.")
            return False
        
        # Optional: Calculate checksum for verification if EXPECTED_CHECKSUM is set
        if EXPECTED_CHECKSUM:
            file_hash = hashlib.sha256(output_file.read_bytes()).hexdigest()
            if file_hash != EXPECTED_CHECKSUM:
                print(f"ERROR: Checksum mismatch. Expected {EXPECTED_CHECKSUM}, got {file_hash}")
                return False

        print(f"Successfully saved logs to {output_file}")
        return True

    except Exception as e:
        print(f"ERROR: Data source unreachable or mismatch: {e}")
        return False

def main():
    """
    Main entry point for downloading CHERRL logs.
    1. Verifies the source.
    2. Downloads data to data/raw/cherrl_logs/.
    3. Exits with code 2 if any step fails.
    """
    project_root = get_project_root()
    output_dir = project_root / "data" / "raw" / "cherrl_logs"
    
    # Step 1: Verify Source
    if not verify_arxiv_source():
        print("ERROR: Data source unreachable or mismatch")
        sys.exit(2)
    
    # Step 2: Download
    if not download_from_huggingface(output_dir):
        print("ERROR: Data source unreachable or mismatch")
        sys.exit(2)
        
    print("Download completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()