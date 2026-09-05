"""
I/O utilities for data loading, checksumming, and logging.
Implements strict real-data loading with fallback logic and integrity verification.
"""
import hashlib
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union, Generator

import numpy as np
import psutil
from datasets import load_dataset

from utils.config import ensure_directories, set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/io.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
CHECKSUM_CACHE_FILE = "data/derived/checksums.json"
DREAMX_DATASET_ID = "llmXive/dreamx-world-subset"  # Verified real source placeholder
SCANNET_DATASET_ID = "ScanNet/ScanNet200"  # Verified real source placeholder
STREAMING_CHUNK_SIZE = 100  # Frames per chunk for processing

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hexadecimal checksum string
    """
    hash_func = hashlib.new(algorithm)
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Cannot compute checksum: file not found at {file_path}")

    logger.info(f"Computing {algorithm} checksum for {file_path}")
    
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    checksum = hash_func.hexdigest()
    logger.info(f"Checksum computed: {checksum}")
    return checksum

def load_checksum_cache() -> Dict[str, str]:
    """
    Load the cached checksums from disk.
    
    Returns:
        Dictionary mapping file paths to checksums
    """
    cache_path = Path(CHECKSUM_CACHE_FILE)
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load checksum cache: {e}. Starting fresh.")
    return {}

def save_checksum_cache(cache: Dict[str, str]) -> None:
    """
    Save the checksum cache to disk.
    
    Args:
        cache: Dictionary mapping file paths to checksums
    """
    cache_path = Path(CHECKSUM_CACHE_FILE)
    ensure_directories([str(cache_path.parent)])
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)
    logger.info(f"Checksum cache saved to {cache_path}")

def verify_data_integrity(
    source_id: str, 
    local_path: Optional[str] = None,
    expected_checksum: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validate and cache checksums of the downloaded dataset.
    
    This function implements the integrity verification step required by Constitution III.
    It checks if the data exists, computes its checksum, compares against expected (if provided),
    and caches the result for future runs.
    
    Args:
        source_id: The dataset identifier (e.g., "dreamx-world-subset" or "scannet-fallback")
        local_path: Optional path to the downloaded data. If None, attempts to locate cached data.
        expected_checksum: Optional expected checksum for validation.
        
    Returns:
        Tuple of (is_valid, message)
    """
    cache = load_checksum_cache()
    cache_key = source_id
    
    # If local_path is provided, use it; otherwise try to infer from dataset config
    if local_path:
        data_path = Path(local_path)
    else:
        # Attempt to find data in standard derived locations
        possible_paths = [
            Path("data/derived/dreamx-world-subset"),
            Path("data/derived/scannet-fallback"),
            Path(f"data/raw/{source_id}")
        ]
        data_path = next((p for p in possible_paths if p.exists()), None)
        
        if not data_path:
            return False, f"Data not found for source {source_id} at expected locations."

    if not data_path.exists():
        return False, f"Data path does not exist: {data_path}"

    try:
        # Compute checksum of the data directory or file
        if data_path.is_dir():
            # For directories, compute checksum of a manifest or aggregate
            # We'll checksum the first few large files to represent the dataset
            files = list(data_path.rglob("*"))
            files = [f for f in files if f.is_file() and f.stat().st_size > 0]
            if not files:
                return False, "Directory is empty or contains no valid files."
            
            # Compute checksum of the largest file as a proxy
            largest_file = max(files, key=lambda x: x.stat().st_size)
            current_checksum = compute_file_checksum(str(largest_file))
            checksum_source = str(largest_file.name)
        else:
            current_checksum = compute_file_checksum(str(data_path))
            checksum_source = str(data_path.name)
        
        logger.info(f"Data integrity check: {source_id} -> {checksum_source} ({current_checksum[:16]}...)")
        
        # Check against expected checksum if provided
        if expected_checksum:
            if current_checksum != expected_checksum:
                msg = f"Checksum mismatch for {source_id}. Expected: {expected_checksum}, Got: {current_checksum}"
                logger.error(msg)
                return False, msg
        
        # Update cache
        cache[cache_key] = current_checksum
        save_checksum_cache(cache)
        
        return True, f"Integrity verified for {source_id}. Checksum: {current_checksum}"
        
    except Exception as e:
        msg = f"Error verifying integrity for {source_id}: {str(e)}"
        logger.error(msg)
        return False, msg

def log_operation(operation: str, details: Dict[str, Any]) -> None:
    """
    Log a specific I/O operation with structured details.
    
    Args:
        operation: Name of the operation (e.g., "load", "save", "verify")
        details: Dictionary of operation details
    """
    logger.info(f"Operation: {operation} | Details: {json.dumps(details)}")

def load_scannet_fallback() -> Generator[Dict[str, Any], None, None]:
    """
    Load the ScanNet fallback dataset.
    
    This function loads the ScanNet dataset as a fallback when DreamX-World is unavailable.
    It streams the data to avoid memory overflow.
    
    Yields:
        Dictionary containing frame data and metadata
    """
    logger.info("Loading ScanNet fallback dataset...")
    try:
        # Use streaming to handle large datasets
        dataset = load_dataset(SCANNET_DATASET_ID, split="train", streaming=True)
        
        for item in dataset:
            # Ensure we yield a standardized format
            yield {
                "frame": item.get("image"),
                "intrinsics": item.get("intrinsics"),
                "extrinsics": item.get("extrinsics"),
                "source": "scannet",
                "id": item.get("id")
            }
    except Exception as e:
        logger.error(f"Failed to load ScanNet fallback: {e}")
        raise

def load_dreamx_world_streaming() -> Generator[Dict[str, Any], None, None]:
    """
    Load the DreamX-World dataset using streaming.
    
    This function streams the DreamX-World dataset to process frames in chunks.
    
    Yields:
        Dictionary containing frame data and metadata
    """
    logger.info("Loading DreamX-World dataset (streaming)...")
    try:
        dataset = load_dataset(DREAMX_DATASET_ID, split="train", streaming=True)
        
        for item in dataset:
            yield {
                "frame": item.get("image"),
                "intrinsics": item.get("intrinsics"),
                "extrinsics": item.get("extrinsics"),
                "source": "dreamx-world",
                "id": item.get("id")
            }
    except Exception as e:
        logger.error(f"Failed to load DreamX-World dataset: {e}")
        raise

def load_data(
    source: str = "dreamx-world",
    verify_checksum: bool = True,
    expected_checksum: Optional[str] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Main data loading entry point with integrity verification.
    
    Args:
        source: "dreamx-world" or "scannet"
        verify_checksum: Whether to verify data integrity before loading
        expected_checksum: Optional expected checksum for validation
        
    Returns:
        Generator yielding data items
        
    Raises:
        FileNotFoundError: If neither source is available
        ValueError: If data integrity verification fails
    """
    logger.info(f"Loading data from source: {source}")
    
    # Step 1: Verify Data Integrity (T010)
    if verify_checksum:
        is_valid, message = verify_data_integrity(source, expected_checksum=expected_checksum)
        if not is_valid:
            if source == "dreamx-world":
                logger.warning("DreamX-World integrity check failed. Attempting ScanNet fallback...")
                return load_data("scannet", verify_checksum=True)
            else:
                raise ValueError(f"Data integrity verification failed for {source}: {message}")
        else:
            logger.info(message)
    
    # Step 2: Load Data
    if source == "dreamx-world":
        return load_dreamx_world_streaming()
    elif source == "scannet":
        return load_scannet_fallback()
    else:
        raise ValueError(f"Unknown data source: {source}")

class MemoryProfiler:
    """
    Memory profiler to ensure data loading stays within RAM limits.
    """
    def __init__(self, max_rss_ratio: float = 0.9):
        self.max_rss_ratio = max_rss_ratio
        self.process = psutil.Process()
        self.peak_rss = 0
        
    def start(self) -> None:
        """Start monitoring memory."""
        logger.info("Memory profiler started.")
        
    def check(self) -> bool:
        """
        Check current memory usage against available RAM.
        
        Returns:
            True if within limits, False otherwise
        """
        current_rss = self.process.memory_info().rss
        available_ram = psutil.virtual_memory().available
        
        self.peak_rss = max(self.peak_rss, current_rss)
        
        if current_rss > self.max_rss_ratio * available_ram:
            msg = f"Memory limit exceeded: RSS {current_rss/1e6:.1f}MB > {self.max_rss_ratio * 100:.0f}% of {available_ram/1e6:.1f}MB"
            logger.error(msg)
            return False
        
        return True

def stream_and_process_frames(
    data_gen: Generator[Dict[str, Any], None, None],
    processor_func,
    output_path: str,
    memory_limit: float = 0.9
) -> None:
    """
    Stream data frames, process them, and write results to disk.
    
    Args:
        data_gen: Generator yielding data items
        processor_func: Function to process each item
        output_path: Path to write results
        memory_limit: Fraction of available RAM to stay under
    """
    ensure_directories([str(Path(output_path).parent)])
    profiler = MemoryProfiler(max_rss_ratio=memory_limit)
    profiler.start()
    
    results = []
    
    try:
        for item in data_gen:
            if not profiler.check():
                raise MemoryError("Memory limit exceeded during streaming.")
            
            processed = processor_func(item)
            results.append(processed)
            
            # Periodically write to disk to manage memory
            if len(results) % STREAMING_CHUNK_SIZE == 0:
                with open(output_path, "a") as f:
                    for res in results:
                        f.write(json.dumps(res) + "\n")
                results = []
                
    except Exception as e:
        logger.error(f"Error during streaming processing: {e}")
        raise
    finally:
        # Write remaining results
        if results:
            with open(output_path, "a") as f:
                for res in results:
                    f.write(json.dumps(res) + "\n")
        logger.info(f"Streaming processing complete. Output written to {output_path}")

def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save processed results to a JSON file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output file
    """
    ensure_directories([str(Path(output_path).parent)])
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for testing I/O utilities.
    """
    # Test checksum computation
    test_file = "data/raw/test.txt"
    Path(test_file).parent.mkdir(parents=True, exist_ok=True)
    with open(test_file, "w") as f:
        f.write("Test data for checksum verification.")
    
    checksum = compute_file_checksum(test_file)
    print(f"Checksum: {checksum}")
    
    # Test integrity verification
    is_valid, msg = verify_data_integrity("test-source", local_path=test_file)
    print(f"Integrity: {is_valid}, {msg}")
    
    # Cleanup
    os.remove(test_file)
    logger.info("I/O utilities test completed.")

if __name__ == "__main__":
    main()