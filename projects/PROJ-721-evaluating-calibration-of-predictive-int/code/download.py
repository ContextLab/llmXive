import hashlib
import json
import os
import shutil
import zipfile
import logging
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
M4_GITHUB_OWNER = "M4Comp"
M4_GITHUB_REPO = "M4-Dataset"
M4_GITHUB_BRANCH = "main"
M4_ZIP_FILENAME = "M4-Dataset.zip"
MANIFEST_FILENAME = "manifest.json"
BASE_URL = f"https://raw.githubusercontent.com/{M4_GITHUB_OWNER}/{M4_GITHUB_REPO}/{M4_GITHUB_BRANCH}"
DATA_DIR = Path("data")
TEMP_DIR = Path("data/tmp")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, destination: Path) -> None:
    """Download a file from a URL to a destination path."""
    logger.info(f"Downloading {url} to {destination}")
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise error for bad status
    
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.info(f"Downloaded {destination}")

def load_manifest(manifest_path: Path) -> dict:
    """Load and parse the manifest JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, "r") as f:
        return json.load(f)

def validate_checksums(manifest: dict, data_dir: Path) -> bool:
    """Validate SHA256 checksums of files against the manifest."""
    all_valid = True
    for file_entry in manifest.get("files", []):
        filename = file_entry.get("filename")
        expected_checksum = file_entry.get("sha256")
        
        if not filename or not expected_checksum:
            logger.warning(f"Skipping entry with missing filename or checksum: {file_entry}")
            continue
        
        file_path = data_dir / filename
        if not file_path.exists():
            logger.error(f"File not found for checksum validation: {file_path}")
            all_valid = False
            continue
        
        actual_checksum = calculate_sha256(file_path)
        if actual_checksum != expected_checksum:
            logger.error(f"Checksum mismatch for {filename}: expected {expected_checksum}, got {actual_checksum}")
            all_valid = False
        else:
            logger.info(f"Checksum valid for {filename}")
    
    return all_valid

def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """Extract a zip file to a destination directory."""
    logger.info(f"Extracting {zip_path} to {dest_dir}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(dest_dir)
    logger.info("Extraction complete")

def cleanup_temp_files(temp_dir: Path) -> None:
    """Remove temporary directory and its contents."""
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")

def main() -> None:
    """Main function to fetch M4 dataset, validate checksums, and extract."""
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    zip_url = f"{BASE_URL}/{M4_ZIP_FILENAME}"
    manifest_url = f"{BASE_URL}/{MANIFEST_FILENAME}"
    
    zip_path = DATA_DIR / M4_ZIP_FILENAME
    manifest_path = DATA_DIR / MANIFEST_FILENAME

    try:
        # Download manifest
        download_file(manifest_url, manifest_path)
        
        # Load manifest to get expected checksums
        manifest = load_manifest(manifest_path)
        
        # Check if zip already exists and validate
        if zip_path.exists():
            logger.info(f"Found existing {M4_ZIP_FILENAME}, validating checksum...")
            if validate_checksums(manifest, DATA_DIR):
                logger.info("Existing file checksum valid. Skipping download.")
            else:
                logger.warning("Existing file checksum invalid. Re-downloading.")
                zip_path.unlink()
        
        # Download zip if not present or invalid
        if not zip_path.exists():
            download_file(zip_url, zip_path)
        
        # Final validation of the downloaded zip
        if not validate_checksums(manifest, DATA_DIR):
            raise RuntimeError("Checksum validation failed after download. Aborting.")
        
        # Extract the dataset
        extract_zip(zip_path, DATA_DIR)
        
        logger.info("M4 Dataset successfully fetched and validated.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during download: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during dataset processing: {e}")
        raise

if __name__ == "__main__":
    main()
