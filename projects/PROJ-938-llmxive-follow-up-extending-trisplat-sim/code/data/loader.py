import logging
import hashlib
import json
import os
from typing import Iterator, Dict, Any, Optional, Tuple
from pathlib import Path

import datasets
from datasets import DatasetDict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
REAL_ESTATE_10K_DATASET_ID = "nielsr/realestate10k-128-256"
REAL_ESTATE_10K_SPLIT = "validation"
TARGET_WIDTH = 320
TARGET_HEIGHT = 240
CHECKSUM_DIR = Path("data/processed")
CHECKSUMS_FILE = CHECKSUM_DIR / "checksums_temp.json"

def compute_sha256_file(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to a temporary JSON file."""
    CHECKSUM_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUMS_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {CHECKSUMS_FILE}")

def load_real_estate_10k_streaming(seed: int = 42) -> Iterator[Dict[str, Any]]:
    """
    Load RealEstate10K dataset in streaming mode.
    
    This function strictly adheres to the "Real Data Source Lock-in" requirement (T049).
    It uses the verified dataset ID and split. It contains NO try/except blocks that
    fallback to synthetic data. If the dataset fetch fails, it raises a loud error
    immediately.
    
    Args:
        seed: Random seed for reproducibility (used if shuffling is enabled, though
              we stream sequentially for deterministic sampling in run_batch).
    
    Yields:
        Dictionary containing scene data (images, intrinsics, poses).
    
    Raises:
        ConnectionError: If the dataset cannot be fetched from HuggingFace.
        RuntimeError: If the dataset ID or split is invalid.
    """
    logger.info(f"Attempting to stream dataset: {REAL_ESTATE_10K_DATASET_ID} split={REAL_ESTATE_10K_SPLIT}")
    
    try:
        # Attempt to load the dataset in streaming mode
        # This will fail loudly if the network is unreachable or the dataset is missing
        dataset = datasets.load_dataset(
            REAL_ESTATE_10K_DATASET_ID,
            split=REAL_ESTATE_10K_SPLIT,
            streaming=True,
            trust_remote_code=True
        )
    except Exception as e:
        # CRITICAL: No synthetic fallback. Fail loudly.
        error_msg = (
            f"CRITICAL FAILURE: Could not load RealEstate10K dataset from "
            f"'{REAL_ESTATE_10K_DATASET_ID}' (split: '{REAL_ESTATE_10K_SPLIT}'). "
            f"Error: {str(e)}. "
            f"Please check your internet connection and dataset availability. "
            f"Synthetic data fallback is DISABLED by design (T049)."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Validate schema immediately to catch structural issues early
    try:
        sample = next(iter(dataset))
        required_keys = {'images', 'intrinsics', 'poses'}
        if not all(k in sample for k in required_keys):
            raise ValueError(f"Dataset schema mismatch. Expected keys {required_keys}, got {sample.keys()}")
        logger.info("Dataset schema validated successfully.")
    except StopIteration:
        raise RuntimeError("Dataset is empty. Cannot proceed.")
    except Exception as e:
        raise RuntimeError(f"Schema validation failed: {e}") from e

    # Return the iterator directly. 
    # Note: Deterministic slicing (itertools.islice) is performed in run_batch.py (T047)
    # to avoid consuming the stream prematurely here.
    return iter(dataset)

def get_scene_batch(dataset_iterator: Iterator[Dict[str, Any]], n_scenes: int, seed: int = 42) -> list:
    """
    Extract a batch of scenes from the streaming iterator.
    
    This function performs the deterministic sampling using itertools.islice as per T047.
    It does NOT generate synthetic data if the stream ends prematurely; it will simply
    return fewer scenes or raise an error if n_scenes is not met (depending on caller logic).
    
    Args:
        dataset_iterator: The streaming iterator from load_real_estate_10k_streaming.
        n_scenes: Number of scenes to fetch.
        seed: Seed for reproducibility (currently unused for sequential islice, but kept for API).
    
    Returns:
        List of scene dictionaries.
    """
    import itertools
    
    logger.info(f"Fetching first {n_scenes} scenes from stream...")
    scenes = list(itertools.islice(dataset_iterator, n_scenes))
    
    if len(scenes) < n_scenes:
        logger.warning(f"Only retrieved {len(scenes)} scenes, requested {n_scenes}. "
                     "This may indicate the dataset is smaller than expected or stream ended early.")
    
    return scenes

def verify_stream_connectivity() -> bool:
    """
    Pre-flight check to verify connectivity and schema validity.
    
    This satisfies T048. It attempts to stream a small sample (1 item) to ensure
    the dataset is reachable and valid before starting the main batch.
    
    Returns:
        True if connection and schema are valid.
    
    Raises:
        RuntimeError: If connectivity or schema check fails.
    """
    logger.info("Running stream connectivity verification...")
    try:
        dataset = datasets.load_dataset(
            REAL_ESTATE_10K_DATASET_ID,
            split=REAL_ESTATE_10K_SPLIT,
            streaming=True,
            trust_remote_code=True
        )
        sample = next(iter(dataset))
        required_keys = {'images', 'intrinsics', 'poses'}
        if not all(k in sample for k in required_keys):
            raise ValueError(f"Schema mismatch: missing keys {required_keys - set(sample.keys())}")
        logger.info("Stream connectivity and schema verification PASSED.")
        return True
    except Exception as e:
        error_msg = (
            f"CRITICAL: Pre-flight stream verification FAILED. "
            f"Cannot proceed with batch processing. Error: {e}. "
            f"Ensure real data source '{REAL_ESTATE_10K_DATASET_ID}' is accessible."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e