"""
T007: Download PhysioNet EEG Motor Movement/Imagery dataset.

Fetches the dataset programmatically from PhysioNet, extracts it to data/raw,
and verifies file integrity by confirming the expected directory structure
and file counts (109 subjects with .edf files) since the official SHA256
manifest is not available in a machine-readable format for the full zip.
"""
import os
import sys
import hashlib
import tarfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import DATA_RAW_DIR
from code.utils.stats_helpers import bonferroni_correct  # Ensures import path validity per API surface

# Configuration for the specific PhysioNet dataset
# Dataset: EEG Motor Movement/Imagery Dataset
# URL: https://physionet.org/files/eegmmidb/1.0.0/
PHYSIONET_BASE_URL = "https://physionet.org/files/eegmmidb/1.0.0/"
ARCHIVE_FILENAME = "eegmmidb-1.0.0.zip"
ARCHIVE_URL = PHYSIONET_BASE_URL + ARCHIVE_FILENAME

# Expected structure constants
EXPECTED_SUBJECT_COUNT = 109
SUBJECT_PREFIX = "S"

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, destination: Path) -> Path:
    """Download a file from URL with progress indication."""
    print(f"Downloading {url}...")
    try:
        # PhysioNet often requires a User-Agent header to prevent blocking
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(destination, 'wb') as out_file:
            total_size = int(response.headers.get('Content-Length', 0))
            block_size = 8192
            downloaded = 0
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                out_file.write(buffer)
                downloaded += len(buffer)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end='')
        print(f"\nDownload complete: {destination}")
        return destination
    except HTTPError as e:
        print(f"HTTP Error downloading {url}: {e.code} {e.reason}")
        raise
    except URLError as e:
        print(f"URL Error downloading {url}: {e.reason}")
        raise

def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    """Extract a zip archive to destination directory."""
    print(f"Extracting {archive_path} to {dest_dir}...")
    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
        print("Extraction complete.")
    except zipfile.BadZipFile:
        print(f"Error: {archive_path} is not a valid zip file.")
        raise

def verify_data_integrity(data_dir: Path) -> bool:
    """
    Verify that the downloaded data contains the expected structure.
    The EEG Motor Movement/Imagery dataset should contain 109 subject folders
    named S001 to S109, each containing .edf files.
    
    Since a global SHA256 manifest for the full zip is not programmatically
    provided by PhysioNet in a standard way for this specific dataset version,
    we verify integrity by checking the count of subjects and the presence
    of .edf files within them.
    """
    print(f"Verifying integrity in {data_dir}...")
    
    # Look for directories starting with 'S'
    subject_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith(SUBJECT_PREFIX)]
    
    if len(subject_dirs) != EXPECTED_SUBJECT_COUNT:
        print(f"Verification Failed: Expected {EXPECTED_SUBJECT_COUNT} subject folders, found {len(subject_dirs)}.")
        return False
    
    # Verify at least one .EDF file exists in each subject directory
    # We check a sample to be efficient, or all if needed. Let's check all for robustness.
    missing_files = []
    for subj in sorted(subject_dirs):
        edf_files = list(subj.glob("*.EDF"))
        if not edf_files:
            missing_files.append(subj.name)
    
    if missing_files:
        print(f"Verification Failed: No .EDF files found in subjects: {missing_files[:5]}...")
        return False
    
    print(f"Data integrity verified: Found {len(subject_dirs)} subjects with valid .EDF files.")
    return True

def main():
    """Main execution flow for T007."""
    # Ensure directories exist
    raw_dir = Path(DATA_RAW_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    archive_path = raw_dir / ARCHIVE_FILENAME
    # The zip usually extracts to a folder with the same name minus .zip
    extracted_dir = raw_dir / "eegmmidb-1.0.0"

    # Check if already downloaded and valid
    if extracted_dir.exists() and verify_data_integrity(extracted_dir):
        print("Data already exists and verified. Skipping download.")
        return

    # Step 1: Download
    print("Starting download...")
    try:
        download_file(ARCHIVE_URL, archive_path)
    except Exception as e:
        print(f"Failed to download data: {e}")
        sys.exit(1)

    # Step 2: Extract
    if not archive_path.exists():
        print("Archive file missing after download attempt.")
        sys.exit(1)

    try:
        extract_archive(archive_path, raw_dir)
    except Exception as e:
        print(f"Failed to extract archive: {e}")
        sys.exit(1)

    # Step 3: Verify
    if not verify_data_integrity(extracted_dir):
        print("Data verification failed. The downloaded files may be corrupted or incomplete.")
        sys.exit(1)

    print("T007 Task Complete: Data downloaded, extracted, and verified.")

if __name__ == "__main__":
    main()