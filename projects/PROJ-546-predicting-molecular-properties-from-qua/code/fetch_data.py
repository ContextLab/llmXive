"""
T004b: Fetch the experimental barrier dataset from Zenodo ID 1048765.

This script downloads the dataset, verifies the checksum, and ensures the
raw data file exists at data/raw/barrier_dataset.csv.
"""
import hashlib
import logging
import os
import sys
import tarfile
import tempfile
import requests
from pathlib import Path

# Import Zenodo ID from config (T004a)
import config

# Setup logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "verification.log"

def setup_logger(name: str, log_file: Path) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    return logger

logger = setup_logger("fetch_data", LOG_FILE)

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path, timeout: int = 300) -> Path:
    """Download a file from a URL with progress logging."""
    logger.info(f"Downloading from {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Download complete: {dest_path}")
        return dest_path
    except requests.RequestException as e:
        logger.error(f"Failed to download file: {e}")
        raise

def verify_checksum(filepath: Path, expected_checksum: str = None) -> bool:
    """Verify file checksum if expected_checksum is provided."""
    actual_checksum = compute_sha256(filepath)
    logger.info(f"Computed checksum for {filepath}: {actual_checksum}")
    
    if expected_checksum:
        if actual_checksum.lower() == expected_checksum.lower():
            logger.info("Checksum verification: PASSED")
            return True
        else:
            logger.error(f"Checksum verification: FAILED. Expected {expected_checksum}, got {actual_checksum}")
            return False
    
    logger.warning("No expected checksum provided, skipping verification")
    return True

def extract_tarball(tarball_path: Path, extract_to: Path) -> None:
    """Extract a tarball to a directory."""
    logger.info(f"Extracting {tarball_path} to {extract_to}")
    try:
        with tarfile.open(tarball_path, 'r:gz') as tar:
            tar.extractall(path=extract_to)
        logger.info("Extraction complete")
    except tarfile.TarError as e:
        logger.error(f"Failed to extract tarball: {e}")
        raise

def convert_to_csv(extracted_dir: Path, output_csv: Path) -> Path:
    """
    Locate the CSV file within the extracted directory and copy/move it to output_csv.
    If the archive contains a CSV directly, use it. If nested, find it.
    """
    logger.info(f"Searching for CSV in {extracted_dir}")
    
    csv_files = list(extracted_dir.rglob("*.csv"))
    
    if not csv_files:
        # Check for other extensions that might be the data (e.g., .tsv, .dat) if no CSV found
        # But spec says CSV, so we raise if not found
        raise FileNotFoundError(f"No CSV file found in extracted archive at {extracted_dir}")
    
    # If multiple CSVs, we might need logic, but typically one main dataset
    primary_csv = csv_files[0]
    logger.info(f"Found CSV: {primary_csv}")
    
    # Copy to final destination
    import shutil
    shutil.copy2(primary_csv, output_csv)
    logger.info(f"Copied {primary_csv} to {output_csv}")
    
    return output_csv

def fetch_and_verify_data() -> Path:
    """
    Main logic to fetch data from Zenodo.
    Zenodo API: https://zenodo.org/api/records/{id}/files/{filename}
    We need to find the file associated with the record.
    """
    zenodo_id = config.ZENODO_ID
    if not zenodo_id:
        raise ValueError("ZENODO_ID is not set in config.py. T004a must be completed first.")
    
    logger.info(f"Fetching data for Zenodo ID: {zenodo_id}")
    
    # Construct Zenodo API URL to get record info
    api_url = f"https://zenodo.org/api/records/{zenodo_id}"
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract files info
        files = data.get('files', [])
        if not files:
            # Try 'entries' or 'files' in different structure? Zenodo API v1 usually has 'files'
            # Check if it's 'files' in the 'metadata' or similar
            # Sometimes Zenodo returns 'files' as a list of objects with 'key' and 'links'
            if 'metadata' in data and 'files' in data['metadata']:
                files = data['metadata']['files']
            else:
                raise ValueError(f"No files found in Zenodo record {zenodo_id}")
        
        # Identify the tarball or zip file
        # Usually there's one main archive
        archive_file = None
        for f in files:
            key = f.get('key', '')
            if key.endswith(('.tar.gz', '.tgz', '.zip')):
                archive_file = f
                break
        
        if not archive_file:
            # Fallback: take the first file if it looks like data
            if files:
                archive_file = files[0]
            else:
                raise ValueError("No archive or data file found in Zenodo record")
        
        file_key = archive_file['key']
        # Download link
        download_link = archive_file['links']['self']
        
        # Determine expected checksum if available
        expected_checksum = archive_file.get('checksum', '').replace('sha256:', '')
        
        # Create temp directory for download
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            archive_path = tmp_path / file_key
            extract_dir = tmp_path / "extracted"
            extract_dir.mkdir()
            
            # Download
            download_file(download_link, archive_path)
            
            # Verify checksum if available
            if expected_checksum:
                if not verify_checksum(archive_path, expected_checksum):
                    raise RuntimeError("Checksum verification failed. Aborting.")
            
            # Extract
            if archive_path.suffix == '.gz' or file_key.endswith('.tar.gz'):
                extract_tarball(archive_path, extract_dir)
            elif archive_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:
                # Assume it's the CSV itself or a folder
                # If it's a single file, just move it
                if archive_path.suffix == '.csv':
                    shutil.move(str(archive_path), str(extract_dir / archive_path.name))
                else:
                    # Try to treat as archive anyway or error
                    raise ValueError(f"Unknown archive type: {archive_path}")
            
            # Convert/Move to final CSV location
            output_dir = Path("data/raw")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_csv = output_dir / "barrier_dataset.csv"
            
            final_path = convert_to_csv(extract_dir, output_csv)
            
            logger.info(f"Data successfully fetched and verified: {final_path}")
            return final_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch record info from Zenodo: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during fetch and verify: {e}")
        raise

def main():
    """Entry point for T004b."""
    try:
        output_path = fetch_and_verify_data()
        if output_path.exists():
            logger.info(f"Verification PASSED: File {output_path} exists.")
            print(f"SUCCESS: Data fetched to {output_path}")
            sys.exit(0)
        else:
            logger.error(f"Verification FAILED: File {output_path} does not exist.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline halted: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()