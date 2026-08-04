"""
Download CHERRL logs from the verified HuggingFace dataset repository.

This script fetches real trajectory data required for the llmXive pipeline.
It implements a 'fail loud' strategy: if the data source is unreachable or
the dataset ID does not match the verified source, it logs an error and
exits with code 2. No mock mode or synthetic data generation is supported.
"""
import os
import sys
import hashlib
import shutil
from pathlib import Path
from typing import Optional

# Attempt to import datasets; if missing, the user must install it per requirements.txt
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' library is not installed. Please install it via 'pip install datasets'")
    sys.exit(2)

# Import project utilities
from config import get_project_root, ensure_paths_exist
from utils.validator import validate_cherrl_source
from utils.io_utils import ensure_dir


# Verified Data Source Configuration
# This matches the verified real data source provided in the project specification.
VERIFIED_DATASET_ID = "cherrl-repo/logs"
VERIFIED_SPLIT = "train"
OUTPUT_DIR_NAME = "cherrl_logs"
EXIT_CODE_DATA_MISSING = 2


def verify_arxiv_source() -> bool:
    """
    Validates that the data source matches the verified CHERRL repository.
    
    Returns:
        bool: True if the source is valid, False otherwise.
    
    Raises:
        SystemExit: If the source is invalid or unreachable.
    """
    try:
        # The validator checks against the known good source
        is_valid = validate_cherrl_source(VERIFIED_DATASET_ID)
        if not is_valid:
            print(f"ERROR: Data source '{VERIFIED_DATASET_ID}' is unreachable or mismatch.")
            return False
        return True
    except Exception as e:
        print(f"ERROR: Data source unreachable or mismatch: {e}")
        return False


def download_from_huggingface(output_path: Path) -> bool:
    """
    Downloads the CHERRL logs dataset from HuggingFace Hub.
    
    Args:
        output_path: The directory where the extracted logs will be saved.
        
    Returns:
        bool: True if download and extraction succeed, False otherwise.
    """
    print(f"Fetching dataset: {VERIFIED_DATASET_ID} (split: {VERIFIED_SPLIT})...")
    
    try:
        # Load the dataset using streaming=False to ensure we get the full data
        # as required for the analysis pipeline.
        dataset = load_dataset(
            VERIFIED_DATASET_ID,
            split=VERIFIED_SPLIT,
            trust_remote_code=True
        )
        
        if dataset is None or len(dataset) == 0:
            print("ERROR: Downloaded dataset is empty.")
            return False
        
        print(f"Successfully loaded {len(dataset)} records from HuggingFace.")
        
        # Ensure the output directory exists
        ensure_dir(output_path)
        
        # Save the dataset to parquet or CSV format for downstream processing.
        # We will save as parquet for efficiency, but the ingestion module
        # can handle various formats. Let's save as a single parquet file per seed
        # if possible, or a single file if the dataset is small enough.
        # For simplicity and robustness, we save the full split as a Parquet file.
        output_file = output_path / "cherrl_logs.parquet"
        
        # Convert to pandas and save (or use dataset.to_parquet if available)
        # Using to_pandas() ensures compatibility with standard pandas I/O
        df = dataset.to_pandas()
        df.to_parquet(output_file, index=False)
        
        print(f"Data saved to: {output_file}")
        
        # Verify the file was created and is not empty
        if not output_file.exists():
            print("ERROR: Output file was not created.")
            return False
        
        if output_file.stat().st_size == 0:
            print("ERROR: Output file is empty.")
            return False
            
        return True

    except Exception as e:
        print(f"ERROR: Failed to download or process dataset: {e}")
        return False


def main() -> int:
    """
    Main entry point for the download script.
    
    Returns:
        int: Exit code (0 for success, 2 for data missing/failure).
    """
    # 1. Setup paths
    project_root = get_project_root()
    raw_data_dir = project_root / "data" / "raw"
    output_dir = raw_data_dir / OUTPUT_DIR_NAME
    
    ensure_paths_exist() # Ensure data directories exist
    
    print(f"Project root: {project_root}")
    print(f"Target output directory: {output_dir}")
    
    # 2. Verify Source
    if not verify_arxiv_source():
        print(f"ERROR: Data source unreachable or mismatch")
        return EXIT_CODE_DATA_MISSING
    
    # 3. Download Data
    success = download_from_huggingface(output_dir)
    
    if not success:
        print(f"ERROR: Data source unreachable or mismatch")
        return EXIT_CODE_DATA_MISSING
    
    print("Download completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
