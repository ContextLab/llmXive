import hashlib
import json
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

from huggingface_hub import HfApi, hf_hub_download, list_repo_files, snapshot_download
from huggingface_hub.utils import RepositoryNotFoundError, LocalEntryNotFoundError, HFValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
REPO_ID = "nppn/root-phenotyping"
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
DATA_RAW_PATH = Path("data/raw")
CHECKSUM_FILE = DATA_RAW_PATH / "nppn_checksums.json"
IMAGE_OUTPUT_DIR = DATA_RAW_PATH / "nppn_images"


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_existing_checksums() -> Dict[str, str]:
    """Load existing checksums from manifest if it exists."""
    if CHECKSUM_FILE.exists():
        logger.info(f"Loading existing checksums from {CHECKSUM_FILE}")
        with open(CHECKSUM_FILE, "r") as f:
            return json.load(f)
    logger.info("No existing checksum manifest found.")
    return {}


def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to manifest."""
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_FILE, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksums to {CHECKSUM_FILE}")


def get_hf_files_list() -> List[str]:
    """Get list of image files from the HuggingFace repository."""
    try:
        api = HfApi()
        files = list_repo_files(REPO_ID)
        image_files = [f for f in files if Path(f).suffix.lower() in IMAGE_EXTENSIONS]
        logger.info(f"Found {len(image_files)} image files in repository.")
        return image_files
    except (RepositoryNotFoundError, HFValidationError) as e:
        logger.error(f"Failed to access repository: {e}")
        raise RuntimeError("No real NPPN root images found. Pipeline cannot proceed.") from e


def stream_download_files(image_files: List[str], batch_size: int = 100) -> Generator[Path, None, None]:
    """
    Download files in batches and yield their local paths.
    This implements streaming to avoid loading all files into memory at once.
    """
    IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for i in range(0, len(image_files), batch_size):
        batch = image_files[i : i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} files")
        
        for repo_path in batch:
            try:
                # Download file to local cache
                local_path = hf_hub_download(
                    repo_id=REPO_ID,
                    filename=repo_path,
                    cache_dir=str(IMAGE_OUTPUT_DIR)
                )
                yield Path(local_path)
            except Exception as e:
                logger.warning(f"Failed to download {repo_path}: {e}")
                continue


def generate_checksums(image_files: List[Path]) -> Dict[str, str]:
    """Generate SHA256 checksums for a list of image files."""
    checksums = {}
    for file_path in image_files:
        if file_path.exists():
          checksums[file_path.name] = compute_sha256(file_path)
    return checksums


def verify_checksums(downloaded_files: List[Path], existing_checksums: Dict[str, str]) -> bool:
    """
    Verify checksums of downloaded files against the manifest.
    
    Logic:
    1. If no existing manifest, generate one from the downloaded files.
    2. If manifest exists, compare hashes.
    3. If mismatch, HALT with specific error.
    """
    if not downloaded_files:
        raise RuntimeError("No real NPPN root images found. Pipeline cannot proceed.")

    current_checksums = generate_checksums(downloaded_files)
    
    if not existing_checksums:
        logger.info("No existing checksum manifest. Generating new one.")
        save_checksums(current_checksums)
        return True
    
    # Compare
    mismatches = []
    for filename, expected_hash in existing_checksums.items():
        if filename not in current_checksums:
            logger.warning(f"File {filename} from manifest not found in download.")
            mismatches.append(filename)
            continue
        
        actual_hash = current_checksums[filename]
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {filename}: Expected {expected_hash}, Got {actual_hash}")
            mismatches.append(filename)
    
    if mismatches:
        logger.error(f"Data integrity check failed for {len(mismatches)} files.")
        raise RuntimeError("Data integrity check failed for NPPN images.")
    
    logger.info("Data integrity check passed for all images.")
    return True


def main() -> None:
    """Main entry point for downloading and verifying NPPN images."""
    logger.info("Starting NPPN image download and verification pipeline.")
    
    # Ensure directory exists
    DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
    
    # Get file list
    try:
        image_files = get_hf_files_list()
    except RuntimeError:
        logger.error("Repository access failed. Cannot proceed.")
        sys.exit(1)
    
    # Download files (streaming/batched)
    downloaded_paths = list(stream_download_files(image_files))
    
    if not downloaded_paths:
        logger.error("No files were successfully downloaded.")
        sys.exit(1)
    
    # Load existing checksums
    existing_checksums = load_existing_checksums()
    
    # Verify checksums (generates manifest if missing)
    try:
        verify_checksums(downloaded_paths, existing_checksums)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
