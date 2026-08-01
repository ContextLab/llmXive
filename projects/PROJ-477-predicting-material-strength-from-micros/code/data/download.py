"""
Data Downloader for Material Strength Prediction Project.

This script fetches the verified public dataset 'Rxzh/ebsd-synthetic' from HuggingFace.
It strictly validates the downloaded content against a SHA256 hash defined in config.yaml.
It raises FileNotFoundError if the dataset is missing, checksum fails, or hash is undefined.
"""

import os
import sys
import hashlib
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path to allow imports from utils
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.config import get_project_root, get_raw_dir, get_results_dir, get_code_dir
except ImportError:
    # Fallback for direct execution or different environment setups
    def get_project_root():
        root = Path(__file__).parent.parent.parent
        if not (root / "code" / "data").exists():
            raise FileNotFoundError("Could not determine project root. Expected 'code' and 'data' directories.")
        return root
    
    def get_raw_dir():
        return get_project_root() / "data" / "raw"
    
    def get_results_dir():
        return get_project_root() / "results"
    
    def get_code_dir():
        return get_project_root() / "code"

def setup_download_logging():
    """Initialize logging for the download process."""
    logger = logging.getLogger("download")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler for results
        results_dir = get_results_dir()
        results_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(results_dir / "download.log")
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_config_hash() -> str:
    """Load the expected SHA256 hash from code/config.yaml."""
    config_path = get_code_dir() / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}. Please ensure code/config.yaml exists.")
    
    # Simple YAML parsing (assuming no complex nested structures for this specific field)
    # Using standard library to avoid dependency on pyyaml if not strictly necessary, 
    # but since requirements.txt includes it, we can try to import it.
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except ImportError:
        # Fallback manual parsing if yaml is not installed (should not happen per requirements)
        config = {}
        with open(config_path, 'r') as f:
            for line in f:
                if 'sha256' in line and ':' in line:
                    val = line.split(':')[1].strip().strip('"').strip("'")
                    config['dataset'] = {'sha256': val}
    
    if 'dataset' not in config or 'sha256' not in config['dataset']:
        raise ValueError("SHA256 hash is undefined in config.yaml under 'dataset'. Please populate this field.")
    
    expected_hash = config['dataset']['sha256']
    if expected_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855":
        # This is the hash of an empty string, indicating it hasn't been set yet.
        # In a real scenario, this should be the hash of the actual dataset archive.
        # For the purpose of this task, we assume the user has updated it, 
        # but we will raise an error if it's still the placeholder to prevent accidental passes.
        raise ValueError("SHA256 hash in config.yaml is still the placeholder value. Please update with the real dataset hash.")
    
    return expected_hash

def download_and_prepare(logger: logging.Logger) -> None:
    """
    Fetch the dataset from HuggingFace and verify integrity.
    
    The dataset 'Rxzh/ebsd-synthetic' is downloaded. Since the task requires 
    fetching the REAL source and failing loudly if it doesn't match, we use 
    the huggingface_hub library.
    """
    from huggingface_hub import snapshot_download, hf_hub_download
    
    dataset_name = "Rxzh/ebsd-synthetic"
    raw_dir = get_raw_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download of dataset: {dataset_name}")
    logger.info(f"Target directory: {raw_dir}")
    
    # Check if dataset is already downloaded to avoid re-downloading
    # We look for a marker file or specific expected file structure.
    # Since the dataset structure might vary, we check for a common artifact like 'dataset_info.json' or the root folder.
    # However, to be safe and ensure integrity, we will re-download if the hash doesn't match.
    # For simplicity in this script, we assume the download goes to a specific subfolder or we extract it.
    
    try:
        # Download the entire dataset snapshot
        # revision="main" is default
        local_dir = raw_dir / dataset_name.split('/')[-1] # e.g., data/raw/ebsd-synthetic
        local_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloading snapshot to {local_dir}...")
        snapshot_download(
            repo_id=dataset_name,
            repo_type="dataset",
            local_dir=str(local_dir),
            local_dir_use_symlinks=False
        )
        
        # Calculate hash of the downloaded directory (we hash all files combined or a specific archive)
        # Since snapshot_download might give a folder of files, we need a consistent way to hash.
        # If the dataset is a single zip, we hash the zip. If it's a folder of images, we hash the folder content.
        # For 'Rxzh/ebsd-synthetic', let's assume it might be a zip or a folder.
        # We will calculate the hash of the entire directory tree by sorting files and hashing their content.
        
        def hash_directory(dir_path: Path) -> str:
            sha256_hash = hashlib.sha256()
            files = sorted(dir_path.rglob("*"))
            for file in files:
                if file.is_file():
                    with open(file, "rb") as f:
                        for byte_block in iter(lambda: f.read(4096), b""):
                            sha256_hash.update(byte_block)
                            sha256_hash.update(b"") # Separator not strictly needed if order is fixed
            return sha256_hash.hexdigest()
        
        actual_hash = hash_directory(local_dir)
        expected_hash = load_config_hash()
        
        if actual_hash != expected_hash:
            error_msg = (
                f"Checksum verification failed!\n"
                f"Expected: {expected_hash}\n"
                f"Actual:   {actual_hash}\n"
                f"Dataset:  {dataset_name}"
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info("Checksum verification successful.")
        
        # If the download resulted in a zip file, extract it to the raw_dir root or keep structure
        # The task says: Output: data/raw/ with original zip/images.
        # If the download created a subfolder, we might want to move contents up if it's a single zip.
        # But usually, keeping the repo name folder is safer for integrity.
        # We will log the structure.
        logger.info(f"Dataset downloaded and verified to: {local_dir}")
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise

def main():
    """Main entry point for the download script."""
    logger = setup_download_logging()
    try:
        download_and_prepare(logger)
        logger.info("Data download and verification completed successfully.")
    except FileNotFoundError as e:
        logger.critical(f"CRITICAL FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()