import hashlib
import json
import os
import shutil
import zipfile
import logging
from pathlib import Path
from typing import Dict, Optional
import urllib.request
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REPO_OWNER = "monash-university"
REPO_NAME = "M4-Competiton"
RELEASE_TAG = "v1.0"
ASSET_NAME = "M4-Dataset.zip"
MANIFEST_NAME = "manifest.json"

# Official GitHub release URL for M4 dataset
BASE_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{RELEASE_TAG}"
DATASET_URL = f"{BASE_URL}/{ASSET_NAME}"
MANIFEST_URL = f"{BASE_URL}/{MANIFEST_NAME}"

# Output paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEMP_DIR = PROJECT_ROOT / "data" / ".temp"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hex digest of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: Path) -> None:
    """Download a file from a URL with progress logging.
    
    Args:
        url: URL to download from
        output_path: Path where file should be saved
        
    Raises:
        RuntimeError: If download fails
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {url} to {output_path}")
    
    try:
        # Use urllib for download (no external dependencies)
        urllib.request.urlretrieve(url, output_path)
        
        if not output_path.exists():
            raise RuntimeError(f"Download failed: {output_path} does not exist")
            
        file_size = output_path.stat().st_size
        logger.info(f"Downloaded {output_path.name}: {file_size:,} bytes")
        
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {str(e)}")

def load_manifest(manifest_path: Path) -> Dict:
    """Load and parse the manifest.json file.
    
    Args:
        manifest_path: Path to manifest.json
        
    Returns:
        Dictionary containing manifest data
        
    Raises:
        FileNotFoundError: If manifest doesn't exist
        json.JSONDecodeError: If manifest is invalid JSON
    """
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    return manifest

def validate_checksums(manifest: Dict, data_dir: Path) -> bool:
    """Validate SHA256 checksums of downloaded files against manifest.
    
    Args:
        manifest: Manifest dictionary with file checksums
        data_dir: Directory containing the downloaded files
        
    Returns:
        True if all checksums match, False otherwise
        
    Raises:
        FileNotFoundError: If any file in manifest is missing
    """
    all_valid = True
    
    for file_info in manifest.get('files', []):
        filename = file_info.get('filename')
        expected_hash = file_info.get('sha256')
        
        if not filename or not expected_hash:
            logger.warning(f"Skipping invalid manifest entry: {file_info}")
            continue
            
        file_path = data_dir / filename
        
        if not file_path.exists():
            logger.error(f"Missing file: {filename}")
            all_valid = False
            continue
            
        actual_hash = calculate_sha256(file_path)
        
        if actual_hash.lower() == expected_hash.lower():
            logger.info(f"✓ {filename}: Checksum valid")
        else:
            logger.error(f"✗ {filename}: Checksum mismatch")
            logger.error(f"  Expected: {expected_hash}")
            logger.error(f"  Actual:   {actual_hash}")
            all_valid = False
            
    return all_valid

def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract a ZIP file to a directory.
    
    Args:
        zip_path: Path to ZIP file
        extract_to: Directory to extract contents to
        
    Raises:
        zipfile.BadZipFile: If ZIP file is corrupted
    """
    extract_to.mkdir(parents=True, exist_ok=True)
    logger.info(f"Extracting {zip_path.name} to {extract_to}")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        
    logger.info(f"Extraction complete: {extract_to}")

def cleanup_temp_files(temp_dir: Path) -> None:
    """Remove temporary directory and its contents.
    
    Args:
        temp_dir: Path to temporary directory to remove
    """
    if temp_dir.exists():
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)
    else:
        logger.debug(f"Temporary directory does not exist: {temp_dir}")

def main() -> bool:
    """Main function to download, validate, and extract M4 dataset.
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Starting M4 dataset download and validation")
    
    # Create necessary directories
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    dataset_zip = DATA_DIR / ASSET_NAME
    manifest_file = DATA_DIR / MANIFEST_NAME
    extracted_dir = DATA_DIR / "M4-Dataset"
    
    try:
        # Step 1: Download manifest
        logger.info("Step 1: Downloading manifest...")
        download_file(MANIFEST_URL, manifest_file)
        
        # Step 2: Load manifest
        logger.info("Step 2: Loading manifest...")
        manifest = load_manifest(manifest_file)
        
        # Step 3: Download dataset if not already present
        if not dataset_zip.exists():
            logger.info("Step 3: Downloading M4 dataset...")
            download_file(DATASET_URL, dataset_zip)
        else:
            logger.info("Step 3: Dataset already exists, skipping download")
        
        # Step 4: Validate checksums
        logger.info("Step 4: Validating checksums...")
        if not validate_checksums(manifest, DATA_DIR):
            logger.error("Checksum validation failed!")
            return False
        
        # Step 5: Extract dataset
        logger.info("Step 5: Extracting dataset...")
        extract_zip(dataset_zip, extracted_dir)
        
        # Step 6: Cleanup (optional - keep zip for reproducibility)
        # cleanup_temp_files(TEMP_DIR)
        
        logger.info("M4 dataset download and validation completed successfully!")
        logger.info(f"Dataset location: {extracted_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process M4 dataset: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
