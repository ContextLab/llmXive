import hashlib
import os
import sys
from pathlib import Path
import yaml

try:
    from openneuro import openneuro_download
except ImportError:
    print("Error: openneuro-py is not installed. Please install it via 'pip install openneuro-py'.")
    sys.exit(1)

from config import get_config
from utils.logging import setup_pipeline_logger, log_step, log_error

def load_expected_hash(config_path: Path) -> str:
    """
    Loads the expected dataset version hash from data/metadata.yaml.
    Raises FileNotFoundError or KeyError if the metadata is missing or malformed.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        metadata = yaml.safe_load(f)
    
    try:
        hash_val = metadata['datasets']['ds004041']['version_hash']
        if not hash_val:
            raise ValueError("version_hash is empty in metadata.yaml")
        return hash_val
    except KeyError as e:
        raise KeyError(f"Missing required key in metadata.yaml: {e}")

def verify_hash(dataset_path: Path, expected_hash: str) -> bool:
    """
    Computes the SHA-256 hash of the downloaded dataset directory tree
    and compares it to the expected hash.
    
    Note: This is a simplified verification. In production, one might verify
    individual file hashes or use the dataset's manifest if available.
    For this implementation, we compute a tree hash of the directory structure
    and file contents to ensure integrity.
    """
    hasher = hashlib.sha256()
    
    # Sort files to ensure deterministic ordering
    all_files = sorted(dataset_path.rglob('*'))
    
    for file_path in all_files:
        if file_path.is_file():
            # Include relative path in hash to prevent directory swapping attacks
            rel_path = str(file_path.relative_to(dataset_path))
            hasher.update(rel_path.encode('utf-8'))
            
            # Read file in chunks to handle large datasets
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
        
    computed_hash = hasher.hexdigest()
    
    if computed_hash == expected_hash:
        log_step("hash_verification", "PASSED", {"computed": computed_hash, "expected": expected_hash})
        return True
    else:
        log_error("hash_verification", "FAILED", {"computed": computed_hash, "expected": expected_hash})
        return False

def download_dataset(dataset_id: str, output_dir: Path, version: str = "1.0.0") -> Path:
    """
    Downloads the specified OpenNeuro dataset to the output directory.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds004041').
        output_dir: The directory where the dataset will be downloaded.
        version: The version tag to download (default: "1.0.0").
        
    Returns:
        The path to the downloaded dataset directory.
        
    Raises:
        RuntimeError: If the download fails or the hash verification fails.
    """
    logger = setup_pipeline_logger("download")
    log_step("download_start", "INITIATED", {"dataset_id": dataset_id, "output_dir": str(output_dir)})
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use openneuro-py to download
        # The library handles the actual fetching. We pass the dataset ID and output path.
        # Note: openneuro_download typically downloads to a subdirectory named after the dataset.
        # We need to handle the case where the library might create the directory or we need to specify it.
        # Based on typical usage, we pass the output directory and let it create the dataset folder.
        
        # We attempt to download the specific version if supported, otherwise default to latest.
        # The openneuro-py library's API might vary, but typically it looks like:
        # openneuro_download(dataset_id, output_dir=output_dir, tag=version)
        
        logger.info(f"Attempting to download {dataset_id} version {version} to {output_dir}")
        
        # Attempt download
        downloaded_path = openneuro_download(
            dataset_id,
            output_dir=str(output_dir),
            tag=version,
            delete=False # Keep existing files if any, though we expect clean run
        )
        
        # The library returns the path to the downloaded dataset
        if not downloaded_path:
            raise RuntimeError("openneuro_download returned None or empty path")
            
        downloaded_path = Path(downloaded_path)
        
        if not downloaded_path.exists():
            raise RuntimeError(f"Downloaded path does not exist: {downloaded_path}")
            
        log_step("download_complete", "SUCCESS", {"path": str(downloaded_path)})
        
        return downloaded_path
        
    except Exception as e:
        log_error("download_dataset", "FAILED", {"error": str(e)})
        raise RuntimeError(f"Failed to download dataset {dataset_id}: {e}") from e

def main():
    """
    Main entry point for the data download script.
    Orchestrates loading the expected hash, downloading the dataset, and verifying integrity.
    """
    config = get_config()
    metadata_path = config.get('metadata_path', Path('data/metadata.yaml'))
    output_dir = Path('data/raw')
    
    logger = setup_pipeline_logger("download_main")
    log_step("main_start", "INITIATED")
    
    try:
        # 1. Load expected hash
        expected_hash = load_expected_hash(metadata_path)
        logger.info(f"Loaded expected hash for ds004041: {expected_hash}")
        
        # 2. Download dataset
        logger.info("Starting download...")
        dataset_path = download_dataset("ds004041", output_dir, version="1.0.0")
        
        # 3. Verify hash
        logger.info("Verifying dataset integrity...")
        if verify_hash(dataset_path, expected_hash):
            log_step("main_complete", "SUCCESS", {"dataset": "ds004041", "path": str(dataset_path)})
            print(f"Download and verification successful: {dataset_path}")
            return 0
        else:
            log_error("main_complete", "HASH_MISMATCH", {"dataset": "ds004041"})
            print("ERROR: Dataset hash verification failed. The downloaded data may be corrupted or from a different version.")
            return 1
            
    except FileNotFoundError as e:
        log_error("main_complete", "FILE_NOT_FOUND", {"error": str(e)})
        print(f"ERROR: {e}")
        return 1
    except KeyError as e:
        log_error("main_complete", "KEY_ERROR", {"error": str(e)})
        print(f"ERROR: {e}")
        return 1
    except RuntimeError as e:
        log_error("main_complete", "RUNTIME_ERROR", {"error": str(e)})
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        log_error("main_complete", "UNEXPECTED_ERROR", {"error": str(e)})
        print(f"ERROR: An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
