#!/usr/bin/env python3
"""
Data loader module for streaming GitHub code corpus.

Streams the codeparrot/github-code dataset using HuggingFace datasets library
with streaming mode enabled, and saves a sample to CSV format.
"""

import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple

from datasets import load_dataset

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"


def setup_logging() -> logging.Logger:
    """Set up logging for the data loader module."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def handle_rate_limit(retry_count: int = 3, base_delay: float = 2.0) -> None:
    """Handle rate limiting with exponential backoff."""
    delay = base_delay * (2 ** retry_count) + random.uniform(0, 1)
    time.sleep(delay)


def handle_network_error(retry_count: int = 3) -> bool:
    """Handle network errors with retry logic."""
    if retry_count > 0:
        time.sleep(random.uniform(1, 3))
        return True
    return False


def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def stream_dataset(
    dataset_name: str = "codeparrot/github-code",
    streaming: bool = True,
    split: str = "train",
    max_samples: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream dataset from HuggingFace with rate limiting and error handling.

    Args:
        dataset_name: Name of the HuggingFace dataset
        streaming: Enable streaming mode (required for large datasets)
        split: Dataset split to load
        max_samples: Maximum number of samples to yield

    Yields:
        Dataset rows as dictionaries
    """
    logger = logging.getLogger(__name__)

    if not streaming:
        logger.warning("Streaming disabled - loading entire dataset into memory")

    try:
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming
        )

        sample_count = 0
        for row in dataset:
            yield row
            sample_count += 1

            if max_samples and sample_count >= max_samples:
                break

    except Exception as e:
        logger.error(f"Error streaming dataset: {e}")
        raise


def save_raw_data_to_csv(
    data: List[Dict[str, Any]],
    output_path: Path,
    checksum_path: Optional[Path] = None
) -> None:
    """
    Save raw dataset samples to CSV format.

    Args:
        data: List of dictionaries to save
        output_path: Path to output CSV file
        checksum_path: Optional path to save checksum file
    """
    import csv

    logger = logging.getLogger(__name__)

    if not data:
        logger.warning("No data to save")
        return

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get field names from first row
    fieldnames = list(data[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Saved {len(data)} samples to {output_path}")

    # Compute and save checksum if requested
    if checksum_path:
        checksum = compute_file_checksum(output_path)
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        logger.info(f"Saved checksum to {checksum_path}")


def download_and_save_sample(
    output_path: Path,
    dataset_name: str = "codeparrot/github-code",
    max_samples: int = 1000,
    streaming: bool = True
) -> Tuple[Path, str]:
    """
    Download and save a sample of the GitHub code dataset.

    Args:
        output_path: Path to save the CSV file
        dataset_name: HuggingFace dataset name
        max_samples: Maximum number of samples to download
        streaming: Enable streaming mode

    Returns:
        Tuple of (output_path, checksum)
    """
    logger = logging.getLogger(__name__)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    samples = []
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            logger.info(f"Streaming dataset: {dataset_name}")
            logger.info(f"Streaming mode: {streaming}")

            for row in stream_dataset(
                dataset_name=dataset_name,
                streaming=streaming,
                max_samples=max_samples
            ):
                # Extract relevant fields
                sample = {
                    'code': row.get('content', ''),
                    'language': row.get('language', ''),
                    'repo': row.get('repository', ''),
                    'path': row.get('path', ''),
                }
                samples.append(sample)

                if len(samples) >= max_samples:
                    break

            # Save to CSV
            save_raw_data_to_csv(samples, output_path)

            # Compute checksum
            checksum = compute_file_checksum(output_path)

            logger.info(f"Successfully downloaded {len(samples)} samples")
            logger.info(f"Checksum: {checksum}")

            return output_path, checksum

        except Exception as e:
            retry_count += 1
            logger.warning(f"Attempt {retry_count} failed: {e}")

            if retry_count < max_retries:
                handle_rate_limit(retry_count)
            else:
                raise

    raise RuntimeError("Failed to download dataset after max retries")


def load_raw_data(
    input_path: Path
) -> List[Dict[str, Any]]:
    """
    Load raw data from CSV file.

    Args:
        input_path: Path to input CSV file

    Returns:
        List of dictionaries
    """
    import csv

    logger = logging.getLogger(__name__)

    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(dict(row))

    logger.info(f"Loaded {len(data)} samples from {input_path}")
    return data


def main() -> None:
    """Main entry point for data loader script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Stream GitHub code dataset and save to CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/raw/github-code-sample.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--max-samples',
        type=int,
        default=1000,
        help='Maximum number of samples to download'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='codeparrot/github-code',
        help='HuggingFace dataset name'
    )
    parser.add_argument(
        '--streaming',
        type=bool,
        default=True,
        help='Enable streaming mode (default: True)'
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging()
    logger.info("Starting data loader")

    # Resolve output path relative to project root
    output_path = PROJECT_ROOT / args.output

    try:
        output_path, checksum = download_and_save_sample(
            output_path=output_path,
            dataset_name=args.dataset,
            max_samples=args.max_samples,
            streaming=args.streaming
        )

        logger.info(f"Data loading complete: {output_path}")
        logger.info(f"Checksum: {checksum}")

    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise


if __name__ == '__main__':
    main()