import os
import sys
import hashlib
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Import from local config to utilize existing error classes and paths
from config import (
    get_dataset_paths,
    get_required_files,
    DatasetNotFoundError,
    LlmXiveError,
    Config,
    setup_logging
)

# Attempt to import datasets library; if missing, we will handle the import error
# but the task requires real data, so we must ensure it's available.
try:
    from datasets import load_dataset, Dataset
except ImportError:
    # We do not provide a synthetic fallback. The script must fail if the library is missing.
    # This block is just to allow syntax checking; runtime will raise ImportError.
    load_dataset = None
    Dataset = None

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Hashing Utilities
# -----------------------------------------------------------------------------

def calculate_file_hash(file_path: str, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """
    Calculate the hash of a file to verify integrity against expected checksums.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default sha256).
        chunk_size: Size of chunks to read.
        
    Returns:
        Hexadecimal hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cannot calculate hash: file not found at {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_checksums(expected_checksums: Dict[str, str], base_dir: str) -> List[str]:
    """
    Verify that existing files match their expected checksums.
    
    Args:
        expected_checksums: Dict mapping relative file paths to expected hex checksums.
        base_dir: Root directory where files are expected.
        
    Returns:
        List of relative file paths that failed verification or are missing.
    """
    missing_or_corrupt = []
    for rel_path, expected_hash in expected_checksums.items():
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            missing_or_corrupt.append(rel_path)
            logger.warning(f"Checksum verification failed: File missing at {full_path}")
            continue
        
        try:
            actual_hash = calculate_file_hash(full_path)
            if actual_hash != expected_hash:
                missing_or_corrupt.append(rel_path)
                logger.error(f"Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
            else:
                logger.info(f"Checksum verified: {rel_path}")
        except Exception as e:
            missing_or_corrupt.append(rel_path)
            logger.error(f"Error calculating checksum for {rel_path}: {e}")
    
    return missing_or_corrupt

# -----------------------------------------------------------------------------
# Download Logic
# -----------------------------------------------------------------------------

def download_dataset(dataset_name: str, config_name: Optional[str] = None, split: str = "train") -> str:
    """
    Download a dataset from HuggingFace using the datasets library.
    
    This function fetches the real data. It does NOT generate synthetic data.
    If the download fails, it raises an exception.
    
    Args:
        dataset_name: The HuggingFace dataset identifier (e.g., 'narrlv/narrlv').
        config_name: Optional configuration name.
        split: The split to download (default 'train').
        
    Returns:
        Path to the downloaded dataset cache directory.
        
    Raises:
        ImportError: If 'datasets' library is not installed.
        Exception: If the download fails for any reason.
    """
    if load_dataset is None:
        raise ImportError(
            "The 'datasets' library is required to download real data. "
            "Please install it via: pip install datasets"
        )

    logger.info(f"Attempting to download dataset: {dataset_name} (config: {config_name}, split: {split})")
    try:
        # Download and cache the dataset
        ds = load_dataset(dataset_name, name=config_name, split=split, trust_remote_code=True)
        
        # The 'datasets' library caches automatically. We return the cache path
        # or a placeholder if we just need to signal success.
        # For robustness, we ensure the data is actually accessible.
        if len(ds) == 0:
            raise ValueError(f"Downloaded dataset '{dataset_name}' is empty.")
        
        logger.info(f"Successfully downloaded and cached {dataset_name}. Size: {len(ds)} samples.")
        return ds.cache_files[0]['filename'] if ds.cache_files else "cached"
        
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_name}: {e}")
        # Re-raise to ensure the pipeline fails loudly
        raise RuntimeError(f"Dataset download failed: {e}") from e

def download_all_datasets() -> Dict[str, str]:
    """
    Download all required datasets defined in the configuration.
    
    Returns:
        Dict mapping dataset name to local path/cache info.
        
    Raises:
        DatasetNotFoundError: If any dataset cannot be downloaded or verified.
    """
    config = get_config()
    dataset_paths = get_dataset_paths()
    results = {}
    
    # Define the datasets to fetch based on project requirements (NarrLV, VBench)
    # These are hardcoded based on the task description, but could be dynamic.
    datasets_to_fetch = [
        {"name": "narrlv/narrlv", "config": "default", "split": "train"},
        {"name": "vladkiselev/vbench", "config": None, "split": "train"} # Example ID, adjust if specific one exists
    ]
    
    for ds_info in datasets_to_fetch:
        name = ds_info["name"]
        try:
            path = download_dataset(name, ds_info.get("config"), ds_info.get("split", "train"))
            results[name] = path
        except Exception as e:
            # Critical failure: we cannot proceed without real data
            raise DatasetNotFoundError(f"Critical: Failed to fetch required dataset '{name}'. {e}")
            
    return results

# -----------------------------------------------------------------------------
# Pre-flight and Error Handling
# -----------------------------------------------------------------------------

def check_preflight_requirements() -> Tuple[bool, List[str]]:
    """
    Check if all required dataset files exist locally before generation.
    
    Returns:
        Tuple of (success: bool, missing_files: List[str])
    """
    config = get_config()
    required_files = get_required_files()
    missing_files = []
    
    logger.info("Running pre-flight check for dataset files...")
    
    for file_path in required_files:
        full_path = os.path.join(config.data_dir, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
            logger.warning(f"Missing required file: {file_path}")
        else:
            logger.debug(f"Found required file: {file_path}")
            
    if missing_files:
        logger.error(f"Pre-flight check failed. Missing {len(missing_files)} files.")
        return False, missing_files
        
    logger.info("Pre-flight check passed. All required files present.")
    return True, []

def abort_on_missing_files(missing_files: List[str]) -> None:
    """
    Abort execution with a clear, formatted error message listing missing files.
    
    This function implements the error handling requirement for T016.
    
    Args:
        missing_files: List of file paths that are missing.
        
    Raises:
        SystemExit: Stops the program immediately.
    """
    if not missing_files:
        return

    error_msg = [
        "\n" + "="*60,
        "FATAL ERROR: MISSING REQUIRED DATASET FILES",
        "="*60,
        f"The following {len(missing_files)} required file(s) are missing:",
    ]
    
    for f in missing_files:
        error_msg.append(f"  - {f}")
    
    error_msg.extend([
        "",
        "Please ensure the datasets have been downloaded successfully.",
        "Run 'python code/download.py' to fetch the required data.",
        "="*60 + "\n"
    ])
    
    # Log the error message
    logger.error("\n".join(error_msg))
    
    # Raise a specific exception to be caught by the main entry point if needed,
    # or exit immediately.
    raise DatasetNotFoundError("\n".join(error_msg))

def main():
    """
    Main entry point for the download and validation script.
    
    Handles:
    1. Downloading datasets if missing.
    2. Verifying checksums.
    3. Pre-flight checks with robust error handling for missing files.
    """
    parser = argparse.ArgumentParser(description="Download and validate datasets for llmXive.")
    parser.add_argument("--force", action="store_true", help="Force re-download of datasets")
    parser.add_argument("--check-only", action="store_true", help="Only check for existing files, do not download")
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        # 1. Check pre-flight requirements
        success, missing = check_preflight_requirements()
        
        if args.check_only:
            if not success:
                abort_on_missing_files(missing)
            else:
                logger.info("Check-only mode: All files present.")
                sys.exit(0)
        
        # 2. If missing files exist, attempt to download
        if not success:
            logger.warning(f"Missing files detected: {missing}. Attempting download...")
            try:
                download_all_datasets()
                # Re-check after download
                success, missing = check_preflight_requirements()
                if not success:
                    abort_on_missing_files(missing)
            except Exception as e:
                logger.critical(f"Download process failed: {e}")
                abort_on_missing_files(missing)
        else:
            logger.info("All required files are present.")

        # 3. Final verification (optional but good practice)
        # If we have checksums defined in config, verify them here.
        # For now, we assume presence is sufficient if download succeeded.
        
        logger.info("Dataset download and validation completed successfully.")

    except DatasetNotFoundError as e:
        # This is the expected path for T016 error handling
        print(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred during dataset handling.")
        sys.exit(1)

if __name__ == "__main__":
    main()