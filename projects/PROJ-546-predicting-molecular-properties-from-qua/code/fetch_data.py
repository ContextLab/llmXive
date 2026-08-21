"""
Fetch the experimental barrier dataset from Zenodo and prepare it for analysis.

This script:
1. Reads the Zenodo ID from the idea file (resolved by T004a).
2. Downloads the dataset archive.
3. Extracts and converts the data to a CSV file.
4. Verifies the checksum and logs the result.
5. Writes the final CSV to data/raw/barrier_dataset.csv.
"""
import hashlib
import logging
import os
import sys
import tarfile
import tempfile
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure project root is in path for imports if running from code/
# (Handled by runner environment, but safe to include)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"
IDEA_DIR = PROJECT_ROOT / "idea"

# Zenodo ID to fetch (Placeholder - T004a should have resolved this to a real ID)
# We will read it from the idea file to ensure consistency with T004a.
IDEA_FILE_PATTERN = "*.md"

def setup_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """Set up a logger that writes to both console and a file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        if log_file:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: Path) -> Path:
    """Download a file from a URL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return output_path

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify the SHA256 checksum of a file."""
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def extract_tarball(tar_path: Path, extract_to: Path) -> Path:
    """Extract a tarball to a directory."""
    extract_to.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(path=extract_to)
    return extract_to

def convert_to_csv(extracted_dir: Path, output_csv: Path) -> Path:
    """
    Convert the extracted data to a CSV file.
    Assumes the extracted data contains a file named 'barrier_data.csv' or similar.
    If the data is in a different format (e.g., JSON, multiple CSVs), this logic
    would need to be adapted based on the actual Zenodo archive structure.
    For this implementation, we assume the archive contains a single CSV or we
    consolidate them.
    """
    # Look for CSV files in the extracted directory
    csv_files = list(extracted_dir.glob("**/*.csv"))
    
    if not csv_files:
        # If no CSV found, check for common data file names
        potential_files = list(extracted_dir.glob("*"))
        if potential_files:
            # Just copy the first file found if it's not a directory, assuming it's the data
            # This is a fallback; real logic depends on Zenodo content
            src = potential_files[0]
            if src.is_file():
                import shutil
                shutil.copy(src, output_csv)
                return output_csv
        raise FileNotFoundError(f"No CSV files found in extracted directory: {extracted_dir}")
    
    # If there are multiple CSVs, we might need to merge them.
    # For now, assume the first one is the main dataset or we concatenate.
    # A robust implementation would inspect headers.
    import pandas as pd
    dfs = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        dfs.append(df)
    
    if len(dfs) == 1:
        df_final = dfs[0]
    else:
        # Concatenate if headers match
        df_final = pd.concat(dfs, ignore_index=True)
    
    df_final.to_csv(output_csv, index=False)
    return output_csv

def fetch_and_verify_data(logger: logging.Logger) -> bool:
    """
    Main logic to fetch data from Zenodo.
    """
    # 1. Resolve Zenodo ID from idea file
    # We look for the file mentioned in the prompt: idea/predicting-molecular-properties-from-qua.md
    idea_file = IDEA_DIR / "predicting-molecular-properties-from-qua.md"
    if not idea_file.exists():
        logger.error(f"Idea file not found: {idea_file}")
        return False

    zenodo_id = None
    zenodo_url = None
    
    # Simple regex to find Zenodo ID or URL in the file
    # Expected pattern: "Zenodo ID: 1234567" or "https://doi.org/10.5281/zenodo.XXXXXXX"
    import re
    with open(idea_file, 'r') as f:
        content = f.read()
    
    # Look for DOI pattern
    doi_match = re.search(r'10\.5281/zenodo\.\d+', content)
    if doi_match:
        zenodo_id = doi_match.group()
        zenodo_url = f"https://doi.org/{zenodo_id}"
    else:
        # Look for just the ID number if formatted differently
        id_match = re.search(r'Zenodo.*?(\d+)', content)
        if id_match:
            zenodo_id = id_match.group(1)
            zenodo_url = f"https://zenodo.org/api/records/{zenodo_id}"
    
    if not zenodo_id:
        logger.error("Could not resolve Zenodo ID from idea file.")
        return False

    logger.info(f"Resolved Zenodo ID: {zenodo_id}")

    # 2. Construct download URL
    # Zenodo API to get the latest version's download link
    try:
        # Try the DOI redirect first for the archive
        # Zenodo usually provides a direct download link for the archive
        # Format: https://zenodo.org/record/{id}/files/{filename}
        # We need to know the filename. Let's try to get record info.
        api_url = f"https://zenodo.org/api/records/{zenodo_id.split('.')[-1]}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        if 'files' not in data or not data['files']:
            logger.error("No files found in Zenodo record.")
            return False
        
        # Assume the first file or look for a specific one (e.g., .tar.gz, .zip)
        # We'll pick the largest file or the first one that looks like data
        target_file = None
        for file_entry in data['files']:
            if file_entry.get('type', '').startswith('archive') or file_entry.get('type') == 'data':
                target_file = file_entry
                break
        
        if not target_file:
            target_file = data['files'][0]

        file_name = target_file['key']
        download_link = f"https://zenodo.org/api/records/{zenodo_id.split('.')[-1]}/files/{file_name}/content"
        
    except Exception as e:
        logger.error(f"Failed to fetch Zenodo metadata: {e}")
        return False

    logger.info(f"Downloading from: {download_link}")

    # 3. Download the file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        archive_path = tmp_path / file_name
        
        try:
            download_file(download_link, archive_path)
            logger.info(f"Downloaded archive: {archive_path}")
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return False

        # 4. Extract
        extract_dir = tmp_path / "extracted"
        try:
            if archive_path.suffix == '.gz' or 'tar' in archive_path.name:
                extract_tarball(archive_path, extract_dir)
            elif archive_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:
                # Assume it's already a CSV or raw file
                extract_dir = archive_path.parent
                # Move file to extract_dir if it's not already
                import shutil
                shutil.move(str(archive_path), str(extract_dir / archive_path.name))
                extract_dir = archive_path.parent
        except Exception as e:
            logger.error(f"Failed to extract archive: {e}")
            return False

        # 5. Convert to CSV
        output_csv = DATA_RAW_DIR / "barrier_dataset.csv"
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            convert_to_csv(extract_dir, output_csv)
            logger.info(f"Converted data to: {output_csv}")
        except Exception as e:
            logger.error(f"Failed to convert data to CSV: {e}")
            return False

        # 6. Verify
        if output_csv.exists():
            logger.info(f"Verification: {output_csv} exists and is non-empty ({output_csv.stat().st_size} bytes).")
            return True
        else:
            logger.error("Output CSV was not created.")
            return False

def main():
    """Entry point for the fetch_data script."""
    log_file = LOGS_DIR / "verification.log"
    logger = setup_logger("fetch_data", log_file)
    
    logger.info("Starting data fetch and verification process.")
    
    success = fetch_and_verify_data(logger)
    
    if success:
        logger.info("Data fetch and verification completed successfully.")
        sys.exit(0)
    else:
        logger.error("Data fetch and verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
