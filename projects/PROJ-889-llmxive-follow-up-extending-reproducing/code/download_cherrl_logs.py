"""
Download CHERRL trajectory logs from the verified HuggingFace repository.

This script fetches real data from the CHERRL repository artifacts.
It implements a 'fail loud' strategy: if the fetch fails or the source
does not match the verified data URL, it logs an error and exits with code 2.

No synthetic fallback is allowed.
"""
import os
import sys
import hashlib
import shutil
from pathlib import Path
import requests
import tarfile
import zipfile
import json

# Verified data source configuration
# Based on arXiv:2606.04923 and CHERRL repository artifacts
VERIFIED_REPO_ID = "CHERRL-repo/trajectory-logs"
VERIFIED_DATASET_NAME = "cherrl_trajectories"
EXPECTED_FILE_PATTERN = "seed_*.json"

# Output directory relative to project root
OUTPUT_DIR_NAME = "data/raw/cherrl_logs"

def get_project_root() -> Path:
    """Get the project root directory (parent of 'code' directory)."""
    return Path(__file__).resolve().parent.parent

def verify_arxiv_source() -> bool:
    """
    Verify that the data source is accessible and matches the verified CHERRL repository.
    
    Returns:
        bool: True if source is verified, False otherwise.
    
    Raises:
        SystemExit: If the source is unreachable or mismatched (exit code 2).
    """
    project_root = get_project_root()
    output_dir = project_root / OUTPUT_DIR_NAME
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if data already exists to avoid redundant downloads
    existing_files = list(output_dir.glob("*.json"))
    if existing_files:
        print(f"INFO: Found {len(existing_files)} existing log files in {output_dir}")
        # Verify at least one file is valid JSON
        try:
            with open(existing_files[0], 'r') as f:
                json.load(f)
            print("INFO: Existing data appears valid, skipping download")
            return True
        except (json.JSONDecodeError, Exception) as e:
            print(f"WARNING: Existing data invalid, will re-download: {e}")
            shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"INFO: Verifying data source: {VERIFIED_REPO_ID}")
    
    try:
        # Attempt to list files from the HuggingFace dataset
        # Using the HuggingFace Hub API endpoint
        api_url = f"https://huggingface.co/api/datasets/{VERIFIED_REPO_ID}"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            print(f"ERROR: Data source unreachable (HTTP {response.status_code})")
            print("ERROR: Data source unreachable or mismatch")
            sys.exit(2)
        
        dataset_info = response.json()
        
        # Verify dataset exists and is accessible
        if "id" not in dataset_info or dataset_info["id"] != VERIFIED_REPO_ID:
            print(f"ERROR: Source mismatch. Expected {VERIFIED_REPO_ID}, got {dataset_info.get('id')}")
            print("ERROR: Data source unreachable or mismatch")
            sys.exit(2)
        
        print(f"INFO: Verified dataset source: {dataset_info['id']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error accessing data source: {e}")
        print("ERROR: Data source unreachable or mismatch")
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: Unexpected error verifying source: {e}")
        print("ERROR: Data source unreachable or mismatch")
        sys.exit(2)

def download_from_huggingface() -> bool:
    """
    Download the CHERRL trajectory logs from the verified HuggingFace repository.
    
    Returns:
        bool: True if download successful, False otherwise.
    
    Raises:
        SystemExit: If download fails (exit code 2).
    """
    project_root = get_project_root()
    output_dir = project_root / OUTPUT_DIR_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"INFO: Starting download from {VERIFIED_REPO_ID} to {output_dir}")
    
    try:
        # Use the HuggingFace datasets library for robust download
        # First, check if the library is available
        try:
            from datasets import load_dataset
        except ImportError:
            print("ERROR: 'datasets' library not installed. Please install it with: pip install datasets")
            print("ERROR: Data source unreachable or mismatch")
            sys.exit(2)
        
        # Load the dataset with streaming to handle large data
        print("INFO: Loading dataset with streaming...")
        dataset = load_dataset(
            VERIFIED_REPO_ID,
            split="train",
            streaming=True
        )
        
        # Process and save the data
        log_count = 0
        for idx, item in enumerate(dataset):
            # Validate item structure
            if not isinstance(item, dict):
                print(f"ERROR: Invalid item format at index {idx}")
                continue
            
            # Create filename based on seed_id if available
            seed_id = item.get("seed_id", f"seed_{idx:04d}")
            filename = f"{seed_id}.json"
            filepath = output_dir / filename
            
            # Save the trajectory data
            with open(filepath, 'w') as f:
                json.dump(item, f, indent=2)
            
            log_count += 1
            
            # Progress indicator every 100 items
            if log_count % 100 == 0:
                print(f"INFO: Downloaded {log_count} logs...")
        
        print(f"INFO: Successfully downloaded {log_count} trajectory logs to {output_dir}")
        
        if log_count == 0:
            print("ERROR: No data downloaded from the source")
            print("ERROR: Data source unreachable or mismatch")
            sys.exit(2)
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to download data: {e}")
        print("ERROR: Data source unreachable or mismatch")
        sys.exit(2)

def main():
    """Main entry point for the CHERRL log download script."""
    print("=" * 60)
    print("CHERRL Trajectory Log Downloader")
    print("=" * 60)
    
    # Step 1: Verify the data source
    print("\n[1/2] Verifying data source...")
    if not verify_arxiv_source():
        print("ERROR: Source verification failed")
        sys.exit(2)
    
    # Step 2: Download the data
    print("\n[2/2] Downloading trajectory logs...")
    if not download_from_huggingface():
        print("ERROR: Download failed")
        sys.exit(2)
    
    print("\n" + "=" * 60)
    print("SUCCESS: CHERRL logs downloaded and saved to data/raw/cherrl_logs/")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())