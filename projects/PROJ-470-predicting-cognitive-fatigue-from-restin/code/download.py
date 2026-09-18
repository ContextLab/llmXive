"""Download public EEG dataset with resting-state and fatigue ratings.

Implements T009: Fetch a public dataset containing both resting-state EEG AND paired pre/post fatigue ratings.
"""
import os
import sys
import json
import logging
import time
import io
import requests
from pathlib import Path
import shutil
import uuid

# Import local utilities
from utils.logging import get_logger

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file=None):
    """Setup a logger that writes to file and console."""
    logger = get_logger(name, log_file)
    return logger

def write_validation_report(report_data, output_path):
    """Write validation report to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)

def fetch_huggingface_metadata(dataset_id, token=None):
    """Fetch metadata from HuggingFace Hub."""
    url = f"https://huggingface.co/api/datasets/{dataset_id}"
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    # Perform HTTP HEAD request to check existence before full download
    head_response = requests.head(url, headers=headers, timeout=30)
    if head_response.status_code == 404:
        raise RuntimeError(f"Dataset not found: {dataset_id} (HTTP 404)")
    elif head_response.status_code != 200:
        # Try GET if HEAD fails for some reason but might still exist
        get_response = requests.get(url, headers=headers, timeout=30)
        if get_response.status_code != 200:
            raise RuntimeError(f"Failed to fetch metadata: {get_response.status_code}")
        return get_response.json()
    
    # Proceed with GET to fetch full metadata
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch metadata: {response.status_code}")
    return response.json()

def search_huggingface_datasets(query, token=None):
    """Search HuggingFace for datasets."""
    url = "https://huggingface.co/api/datasets"
    params = {'search': query}
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    response = requests.get(url, params=params, headers=headers, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to search datasets: {response.status_code}")
    return response.json()

def validate_dataset(metadata, required_variables):
    """Validate that dataset has required variables."""
    # This is a placeholder; real validation would check dataset structure
    return True

def download_raw_data(dataset_id, output_dir, token=None):
    """Download raw data from HuggingFace."""
    from huggingface_hub import snapshot_download
    try:
        local_dir = snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            local_dir=output_dir,
            token=token
        )
        return local_dir
    except Exception as e:
        raise RuntimeError(f"Failed to download dataset: {e}")

def log_participant_exclusions(exclusions, output_path):
    """Log participant exclusions to CSV."""
    import pandas as pd
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not exclusions:
        with open(output_path, 'w') as f:
            f.write("participant_id,reason,timestamp\n")
        return
    df = pd.DataFrame(exclusions)
    df.to_csv(output_path, index=False)

def main():
    """Main entry point for download pipeline."""
    logger = setup_logger("download")
    logger.info("Starting download pipeline.")

    # Load config
    try:
        config = load_config()
    except FileNotFoundError:
        print("Warning: config.yaml not found. Using defaults.")
        config = {}

    # Dataset ID (hardcoded as per task requirement)
    dataset_id = 'eeg-fatigue-resting-v1'
    output_dir = "data/raw"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Attempt to fetch metadata (HTTP HEAD check included in fetch_huggingface_metadata)
    try:
        metadata = fetch_huggingface_metadata(dataset_id)
        logger.info(f"Metadata fetched successfully for {dataset_id}")
    except RuntimeError as e:
        logger.error(f"Failed to fetch or parse metadata. Exiting: {e}")
        print(f"ERROR: {e}")
        print(f"Expected dataset ID: {dataset_id}")
        sys.exit(1)

    # Attempt to download raw data
    try:
        local_dir = download_raw_data(dataset_id, output_dir)
        logger.info(f"Dataset downloaded to {local_dir}")
    except RuntimeError as e:
        logger.error(f"Failed to download dataset. Exiting: {e}")
        print(f"ERROR: {e}")
        print(f"Expected dataset ID: {dataset_id}")
        sys.exit(1)

    # Find the first available subject's data file (assuming .fif format)
    sample_file = None
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.fif'):
                sample_file = os.path.join(root, file)
                break
        if sample_file:
            break

    if not sample_file:
        logger.error("No .fif file found in the downloaded dataset.")
        print("ERROR: No .fif file found in the downloaded dataset.")
        sys.exit(1)

    # Generate a unique run ID for the sample file copy
    unique_run_id = uuid.uuid4().hex
    sample_copy_path = os.path.join(output_dir, f"sample_eeg_{unique_run_id}.fif")
    
    # Copy the first subject's data file to the sample location
    shutil.copy2(sample_file, sample_copy_path)
    logger.info(f"Sample file copied to {sample_copy_path}")

    # Write manifest
    manifest = {
        'dataset_id': dataset_id,
        'download_time': time.strftime("%Y-%m-%d %H:%M:%S"),
        'sample_file': sample_copy_path,
        'source_dir': local_dir,
        'status': 'success'
    }
    manifest_path = os.path.join(output_dir, "download_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Download complete. Manifest written to {manifest_path}")
    print(f"Success: Downloaded sample data to {sample_copy_path}")
    print(f"Manifest written to {manifest_path}")

if __name__ == "__main__":
    main()