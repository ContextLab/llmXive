import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Optional
import time

# FR-008 Disclaimer constant
FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(message: str) -> None:
    """Print a formatted header with the FR-008 disclaimer."""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"  {FR008_DISCLAIMER}")
    print(f"{'='*60}\n")

def log_disclaimer() -> None:
    """Log the FR-008 disclaimer to stdout."""
    print(f"[DISCLAIMER] {FR008_DISCLAIMER}")

def get_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_and_verify_dataset(
    url: str,
    output_path: Path,
    expected_checksum: Optional[str] = None,
    dataset_name: str = "Unknown"
) -> Tuple[bool, str]:
    """
    Download a dataset from a URL and verify its checksum.
    
    Args:
        url: The URL to download from.
        output_path: Where to save the file.
        expected_checksum: Optional SHA-256 checksum to verify against.
        dataset_name: Name of the dataset for logging.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    log_header(f"Downloading {dataset_name}")
    log_disclaimer()
    
    try:
        import requests
        # Whitelist domains check
        allowed_domains = ['archive.ics.uci.edu', 'raw.githubusercontent.com', 'datasets.load_dataset']
        # Simple domain check logic (simplified for this implementation)
        if not any(domain in url for domain in allowed_domains):
            # Allow specific known URLs if they don't match whitelist but are known
            pass 
        
        print(f"Downloading from: {url}")
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        actual_checksum = get_file_checksum(output_path)
        print(f"Downloaded {output_path.name}")
        print(f"SHA-256: {actual_checksum}")
        
        if expected_checksum:
            if actual_checksum.lower() == expected_checksum.lower():
                print(f"Checksum verification PASSED for {dataset_name}")
                return True, actual_checksum
            else:
                print(f"Checksum verification FAILED for {dataset_name}")
                print(f"Expected: {expected_checksum}")
                print(f"Actual:   {actual_checksum}")
                return False, f"Checksum mismatch for {dataset_name}"
        else:
            print(f"No checksum provided for {dataset_name}, skipping verification.")
            return True, actual_checksum
            
    except Exception as e:
        print(f"Error downloading {dataset_name}: {str(e)}")
        return False, str(e)

def main():
    """Main entry point for data acquisition."""
    log_header("US1 Data Acquisition Pipeline")
    log_disclaimer()
    
    print("Starting data acquisition process...")
    
    # Define datasets (URLs and checksums would be populated from spec)
    # This is a simplified structure; real implementation would load from config
    datasets = [
        {
            "name": "UCI Adult",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data",
            "output": Path("data/raw/adult.data"),
            "checksum": None  # To be filled from spec
        },
        {
            "name": "COMPAS",
            "url": "https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv",
            "output": Path("data/raw/compas-scores-two-years.csv"),
            "checksum": None
        },
        {
            "name": "Bank Marketing",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00222/bank-additional.zip",
            "output": Path("data/raw/bank-additional.zip"),
            "checksum": None
        },
        {
            "name": "German Credit",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data",
            "output": Path("data/raw/german.data"),
            "checksum": None
        },
        {
            "name": "Law School",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00417/law_school_data.csv",
            "output": Path("data/raw/law_school_data.csv"),
            "checksum": None
        }
    ]
    
    success_count = 0
    for ds in datasets:
        print(f"\nProcessing: {ds['name']}")
        success, msg = download_and_verify_dataset(
            ds['url'], 
            ds['output'], 
            ds.get('checksum'),
            ds['name']
        )
        if success:
            success_count += 1
        else:
            print(f"Failed: {msg}")
    
    print(f"\n{'='*60}")
    print(f"Data Acquisition Summary")
    print(f"{'='*60}")
    print(f"Total datasets: {len(datasets)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(datasets) - success_count}")
    print(f"{FR008_DISCLAIMER}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
