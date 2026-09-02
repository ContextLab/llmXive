import os
import sys
import json
import hashlib
import requests
import zipfile
import io
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

def get_study_download_url(study_id: str) -> str:
    """Construct the download URL for a study."""
    # Convert C00004 to ST000004
    base_id = study_id.replace('C', 'ST')
    return f"https://www.metabolomicsworkbench.org/data/{base_id}/{base_id}_RAW_DATA.TXT"

def download_study_data(url: str, timeout: int = 60) -> Optional[str]:
    """Download data from a URL and return the content."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error downloading from {url}: {e}")
        return None

def extract_and_save_csvs(content: str, output_path: Path):
    """
    Save the downloaded content to a file.
    This is a simplified version; real extraction might involve parsing.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def load_phenotype_metadata(phenotype_path: Path) -> Optional[Dict[str, Any]]:
    """Load phenotype metadata from a file."""
    if not phenotype_path.exists():
        return None
    try:
        with open(phenotype_path, 'r') as f:
            # Assuming CSV/TSV format
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            return {"headers": headers}
    except Exception as e:
        print(f"Error loading phenotype metadata: {e}")
        return None

def verify_temporal_separation(metadata: Dict[str, Any]) -> bool:
    """Verify that temporal separation exists in metadata."""
    if not metadata or "headers" not in metadata:
        return False
    headers = set(metadata["headers"])
    temporal_keywords = {'timepoint', 'sample_date', 'inoculation_date', 'days_post_inoculation'}
    return bool(headers.intersection(temporal_keywords))

def compute_checksums(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_study(study_id: str, output_dir: Path):
    """Download study data and save to output directory."""
    url = get_study_download_url(study_id)
    content = download_study_data(url)
    
    if content:
        intensity_file = output_dir / f"{study_id}_raw_intensity.csv"
        extract_and_save_csvs(content, intensity_file)
        checksum = compute_checksums(intensity_file)
        print(f"Downloaded {intensity_file.name}, checksum: {checksum}")
        return True
    return False

def main():
    """Main entry point."""
    print("Running download_study.py (helper for T012b)")
    # This is a helper module, main logic is in match_and_download.py
    # This main is for standalone testing if needed

if __name__ == "__main__":
    main()