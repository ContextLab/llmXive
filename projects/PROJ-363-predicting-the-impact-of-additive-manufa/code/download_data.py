"""
Download the verified 316L LPBF dataset from Zenodo.

This script fetches the dataset, verifies the material type is 316L,
saves it to data/raw/, computes its SHA-256 checksum, and updates state.yaml.
"""
import os
import sys
import hashlib
import logging
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils import setup_logging, compute_file_hash, load_state, update_state

# Zenodo record ID for the 316L LPBF dataset
# Using a known public dataset: "Additive Manufacturing of 316L Stainless Steel"
ZENODO_RECORD_ID = "6826006"
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"
OUTPUT_DIR = project_root / "data" / "raw"
OUTPUT_FILENAME = "316L_LPBF_porosity.csv"
OUTPUT_PATH = OUTPUT_DIR / OUTPUT_FILENAME

def fetch_record_metadata():
    """Fetch metadata from Zenodo API."""
    import urllib.request
    import json as json_module

    try:
        with urllib.request.urlopen(ZENODO_API_URL, timeout=30) as response:
            data = json_module.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Zenodo metadata: {e}")

def verify_material_type(metadata):
    """Verify the dataset is for 316L stainless steel."""
    # Check title and description for 316L mention
    title = metadata.get('metadata', {}).get('title', '').lower()
    description = metadata.get('metadata', {}).get('description', '').lower()
    
    # Look for 316L in title or description
    if '316l' in title or '316l' in description:
        return True
    
    # Check keywords
    keywords = [kw.get('title', '').lower() for kw in metadata.get('metadata', {}).get('keywords', [])]
    if any('316l' in kw for kw in keywords):
        return True
    
    raise ValueError("Dataset does not appear to be for 316L stainless steel")

def download_file(file_url, output_path):
    """Download a file from the given URL."""
    import urllib.request

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with urllib.request.urlopen(file_url, timeout=120) as response:
            with open(output_path, 'wb') as f:
                # Download in chunks to show progress
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192
                
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = downloaded / total_size * 100
                        if downloaded % (chunk_size * 100) == 0:  # Update every ~800KB
                            print(f"\rDownload progress: {progress:.1f}%", end='')
                
                print()  # New line after progress
                
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to download file: {e}")

def main():
    """Main entry point for data download."""
    logger = setup_logging()
    logger.info("Starting 316L LPBF dataset download")

    # Fetch metadata
    logger.info(f"Fetching metadata from Zenodo record {ZENODO_RECORD_ID}")
    metadata = fetch_record_metadata()

    # Verify material type
    logger.info("Verifying material type is 316L")
    verify_material_type(metadata)
    logger.info("Material type verified: 316L")

    # Find the CSV file in the metadata
    files = metadata.get('files', [])
    csv_file = None
    
    for file_info in files:
        if file_info.get('key', '').endswith('.csv'):
            csv_file = file_info
            break
    
    if not csv_file:
        raise ValueError("No CSV file found in the Zenodo record")

    # Get download URL
    download_url = csv_file.get('links', {}).get('self')
    if not download_url:
        raise ValueError("No download link found for the CSV file")

    logger.info(f"Downloading file: {csv_file.get('key')}")
    logger.info(f"File size: {csv_file.get('size', 0) / 1024 / 1024:.2f} MB")
    
    # Download the file
    download_file(download_url, OUTPUT_PATH)
    
    # Verify download
    if not OUTPUT_PATH.exists():
        raise RuntimeError("Downloaded file not found after download")

    # Compute SHA-256 file hash
    file_hash = compute_file_hash(OUTPUT_PATH)
    logger.info(f"File SHA-256 hash: {file_hash}")

    # Update state.yaml
    state = load_state()
    update_state(
        state,
        artifact_name="raw_dataset",
        artifact_path=str(OUTPUT_PATH.relative_to(project_root)),
        file_hash=file_hash,
        metadata={
            "zenodo_id": ZENODO_RECORD_ID,
            "filename": csv_file.get('key'),
            "size_bytes": csv_file.get('size', 0),
            "downloaded_at": "now"
        }
    )

    logger.info(f"Successfully downloaded and saved to {OUTPUT_PATH}")
    logger.info(f"Updated state.yaml with file hash")

    return 0

if __name__ == "__main__":
    sys.exit(main())