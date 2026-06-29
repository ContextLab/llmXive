#!/usr/bin/env python3
"""
Data loader for streaming GitHub code dataset.

This module streams the codeparrot/github-code dataset from HuggingFace
with streaming mode enabled to avoid downloading the full dataset into memory.
Outputs data to data/raw/github-code-sample.csv for downstream processing.
"""

import logging
import time
import random
import hashlib
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple

# Import from project config
from config import (
    get_dataset_name,
    get_model_name,
    get_streaming_enabled,
    get_random_seed,
    get_max_runtime_seconds,
)


def setup_logging(name: str = "data_loader") -> logging.Logger:
    """
    Configure logging for the data loader module.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def handle_rate_limit(retry_count: int = 3, base_delay: float = 1.0) -> Generator[int, None, None]:
    """
    Handle rate limiting with exponential backoff and jitter.

    Args:
        retry_count: Maximum number of retries
        base_delay: Base delay in seconds

    Yields:
        Retry attempt number (0 to retry_count)
    """
    logger = logging.getLogger(__name__)
    for attempt in range(retry_count + 1):
        if attempt > 0:
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
            logger.warning(f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt}/{retry_count})")
            time.sleep(delay)
        yield attempt


def handle_network_error(retry_count: int = 3, base_delay: float = 2.0) -> Generator[int, None, None]:
    """
    Handle network errors with exponential backoff.

    Args:
        retry_count: Maximum number of retries
        base_delay: Base delay in seconds

    Yields:
        Retry attempt number (0 to retry_count)
    """
    logger = logging.getLogger(__name__)
    for attempt in range(retry_count + 1):
        if attempt > 0:
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 2)
            logger.warning(f"Network error, retrying in {delay:.2f}s (attempt {attempt}/{retry_count})")
            time.sleep(delay)
        yield attempt


def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute SHA-256 checksum of a file.

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


def stream_dataset(dataset_name: str = None, streaming: bool = True, split: str = 'train',
                   max_samples: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Stream dataset from HuggingFace with streaming mode enabled.

    Args:
        dataset_name: Name of HuggingFace dataset to load
        streaming: Whether to use streaming mode (must be True for large datasets)
        split: Dataset split to load
        max_samples: Maximum number of samples to yield (None for unlimited)

    Yields:
        Dataset samples as dictionaries

    Raises:
        ImportError: If datasets library is not installed
        Exception: If dataset loading fails after all retries
    """
    logger = logging.getLogger(__name__)

    # Import datasets library
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("datasets library not installed. Run: pip install datasets")
        raise

    # Use config defaults if not specified
    if dataset_name is None:
        dataset_name = get_dataset_name()
    if streaming is None:
        streaming = get_streaming_enabled()

    logger.info(f"Loading dataset: {dataset_name} (streaming={streaming}, split={split})")

    # Retry with backoff for network issues
    for attempt in handle_network_error(retry_count=5, base_delay=5.0):
        try:
            ds = load_dataset(
                dataset_name,
                split=split,
                streaming=streaming,
                trust_remote_code=True
            )
            logger.info(f"Successfully loaded dataset: {dataset_name}")

            sample_count = 0
            for sample in ds:
                if max_samples and sample_count >= max_samples:
                    break
                yield sample
                sample_count += 1

            logger.info(f"Streamed {sample_count} samples from {dataset_name}")
            break

        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {str(e)}")
            if attempt == 5:
                logger.error(f"Failed to load dataset after all retries: {str(e)}")
                raise


def save_raw_data_to_csv(samples: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save raw dataset samples to CSV file.

    Args:
        samples: List of sample dictionaries
        output_path: Path to output CSV file
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Saving {len(samples)} samples to {output_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if not samples:
            logger.warning("No samples to write to CSV")
            return

        # Use 'content' as the primary column for code data
        fieldnames = ['id', 'content', 'language', 'repo', 'timestamp']
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for idx, sample in enumerate(samples):
            row = {
                'id': str(idx),
                'content': sample.get('content', sample.get('text', '')),
                'language': sample.get('language', 'unknown'),
                'repo': sample.get('repo', sample.get('repository', 'unknown')),
                'timestamp': sample.get('timestamp', '')
            }
            writer.writerow(row)

    logger.info(f"Successfully saved {len(samples)} samples to {output_path}")


def download_and_save_sample(output_path: Path = None, max_samples: int = 1000,
                             dataset_name: str = None) -> Path:
    """
    Download dataset sample and save to CSV.

    Args:
        output_path: Output path for CSV file (default: data/raw/github-code-sample.csv)
        max_samples: Maximum number of samples to download
        dataset_name: HuggingFace dataset name

    Returns:
        Path to output CSV file
    """
    logger = logging.getLogger(__name__)

    # Default output path
    if output_path is None:
        output_path = Path("data/raw/github-code-sample.csv")
    else:
        output_path = Path(output_path)

    logger.info(f"Downloading {dataset_name or get_dataset_name()} dataset")
    logger.info(f"Streaming mode: {get_streaming_enabled()}")
    logger.info(f"Max samples: {max_samples}")

    # Collect samples from streaming dataset
    samples = []
    for sample in stream_dataset(
        dataset_name=dataset_name,
        streaming=True,  # Force streaming mode as required
        split='train',
        max_samples=max_samples
    ):
        samples.append(sample)

    # Save to CSV
    save_raw_data_to_csv(samples, output_path)

    # Compute and log checksum
    if output_path.exists():
        checksum = compute_file_checksum(output_path)
        logger.info(f"Output file checksum: {checksum}")

    return output_path


def load_raw_data(raw_data_path: Path = None) -> List[Dict[str, Any]]:
    """
    Load raw data from CSV file.

    Args:
        raw_data_path: Path to raw data CSV file

    Returns:
        List of sample dictionaries
    """
    logger = logging.getLogger(__name__)

    if raw_data_path is None:
        raw_data_path = Path("data/raw/github-code-sample.csv")
    else:
        raw_data_path = Path(raw_data_path)

    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data not found: {raw_data_path}")

    samples = []
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append(row)

    logger.info(f"Loaded {len(samples)} samples from {raw_data_path}")
    return samples


def main():
    """
    Main entry point for data loader.

    Usage: python code/data_loader.py

    This script streams the codeparrot/github-code dataset using
    HuggingFace datasets library with streaming=True and saves
    the output to data/raw/github-code-sample.csv.
    """
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("Starting data loader - Stage 1: Download data")
    logger.info("=" * 60)

    try:
        # Download and save dataset sample
        output_path = download_and_save_sample(
            max_samples=1000,  # Start with 1000 samples for testing
            dataset_name=get_dataset_name()
        )

        logger.info("=" * 60)
        logger.info("Data loader completed successfully")
        logger.info(f"Output: {output_path}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Data loader failed: {str(e)}")
        logger.error("Please check that the datasets library is installed:")
        logger.error("  pip install datasets")
        return 1


if __name__ == "__main__":
    sys.exit(main())