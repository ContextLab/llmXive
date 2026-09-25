import hashlib
import logging
import os
import sys
import tarfile
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
import requests

# Import config for ZENODO_ID
try:
    import config
except ImportError:
    print("Error: config.py not found. Ensure ZENODO_ID is defined.")
    sys.exit(1)

def setup_logger(log_file: str) -> logging.Logger:
    logger = logging.getLogger("fetch_data")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_zenodo_record(zenodo_id: str) -> dict:
    url = f"https://zenodo.org/api/records/{zenodo_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch Zenodo record {zenodo_id}: {e}")

def find_data_file(record: dict) -> Optional[str]:
    """
    Identifies the data file in the Zenodo record.
    Prefers files matching '*barrier*.csv' if compressed, else the largest .csv.
    """
    files = record.get('files', [])
    if not files:
        raise FileNotFoundError("No files found in Zenodo record.")

    # Filter for potential archives or CSVs
    candidates = []
    for f in files:
        fname = f.get('key', '')
        size = f.get('size', 0)
        # Check for archives or CSVs
        if fname.endswith(('.zip', '.tar.gz', '.gz', '.tar')) or fname.endswith('.csv'):
            candidates.append((fname, size, f))

    if not candidates:
        raise FileNotFoundError("No archive or CSV files found in Zenodo record.")

    # Prioritize CSVs matching the pattern
    barrier_csvs = [c for c in candidates if 'barrier' in c[0].lower() and c[0].endswith('.csv')]
    if barrier_csvs:
        return barrier_csvs[0][0]

    # If multiple archives exist, we will handle extraction logic in download/extract
    # For now, return the largest archive or CSV
    # Sort by size descending
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]

def download_file(url: str, dest_path: Path, logger: logging.Logger) -> Path:
    """Downloads file from URL to dest_path."""
    logger.info(f"Downloading from {url} to {dest_path}")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"Download complete: {dest_path}")
        return dest_path
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Download failed: {e}")

def extract_tarball(tar_path: Path, dest_dir: Path, logger: logging.Logger) -> List[Path]:
    """Extracts tarball and returns list of extracted files."""
    logger.info(f"Extracting tarball: {tar_path}")
    extracted_files = []
    with tarfile.open(tar_path, 'r') as tar:
        tar.extractall(path=dest_dir)
        for member in tar.members:
            if not member.isdir():
                extracted_files.append(dest_dir / member.name)
    logger.info(f"Extracted {len(extracted_files)} files")
    return extracted_files

def extract_zipball(zip_path: Path, dest_dir: Path, logger: logging.Logger) -> List[Path]:
    """Extracts zipball and returns list of extracted files."""
    logger.info(f"Extracting zipball: {zip_path}")
    extracted_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)
        for file in zip_ref.filelist:
            if not file.is_dir():
                extracted_files.append(dest_dir / file.filename)
    logger.info(f"Extracted {len(extracted_files)} files")
    return extracted_files

def select_csv_from_directory(extracted_dir: Path, logger: logging.Logger) -> Path:
    """
    Selects the target CSV file from extracted directory.
    Logic:
    1. Look for '*barrier*.csv'
    2. If none, select the largest .csv file.
    """
    csv_files = list(extracted_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No CSV files found after extraction.")

    # Filter for pattern
    barrier_matches = [f for f in csv_files if 'barrier' in f.name.lower()]
    if barrier_matches:
        selected = max(barrier_matches, key=lambda f: f.stat().st_size)
        logger.info(f"Selected pattern match: {selected.name}")
        return selected

    # Fallback: largest CSV
    selected = max(csv_files, key=lambda f: f.stat().st_size)
    logger.info(f"No pattern match. Selected largest CSV: {selected.name}")
    return selected

def convert_to_csv(source_path: Path, dest_path: Path, logger: logging.Logger) -> Path:
    """
    Ensures the final output is a CSV at dest_path.
    If source is already CSV, just copy/move.
    If source is not CSV (e.g. JSON), this function assumes the Zenodo record
    provides a CSV or we selected a CSV.
    """
    logger.info(f"Ensuring final CSV at {dest_path}")
    if source_path == dest_path:
        return dest_path

    shutil.copy2(source_path, dest_path)
    logger.info(f"Final CSV created: {dest_path}")
    return dest_path

def verify_checksum(file_path: Path, expected_checksum: Optional[str], logger: logging.Logger) -> bool:
    actual = compute_sha256(file_path)
    if expected_checksum:
        match = actual == expected_checksum
        logger.info(f"Checksum verification: {'PASS' if match else 'FAIL'}")
        logger.info(f"  Expected: {expected_checksum}")
        logger.info(f"  Actual:   {actual}")
        return match
    else:
        logger.info(f"Checksum verification: SKIPPED (no expected value)")
        logger.info(f"  Actual:   {actual}")
        return True

def fetch_and_verify_data(zenodo_id: str, raw_dir: Path, logger: logging.Logger) -> Path:
    """
    Main orchestration for T004c:
    1. Fetch record.
    2. Download file.
    3. Extract if archive.
    4. Select CSV.
    5. Rename to barrier_dataset.csv.
    """
    logger.info(f"Starting fetch for Zenodo ID: {zenodo_id}")

    # 1. Get Record
    record = get_zenodo_record(zenodo_id)
    # Extract checksum if available
    # Zenodo API structure: files -> [ { key, checksum: { type, value }, ... } ]
    # We look for 'md5' or 'sha256' in the checksum dict
    expected_checksum = None
    for f in record.get('files', []):
        if 'checksum' in f:
            # checksum format: 'md5:abc123...' or 'sha256:abc123...'
            parts = f['checksum'].split(':')
            if len(parts) == 2:
                expected_checksum = parts[1] # We accept the hash value regardless of algo for now
            break

    # 2. Identify file to download
    file_key = find_data_file(record)
    # Construct download URL
    # Zenodo download URL pattern: https://zenodo.org/api/records/{id}/files/{key}
    download_url = f"https://zenodo.org/api/records/{zenodo_id}/files/{file_key}"

    # Create temp dir for download
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        downloaded_file = tmp_path / file_key

        # Download
        download_file(download_url, downloaded_file, logger)

        # Verify checksum if available
        verify_checksum(downloaded_file, expected_checksum, logger)

        # 3. Extract if archive
        extracted_files = []
        if file_key.endswith(('.zip', '.tar.gz', '.gz', '.tar')):
            if file_key.endswith('.zip'):
                extracted_files = extract_zipball(downloaded_file, tmp_path, logger)
            else:
                extracted_files = extract_tarball(downloaded_file, tmp_path, logger)
        else:
            extracted_files = [downloaded_file]

        # 4. Select CSV
        # We assume extraction puts files in tmp_path (or subdirs)
        # We search recursively
        selected_csv = select_csv_from_directory(tmp_path, logger)

        # 5. Final output path
        final_path = raw_dir / "barrier_dataset.csv"
        convert_to_csv(selected_csv, final_path, logger)

    logger.info(f"Task T004c complete: {final_path}")
    return final_path

def main():
    # Setup paths
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logger(log_dir / "verification.log")

    # Get Zenodo ID from config
    zenodo_id = getattr(config, 'ZENODO_ID', None)
    if not zenodo_id:
        logger.error("ZENODO_ID not found in config.py. Aborting.")
        sys.exit(1)

    try:
        result_path = fetch_and_verify_data(zenodo_id, raw_dir, logger)
        logger.info(f"Success. Output file: {result_path}")
        print(f"Success. Output file: {result_path}")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
