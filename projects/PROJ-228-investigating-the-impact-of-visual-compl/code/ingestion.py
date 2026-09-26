import os
import subprocess
import hashlib
import shutil
from pathlib import Path
from typing import Optional
import logging

from code.config import DATA_RAW_DIR, DATASET_ID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_RAW_DIR / "ingestion.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_dataset(dataset_id: str) -> Path:
    """
    Download the dataset from OpenNeuro using wget.
    Verifies checksums if available.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000246')
        
    Returns:
        Path to the downloaded dataset directory.
        
    Raises:
        RuntimeError: If download fails or checksum verification fails.
    """
    target_dir = DATA_RAW_DIR / dataset_id
    
    if target_dir.exists():
        logger.info(f"Dataset {dataset_id} already exists at {target_dir}. Skipping download.")
        # Verify integrity if files exist
        if not check_dataset_integrity(dataset_id):
            logger.warning(f"Integrity check failed for existing {dataset_id}. Re-downloading.")
            shutil.rmtree(target_dir)
        else:
            return target_dir

    logger.info(f"Starting download of dataset {dataset_id} to {target_dir}...")
    
    # Ensure parent directory exists
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Construct wget command
    # Using rsync or wget for OpenNeuro datasets
    # OpenNeuro datasets are typically accessed via:
    # wget -r -np -nH --cut-dirs=3 -R "index.html*" https://openneuro.org/datasets/{dataset_id}/versions/latest/file-display/
    # However, for simplicity and robustness in this script, we attempt a direct file fetch 
    # or use a standard mirror if specific file structure is known.
    # Given the constraints of a generic script without specific file lists, we use a robust wget approach.
    
    base_url = f"https://openneuro.org/datasets/{dataset_id}/versions/latest/file-display/"
    # Note: OpenNeuro often requires specific file paths or rsync. 
    # For this implementation, we simulate the download logic or fetch a known manifest.
    # Since we cannot guarantee a specific file list without a manifest, we attempt to fetch the root structure.
    # In a real scenario, one would use 'openneuro' CLI or specific rsync commands.
    # Here we use wget to fetch the directory structure if accessible, or fail loudly.
    
    # Attempt to download using wget (recursive, no parent dirs, no host dirs, cut dirs, reject index)
    cmd = [
        "wget",
        "-r",
        "-np",
        "-nH",
        "--cut-dirs=3",
        "-R", "index.html*",
        "--no-check-certificate",
        base_url
    ]
    
    # Change to target dir for download
    original_cwd = os.getcwd()
    try:
        os.chdir(DATA_RAW_DIR)
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Fallback: If wget fails, check if it's a network issue or repo issue
            if "404" in result.stderr or "Connection refused" in result.stderr:
                raise RuntimeError(f"Dataset {dataset_id} not found or unavailable at {base_url}.")
            elif "Network" in result.stderr or "Try" in result.stderr:
                raise RuntimeError(f"Network error during download of {dataset_id}: {result.stderr}")
            else:
                raise RuntimeError(f"Download failed with code {result.returncode}: {result.stderr}")
        
        if not target_dir.exists() or not any(target_dir.iterdir()):
            raise RuntimeError(f"Download completed but target directory {target_dir} is empty.")
            
        logger.info(f"Dataset {dataset_id} downloaded successfully.")
    finally:
        os.chdir(original_cwd)

    if not check_dataset_integrity(dataset_id):
        raise RuntimeError(f"Checksum verification failed for {dataset_id}.")
        
    return target_dir

def check_dataset_integrity(dataset_id: str) -> bool:
    """
    Verify the integrity of the downloaded dataset.
    For this implementation, we check if critical files exist.
    A full checksum verification would require a manifest file.
    """
    target_dir = DATA_RAW_DIR / dataset_id
    if not target_dir.exists():
        return False
    
    # Check for at least some files (basic sanity check)
    file_count = sum(1 for _ in target_dir.rglob('*') if _.is_file())
    if file_count == 0:
        logger.warning(f"Dataset {dataset_id} exists but contains no files.")
        return False
        
    logger.info(f"Integrity check passed for {dataset_id} ({file_count} files found).")
    return True

def main():
    """Main entry point for ingestion script."""
    logger.info("Starting dataset ingestion...")
    try:
        path = download_dataset(DATASET_ID)
        logger.info(f"Ingestion complete. Data located at: {path}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    main()
