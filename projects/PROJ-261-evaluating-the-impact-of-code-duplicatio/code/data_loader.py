#!/usr/bin/env python3
"""
Data loader module for streaming GitHub code corpus from HuggingFace.

This module handles:
- Streaming large datasets from HuggingFace Hub
- Rate limit handling with exponential backoff
- Network error handling with retry logic
- CSV output generation for downstream processing
"""

import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple

# Import config for dataset/model parameters
from config import (
    get_dataset_name,
    get_random_seed,
    get_streaming_enabled,
    get_checksum_algorithm
)

# Set up logging
logger = logging.getLogger(__name__)

def handle_rate_limit(retry_count: int = 0, max_retries: int = 5, base_delay: float = 1.0) -> float:
    """
    Handle rate limit errors with exponential backoff and jitter.

    Args:
        retry_count: Current retry attempt number
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff

    Returns:
        Delay in seconds before next retry

    Raises:
        RuntimeError: If max retries exceeded
    """
    if retry_count >= max_retries:
        raise RuntimeError(f"Rate limit retries exceeded: {max_retries}")

    # Exponential backoff with jitter
    delay = base_delay * (2 ** retry_count) + random.uniform(0, 0.5)
    logger.info(f"Rate limit hit, waiting {delay:.2f}s before retry {retry_count + 1}/{max_retries}")
    time.sleep(delay)
    return delay

def handle_network_error(retry_count: int = 0, max_retries: int = 3, base_delay: float = 2.0) -> float:
    """
    Handle network errors with exponential backoff.

    Args:
        retry_count: Current retry attempt number
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff

    Returns:
        Delay in seconds before next retry

    Raises:
        RuntimeError: If max retries exceeded
    """
    if retry_count >= max_retries:
        raise RuntimeError(f"Network error retries exceeded: {max_retries}")

    delay = base_delay * (2 ** retry_count)
    logger.warning(f"Network error, waiting {delay:.2f}s before retry {retry_count + 1}/{max_retries}")
    time.sleep(delay)
    return delay

def load_raw_data(dataset_name: str, streaming: bool = True) -> Any:
    """
    Load raw data from HuggingFace datasets with optional streaming.

    Args:
        dataset_name: Name of the dataset on HuggingFace Hub
        streaming: Whether to use streaming mode (True for large datasets)

    Returns:
        Dataset object (streaming or loaded)

    Raises:
        ImportError: If datasets library is not installed
        Exception: If dataset loading fails
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("datasets library not installed. Please install with: pip install datasets")
        raise

    logger.info(f"Loading dataset: {dataset_name} (streaming={streaming})")

    try:
        if streaming:
            dataset = load_dataset(dataset_name, split="train", streaming=True)
        else:
            dataset = load_dataset(dataset_name, split="train")

        logger.info(f"Dataset loaded successfully: {dataset_name}")
        return dataset

    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {str(e)}")
        raise

def stream_dataset(dataset_name: str, sample_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Stream a sample from the dataset.

    Args:
        dataset_name: Name of the dataset on HuggingFace Hub
        sample_size: Number of samples to retrieve

    Returns:
        List of dataset rows as dictionaries

    Raises:
        RuntimeError: If streaming fails
    """
    streaming = get_streaming_enabled()
    logger.info(f"Streaming dataset with streaming={streaming}, sample_size={sample_size}")

    try:
        dataset = load_raw_data(dataset_name, streaming=streaming)

        samples = []
        count = 0

        for item in dataset:
            if count >= sample_size:
                break

            # Filter for Python files only
            lang = item.get('lang', '').lower() if isinstance(item.get('lang'), str) else ''
            if 'code' in item and lang == 'python':
                samples.append({
                    'repo': item.get('repo', 'unknown'),
                    'path': item.get('path', 'unknown'),
                    'code': item.get('code', ''),
                    'lang': item.get('lang', 'python'),
                    'license': item.get('license', 'unknown')
                })
                count += 1

                if count % 100 == 0:
                    logger.info(f"Collected {count}/{sample_size} Python samples")

        logger.info(f"Successfully streamed {len(samples)} samples from {dataset_name}")
        return samples

    except Exception as e:
        logger.error(f"Failed to stream dataset: {str(e)}")
        raise RuntimeError(f"Dataset streaming failed: {str(e)}")

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute checksum of a file.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of file checksum
    """
    hash_func = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()

def save_raw_data_to_csv(data: List[Dict[str, Any]], output_path: str) -> str:
    """
    Save raw data to CSV file.

    Args:
        data: List of dictionaries to save
        output_path: Path to output CSV file

    Returns:
        Path to saved file

    Raises:
        IOError: If file cannot be written
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        logger.warning("No data to save to CSV")
        return str(output_path)

    import csv

    logger.info(f"Saving {len(data)} samples to {output_path}")

    fieldnames = ['repo', 'path', 'code', 'lang', 'license']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

    # Compute checksum
    checksum = compute_file_checksum(output_path)
    logger.info(f"Saved CSV with checksum: {checksum}")

    return str(output_path)

def download_and_save_sample(dataset_name: str, output_path: str, sample_size: int = 1000) -> str:
    """
    Download dataset sample and save to CSV.

    Args:
        dataset_name: Name of the dataset on HuggingFace Hub
        output_path: Path to save CSV output
        sample_size: Number of samples to retrieve

    Returns:
        Path to saved CSV file

    Raises:
        RuntimeError: If download or save fails
    """
    logger.info(f"Starting download of {dataset_name} (sample_size={sample_size})")

    try:
        # Stream the dataset
        samples = stream_dataset(dataset_name, sample_size)

        if not samples:
            logger.warning(f"No samples collected from {dataset_name}")
            return output_path

        # Save to CSV
        saved_path = save_raw_data_to_csv(samples, output_path)

        logger.info(f"Successfully downloaded and saved {len(samples)} samples to {saved_path}")
        return saved_path

    except Exception as e:
        logger.error(f"Failed to download and save sample: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}")

def main():
    """
    Main entry point for data loader.

    Downloads GitHub code corpus and saves to data/raw/github-code-sample.csv
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get configuration
    dataset_name = get_dataset_name()
    output_path = Path("data/raw/github-code-sample.csv")

    logger.info(f"Data loader starting for dataset: {dataset_name}")
    logger.info(f"Output path: {output_path}")

    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download and save sample
        saved_path = download_and_save_sample(
            dataset_name=dataset_name,
            output_path=str(output_path),
            sample_size=1000
        )

        logger.info(f"Data loader completed successfully. Output: {saved_path}")

    except Exception as e:
        logger.error(f"Data loader failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()