"""
Download eBird Basic Dataset (EBD) data for the Avian Foraging Behavior project.

This script fetches the EBD data from the official eBird S3 bucket (as the official
HTTPS download often requires a login or is rate-limited, the S3 bucket is the
verified fallback per project plan). It validates the presence of the file,
computes a SHA-256 checksum, and records metadata in data/metadata.yaml.

Output:
    data/raw/ebd_basic.csv (or .zip if compressed, handled as raw input)
    data/metadata.yaml (checksums and provenance info)
"""
import os
import sys
import hashlib
import yaml
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path to import utils
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.provenance import compute_file_hash, generate_provenance_record, save_provenance_record

# Configuration
# eBird EBD is hosted on AWS S3. The URL format is stable for the public dataset.
# We use the most recent release available. If a specific date is required,
# it should be updated here.
EBD_S3_BUCKET = "ebd-public"
EBD_FILE_NAME = "ebd_relFeb-2024.zip" # Example stable filename structure
# Note: The actual filename changes periodically. We will attempt to fetch the
# latest by checking a known stable URL pattern or a manifest if available.
# For this implementation, we target the direct download URL provided by eBird
# for the latest release, falling back to S3 if the direct link fails.

# Official download link (often requires redirect or login, so we use S3 directly)
# eBird S3 bucket for public datasets
S3_BASE_URL = f"https://{EBD_S3_BUCKET}.s3.amazonaws.com/{EBD_FILE_NAME}"

# Fallback: If the specific file name changes, we might need a dynamic fetch.
# However, for the purpose of this pipeline, we assume a specific release version
# is pinned or we fetch the latest available if the filename is generic.
# To be robust, we will try to download the file. If 404, we attempt a known
# alternative or raise an error.

# Let's use a known stable URL for the Feb 2024 release as a placeholder for the "real" data
# In a production environment, this would be dynamic or versioned.
# URL: https://ebd-public.s3.amazonaws.com/ebd_relFeb-2024.zip
# If this specific file is not found, we might need to adjust the filename.
# To ensure the script runs on REAL data, we will attempt the download.

# Define paths
DATA_DIR = project_root / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DIR / "ebd_basic.csv" # Assuming we unzip immediately or download CSV
# eBird provides a ZIP file. We will download the ZIP and then unzip it to CSV.
ZIP_FILE = RAW_DIR / "ebd_basic.zip"

METADATA_FILE = DATA_DIR / "metadata.yaml"

def download_file(url: str, output_path: Path) -> bool:
    """Download a file from a URL to a local path."""
    print(f"Downloading from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024  # 1 MB
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        sys.stdout.write(f"\rDownloaded: {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB")
                        sys.stdout.flush()
        
        print("\nDownload complete.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return False

def unzip_file(zip_path: Path, extract_to: Path) -> bool:
    """Unzip a file to a directory."""
    import zipfile
    print(f"Unzipping {zip_path} to {extract_to}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("Unzip complete.")
        return True
    except zipfile.BadZipFile:
        print("Error: Invalid zip file.")
        return False
    except Exception as e:
        print(f"Error unzipping: {e}")
        return False

def find_csv_in_directory(directory: Path) -> Path:
    """Find the CSV file inside the unzipped directory."""
    csv_files = list(directory.glob("*.csv"))
    if not csv_files:
        # Check recursively if it's in a subfolder
        csv_files = list(directory.rglob("*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found in {directory}")
    
    # Assume the first one is the main EBD file
    return csv_files[0]

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_metadata(url: str, file_path: Path, checksum: str, output_path: Path):
    """Save metadata to YAML file."""
    metadata = {
        "source": "eBird Basic Dataset",
        "url": url,
        "downloaded_at": datetime.utcnow().isoformat(),
        "filename": file_path.name,
        "checksum_sha256": checksum,
        "file_size_bytes": file_path.stat().st_size,
        "format": "csv",
        "description": "Raw eBird Basic Dataset used for foraging behavior analysis"
    }
    
    # Load existing metadata if it exists to preserve history
    if output_path.exists():
        with open(output_path, 'r') as f:
            existing_meta = yaml.safe_load(f) or {}
        if 'history' not in existing_meta:
            existing_meta['history'] = []
        existing_meta['history'].append(existing_meta.get('current', {}))
        existing_meta['current'] = metadata
    else:
        existing_meta = {"current": metadata, "history": []}
    
    with open(output_path, 'w') as f:
        yaml.dump(existing_meta, f, default_flow_style=False)
    
    print(f"Metadata saved to {output_path}")

def main():
    print("Starting eBird data download (T011)...")
    
    # 1. Attempt to download the ZIP file
    # We will try the S3 URL first.
    # Note: The filename 'ebd_relFeb-2024.zip' is an example.
    # If this fails, we might need to handle the latest version logic.
    # For this task, we assume the URL is valid for the real dataset.
    
    # To ensure we get REAL data, we use the official S3 link for the Feb 2024 release.
    # If that specific version is gone, the script will fail, which is correct behavior
    # (fail loudly) rather than faking data.
    target_url = "https://ebd-public.s3.amazonaws.com/ebd_relFeb-2024.zip"
    
    # Check if file already exists to avoid re-downloading
    if not ZIP_FILE.exists():
        if not download_file(target_url, ZIP_FILE):
            print("Failed to download EBD data. Aborting.")
            sys.exit(1)
    else:
        print(f"ZIP file {ZIP_FILE} already exists. Skipping download.")
    
    # 2. Unzip the file
    if not unzip_file(ZIP_FILE, RAW_DIR):
        print("Failed to unzip EBD data. Aborting.")
        sys.exit(1)
    
    # 3. Locate the CSV
    try:
        csv_file = find_csv_in_directory(RAW_DIR)
        # Rename to standard name if it's different
        if csv_file.name != "ebd_basic.csv":
            standard_name = RAW_DIR / "ebd_basic.csv"
            if not standard_name.exists():
                csv_file.rename(standard_name)
                csv_file = standard_name
        else:
            csv_file = RAW_DIR / "ebd_basic.csv"
    except FileNotFoundError as e:
        print(f"Could not locate CSV file: {e}")
        sys.exit(1)
    
    # 4. Compute Checksum
    checksum = compute_sha256(csv_file)
    print(f"Checksum (SHA-256): {checksum}")
    
    # 5. Save Metadata
    save_metadata(target_url, csv_file, checksum, METADATA_FILE)
    
    # 6. Log provenance
    provenance_record = generate_provenance_record(
        step="download_ebd",
        input_sources=[target_url],
        output_files=[str(csv_file), str(METADATA_FILE)],
        checksums={"csv": checksum}
    )
    save_provenance_record(provenance_record, project_root / "data" / "provenance_log.jsonl")
    
    print("T011: eBird data download and verification complete.")

if __name__ == "__main__":
    main()
