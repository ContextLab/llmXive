"""
Data loader module for streaming GitHub code dataset.

This module handles downloading and streaming the codeparrot/github-code dataset
using HuggingFace datasets library with streaming mode enabled to stay within
memory constraints (SC-002: 7GB limit).

Output: data/raw/github-code-sample.csv
"""

import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple

import pandas as pd
from datasets import load_dataset

# Configure module logger
logger = logging.getLogger(__name__)

# Configuration constants
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds
STREAMING_BATCH_SIZE = 100
OUTPUT_PATH = Path("data/raw/github-code-sample.csv")
DATASET_NAME = "codeparrot/github-code"
LANGUAGE_FILTER = "python"
SAMPLE_SIZE = 1000  # Number of samples to download for initial run
RANDOM_SEED = 42

def handle_rate_limit(retry_count: int) -> float:
    """
    Handle rate limiting by implementing exponential backoff.
    
    Args:
        retry_count: Current retry attempt number
        
    Returns:
        Delay in seconds before next retry
    """
    delay = RETRY_DELAY_BASE * (2 ** retry_count) + random.uniform(0, 1)
    logger.warning(f"Rate limit detected, retrying in {delay:.2f} seconds (attempt {retry_count + 1}/{MAX_RETRIES})")
    return delay

def handle_network_error(retry_count: int) -> float:
    """
    Handle network errors with exponential backoff.
    
    Args:
        retry_count: Current retry attempt number
        
    Returns:
        Delay in seconds before next retry
    """
    delay = RETRY_DELAY_BASE * (2 ** retry_count) + random.uniform(0, 1)
    logger.warning(f"Network error detected, retrying in {delay:.2f} seconds (attempt {retry_count + 1}/{MAX_RETRIES})")
    return delay

def load_raw_data(
    dataset_name: str = DATASET_NAME,
    streaming: bool = True,
    language: str = LANGUAGE_FILTER,
    seed: int = RANDOM_SEED
) -> Generator[Dict[str, Any], None, None]:
    """
    Load raw data from HuggingFace datasets with streaming enabled.
    
    Args:
        dataset_name: Name of the dataset to load
        streaming: Whether to use streaming mode (True for memory efficiency)
        language: Language filter for code (e.g., 'python')
        seed: Random seed for reproducibility
        
    Yields:
        Dictionary containing code samples with metadata
    """
    logger.info(f"Loading dataset '{dataset_name}' with streaming={streaming}")
    
    try:
        # Load dataset with streaming enabled to stay within memory limits
        dataset = load_dataset(
            dataset_name,
            split="train",
            streaming=streaming,
            trust_remote_code=True
        )
        
        # Filter for Python files if language specified
        if language:
            logger.info(f"Filtering for language: {language}")
            dataset = dataset.filter(lambda x: x.get("language", "").lower() == language.lower())
        
        logger.info("Dataset loaded successfully, starting iteration")
        
        # Iterate and yield samples
        for idx, sample in enumerate(dataset):
            yield sample
            if idx % 100 == 0:
                logger.debug(f"Processed {idx} samples")
                
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def stream_dataset(
    data_generator: Generator[Dict[str, Any], None, None],
    max_samples: int = SAMPLE_SIZE
) -> List[Dict[str, Any]]:
    """
    Stream dataset samples into memory up to max_samples limit.
    
    Args:
        data_generator: Generator yielding dataset samples
        max_samples: Maximum number of samples to collect
        
    Returns:
        List of collected samples as dictionaries
    """
    samples = []
    logger.info(f"Streaming dataset, collecting up to {max_samples} samples")
    
    try:
        for idx, sample in enumerate(data_generator):
            if idx >= max_samples:
                logger.info(f"Collected {max_samples} samples, stopping")
                break
            
            # Ensure sample has required fields
            if "content" in sample or "code" in sample:
                samples.append(sample)
            
            if idx % 50 == 0:
                logger.debug(f"Collected {len(samples)} samples so far")
                
    except Exception as e:
        logger.error(f"Error during streaming: {e}")
        raise
    
    logger.info(f"Successfully streamed {len(samples)} samples")
    return samples

def save_raw_data_to_csv(
    samples: List[Dict[str, Any]],
    output_path: Path = OUTPUT_PATH
) -> Path:
    """
    Save raw data samples to CSV file.
    
    Args:
        samples: List of sample dictionaries to save
        output_path: Path to output CSV file
        
    Returns:
        Path to the saved file
        
    Raises:
        ValueError: If no samples to save
    """
    if not samples:
        logger.warning("No samples to save")
        raise ValueError("Cannot save empty dataset")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Normalize sample keys for CSV
    normalized_samples = []
    for sample in samples:
        normalized = {
            "id": sample.get("id", f"sample_{len(normalized_samples)}"),
            "language": sample.get("language", "unknown"),
            "repo": sample.get("repo", ""),
            "path": sample.get("path", ""),
            "content": sample.get("content", sample.get("code", "")),
            "size": sample.get("size", 0),
            "license": sample.get("license", ""),
            "ext": sample.get("ext", "")
        }
        normalized_samples.append(normalized)
    
    # Create DataFrame and save
    df = pd.DataFrame(normalized_samples)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved {len(normalized_samples)} samples to {output_path}")
    return output_path

def download_and_save_sample(
    dataset_name: str = DATASET_NAME,
    output_path: Path = OUTPUT_PATH,
    max_samples: int = SAMPLE_SIZE,
    streaming: bool = True,
    language: str = LANGUAGE_FILTER,
    seed: int = RANDOM_SEED
) -> Tuple[Path, int]:
    """
    Main function to download dataset and save to CSV.
    
    This is the primary entry point for downloading the GitHub code corpus
    with streaming enabled to maintain memory constraints.
    
    Args:
        dataset_name: Name of HuggingFace dataset
        output_path: Path to output CSV file
        max_samples: Maximum samples to download
        streaming: Enable streaming mode (REQUIRED for memory efficiency)
        language: Language filter
        seed: Random seed
        
    Returns:
        Tuple of (output_path, sample_count)
        
    Raises:
        RuntimeError: If download fails after all retries
    """
    # Verify streaming is enabled (critical for memory constraints)
    if not streaming:
        logger.warning("Streaming is disabled - this may exceed memory limits!")
    
    retry_count = 0
    last_error = None
    
    while retry_count < MAX_RETRIES:
        try:
            logger.info(f"Starting download attempt {retry_count + 1}/{MAX_RETRIES}")
            
            # Load data with streaming enabled
            data_generator = load_raw_data(
                dataset_name=dataset_name,
                streaming=True,  # Force streaming=True for memory efficiency
                language=language,
                seed=seed
            )
            
            # Stream samples
            samples = stream_dataset(data_generator, max_samples=max_samples)
            
            # Save to CSV
            saved_path = save_raw_data_to_csv(samples, output_path)
            
            logger.info(f"Download complete: {len(samples)} samples saved to {saved_path}")
            return saved_path, len(samples)
            
        except Exception as e:
            last_error = e
            retry_count += 1
            
            if retry_count < MAX_RETRIES:
                delay = handle_network_error(retry_count - 1)
                time.sleep(delay)
            else:
                logger.error(f"Download failed after {MAX_RETRIES} retries: {e}")
    
    raise RuntimeError(f"Failed to download dataset after {MAX_RETRIES} retries: {last_error}")

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of output file for integrity verification.
    
    Args:
        file_path: Path to file to checksum
        
    Returns:
        Hex digest of SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def main() -> int:
    """
    Main entry point for data loader script.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("=" * 60)
    logger.info("Starting GitHub Code Dataset Download")
    logger.info("=" * 60)
    
    try:
        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Download and save dataset
        output_path, sample_count = download_and_save_sample(
            dataset_name=DATASET_NAME,
            output_path=OUTPUT_PATH,
            max_samples=SAMPLE_SIZE,
            streaming=True  # CRITICAL: streaming must be True
        )
        
        # Compute checksum for integrity tracking
        checksum = compute_file_checksum(output_path)
        logger.info(f"Output file checksum: {checksum}")
        
        logger.info("=" * 60)
        logger.info(f"SUCCESS: Downloaded {sample_count} samples to {output_path}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"FAILED: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
