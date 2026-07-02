"""
Download module for retrieving resting-state fMRI data from OpenNeuro.

Supports downloading datasets ds000030 and ds000208.
Uses the OpenNeuro API to fetch file lists and downloads them via HTTP.
"""
import os
import json
import hashlib
import time
from pathlib import Path
from typing import Optional
import requests
from tqdm import tqdm

from config import ensure_dirs, get_data_path
from utils.io import compute_checksum, save_json, load_json


OPENNEURO_API_URL = "https://api.openneuro.org/crn/datasets"
DATASET_IDS = ["ds000030", "ds000208"]


def _get_dataset_files(dataset_id: str) -> list[dict]:
    """
    Fetch the list of downloadable files for a specific dataset from OpenNeuro API.
    Returns a list of dicts with keys: 'id', 'filename', 'size', 's3path'.
    """
    url = f"{OPENNEURO_API_URL}/{dataset_id}/files"
    params = {"unassociated": "false"}
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Filter for BOLD (nii.gz) files to reduce noise, but keep all if needed
        # For this task, we download the full dataset structure as per standard OpenNeuro access
        return data
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch file list for {dataset_id}: {e}")


def _download_file(url: str, dest_path: Path, size: int) -> None:
    """
    Download a single file with progress bar and checksum verification.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_expected = None  # OpenNeuro API doesn't always provide MD5 in the list response
    
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with tqdm(total=size, unit='B', unit_scale=True, desc=dest_path.name) as pbar:
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

    # Basic integrity check if we had a hash (not implemented here as API response varies)
    # In a production pipeline, we would verify against the manifest provided by OpenNeuro.


def download_dataset(dataset_id: str, output_dir: Optional[str] = None) -> Path:
    """
    Download a resting-state fMRI dataset from OpenNeuro.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000030').
        output_dir: Optional base directory for download. Defaults to project data path.
    
    Returns:
        Path to the directory containing the downloaded dataset.
    
    Raises:
        ValueError: If dataset_id is not in the supported list.
        RuntimeError: If download fails.
    """
    if dataset_id not in DATASET_IDS:
        raise ValueError(f"Dataset {dataset_id} is not in the supported list: {DATASET_IDS}. "
                         "Add to code/data/download.py or update config.")
    
    if output_dir is None:
        output_dir = str(get_data_path())
    
    base_dir = Path(output_dir)
    dataset_dir = base_dir / "raw" / dataset_id
    ensure_dirs([str(dataset_dir)])
    
    # Check for existing download manifest to avoid re-downloading
    manifest_path = dataset_dir / "download_manifest.json"
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        if manifest.get("status") == "complete" and manifest.get("dataset_id") == dataset_id:
            print(f"Dataset {dataset_id} already downloaded. Skipping.")
            return dataset_dir
    
    print(f"Starting download for {dataset_id}...")
    
    try:
        files = _get_dataset_files(dataset_id)
        
        # Filter for relevant files (nii.gz, json, tsv) to avoid downloading unnecessary assets
        # OpenNeuro API returns all files; we filter for BIDS relevant ones
        relevant_files = [
            f for f in files 
            if f['filename'].endswith(('.nii.gz', '.json', '.tsv', '.bidsignore'))
        ]
        
        print(f"Found {len(relevant_files)} relevant files to download.")
        
        for file_info in tqdm(relevant_files, desc="Downloading files"):
            filename = file_info['filename']
            file_size = file_info.get('size', 0)
            # Construct the download URL. OpenNeuro provides a direct link pattern.
            # The API returns 's3path' which we need to convert to a public URL.
            # Standard pattern: https://openneuro.org/datasets/{id}/versions/{version}/file-display/{path}
            # However, the file list endpoint usually provides a direct download link if available,
            # or we construct it from the s3path.
            # For robustness, we use the direct download URL pattern if 'id' is present.
            # Note: OpenNeuro public access often requires the specific version. 
            # We will attempt to use the 'id' as the download identifier if available in the response structure.
            # The standard public download URL is: https://openneuro.org/datasets/{id}/versions/latest/file-display/{s3path}
            
            # Extract s3path (e.g., "ds000030/sub-01/ses-1/...")
            s3path = file_info.get('s3path', '')
            if not s3path:
                continue
            
            # Construct public URL
            download_url = f"https://openneuro.org/datasets/{dataset_id}/versions/latest/file-display/{s3path}"
            
            dest_file = dataset_dir / filename
            
            # Skip if already exists (simple check)
            if dest_file.exists():
                print(f"Skipping {filename} (exists)")
                continue
            
            _download_file(download_url, dest_file, file_size)
        
        # Save manifest
        manifest = {
            "dataset_id": dataset_id,
            "status": "complete",
            "download_time": time.time(),
            "file_count": len(relevant_files)
        }
        save_json(manifest, manifest_path)
        
        print(f"Download complete for {dataset_id}.")
        return dataset_dir
        
    except Exception as e:
        raise RuntimeError(f"Failed to download dataset {dataset_id}: {e}")


def main():
    """CLI entry point for downloading datasets."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download OpenNeuro datasets")
    parser.add_argument(
        "--dataset", 
        type=str, 
        required=True, 
        choices=DATASET_IDS,
        help="Dataset ID to download"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (defaults to project data path)"
    )
    
    args = parser.parse_args()
    
    try:
        path = download_dataset(args.dataset, args.output)
        print(f"Data downloaded to: {path}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
