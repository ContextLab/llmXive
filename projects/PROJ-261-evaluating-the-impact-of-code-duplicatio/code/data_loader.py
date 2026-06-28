"""
Data loader module for downloading HuggingFace datasets.

This module handles:
- Streaming download of large datasets (500MB+ subset)
- Rate-limiting and network interruption handling
- Retry logic with exponential backoff
- Data validation and checksum computation

Per T018: Implements streaming mode for codeparrot/github-code dataset.
Per T015a: Handles rate-limiting and network interruptions.
"""
import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple

# Import from project config
from config import (
    get_dataset_name,
    get_random_seed,
    get_streaming_enabled,
    get_memory_limit_mb
)
from checksum_manifest import compute_file_checksum, record_artifact_checksums

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def handle_rate_limit(
    attempt: int,
    max_attempts: int = 5,
    base_delay: float = 1.0
) -> bool:
    """
    Handle rate-limiting errors with exponential backoff.

    Args:
        attempt: Current retry attempt number (0-indexed)
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff

    Returns:
        True if should retry, False if max attempts exceeded
    """
    if attempt >= max_attempts:
        logger.error(f"Max retry attempts ({max_attempts}) exceeded")
        return False

    # Calculate exponential backoff with jitter
    delay = base_delay * (2 ** attempt)
    jitter = random.uniform(0, 0.5)  # Up to 50% jitter
    total_delay = delay + jitter

    logger.info(f"Rate limited. Retrying in {total_delay:.2f}s (attempt {attempt + 1}/{max_attempts})")
    time.sleep(total_delay)
    return True


def handle_network_error(
    error: Exception,
    attempt: int,
    max_attempts: int = 5
) -> bool:
    """
    Handle network interruption errors with retry logic.

    Args:
        error: The exception that was raised
        attempt: Current retry attempt number (0-indexed)
        max_attempts: Maximum number of retry attempts

    Returns:
        True if should retry, False if max attempts exceeded
    """
    if attempt >= max_attempts:
        logger.error(f"Network error after {max_attempts} attempts: {error}")
        return False

    delay = 0.5 * (2 ** attempt)
    logger.warning(f"Network error: {error}. Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_attempts})")
    time.sleep(delay)
    return True


def load_raw_data(
    dataset_name: Optional[str] = None,
    streaming: bool = True,
    split: str = "train",
    max_shards: Optional[int] = None,
    max_retries: int = 5,
    output_path: Optional[str] = None
) -> Any:
    """
    Load data from HuggingFace datasets with streaming support.

    This function handles rate-limiting and network interruptions
    during the download of large datasets (500MB+).

    Args:
        dataset_name: HuggingFace dataset identifier (default: from config)
        streaming: Enable streaming mode for large datasets
        split: Dataset split to load (default: "train")
        max_shards: Maximum number of shards to download
        max_retries: Maximum retry attempts for network errors
        output_path: Path to save downloaded data (optional)

    Returns:
        Dataset or DatasetDict object from HuggingFace datasets
    """
    if dataset_name is None:
        dataset_name = get_dataset_name()

    # Import datasets module here to allow mocking in tests
    try:
        from datasets import load_dataset, Dataset, DatasetDict
    except ImportError:
        logger.error("datasets library not installed. Run: pip install datasets")
        raise

    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Loading dataset: {dataset_name} (streaming={streaming})")

            # Load dataset with streaming for large downloads
            dataset = load_dataset(
                dataset_name,
                split=split,
                streaming=streaming,
                trust_remote_code=True
            )

            # Limit shards if specified
            if max_shards is not None and not streaming:
                # For non-streaming, limit to max_shards
                if isinstance(dataset, Dataset):
                    dataset = dataset.select(range(min(max_shards, len(dataset))))

            # Validate dataset loaded correctly
            if dataset is None:
                raise ValueError("Dataset returned None")

            logger.info(f"Successfully loaded dataset: {dataset}")
            return dataset

        except Exception as e:
            # Check if rate-limited
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str:
                if not handle_rate_limit(attempt, max_retries):
                    raise
            # Check if network error
            elif isinstance(e, (ConnectionError, TimeoutError, OSError)):
                if not handle_network_error(e, attempt, max_retries):
                    raise
            else:
                # Unexpected error - log and re-raise
                logger.error(f"Unexpected error loading dataset: {e}")
                raise

            attempt += 1

    raise RuntimeError(f"Failed to load dataset after {max_retries} attempts")


def stream_dataset(
    dataset: Any,
    batch_size: int = 100,
    max_samples: Optional[int] = None
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream dataset in batches for memory-efficient processing.

    Args:
        dataset: HuggingFace Dataset object
        batch_size: Number of samples per batch
        max_samples: Maximum number of samples to yield (optional)

    Yields:
        Batches of samples as list of dictionaries
    """
    count = 0
    batch = []

    for sample in dataset:
        batch.append(sample)
        count += 1

        if len(batch) >= batch_size:
            yield batch
            batch = []

        if max_samples is not None and count >= max_samples:
            break

    # Yield remaining samples
    if batch:
        yield batch


def save_raw_data_to_csv(
    dataset: Any,
    output_path: str,
    streaming: bool = True,
    max_samples: Optional[int] = None
) -> str:
    """
    Save dataset to CSV file for downstream processing.

    Args:
        dataset: HuggingFace Dataset object
        output_path: Path to output CSV file
        streaming: Whether dataset is in streaming mode
        max_samples: Maximum samples to save (optional)

    Returns:
        Path to saved CSV file
    """
    import csv
    from datetime import datetime

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving raw data to: {output_path}")

    samples_saved = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = None

        for batch in stream_dataset(dataset, batch_size=100, max_samples=max_samples):
            if not batch:
                continue

            # Initialize CSV writer with fieldnames from first sample
            if writer is None:
                fieldnames = list(batch[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

            # Write batch
            writer.writerows(batch)
            samples_saved += len(batch)

            if max_samples is not None and samples_saved >= max_samples:
                break

        # Add metadata comment at end
        f.write(f"# Downloaded: {datetime.now().isoformat()}\n")
        f.write(f"# Samples: {samples_saved}\n")

    logger.info(f"Saved {samples_saved} samples to {output_path}")

    # Compute checksum for artifact tracking
    checksum = compute_file_checksum(output_path)
    logger.info(f"Checksum for {output_path}: {checksum}")

    return str(output_path)


def download_and_save_sample(
    dataset_name: Optional[str] = None,
    output_path: str = "data/raw/github-code-sample.csv",
    max_samples: int = 1000,
    streaming: bool = True
) -> Tuple[str, int]:
    """
    Download dataset sample and save to CSV.

    This is the main entry point for T018 implementation.

    Args:
        dataset_name: HuggingFace dataset identifier
        output_path: Path for output CSV file
        max_samples: Maximum samples to download
        streaming: Enable streaming mode

    Returns:
        Tuple of (output_path, samples_count)
    """
    # Load dataset
    dataset = load_raw_data(
        dataset_name=dataset_name,
        streaming=streaming,
        max_retries=5
    )

    # Save to CSV
    saved_path = save_raw_data_to_csv(
        dataset=dataset,
        output_path=output_path,
        streaming=streaming,
        max_samples=max_samples
    )

    # Count samples
    samples_count = max_samples  # Approximate for streaming

    return saved_path, samples_count


def main():
    """Main entry point for data download."""
    import argparse

    parser = argparse.ArgumentParser(description="Download HuggingFace dataset sample")
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="HuggingFace dataset name (default: from config)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/github-code-sample.csv",
        help="Output CSV file path"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=1000,
        help="Maximum samples to download"
    )
    parser.add_argument(
        "--no-streaming",
        action="store_true",
        help="Disable streaming mode"
    )

    args = parser.parse_args()

    output_path, samples_count = download_and_save_sample(
        dataset_name=args.dataset,
        output_path=args.output,
        max_samples=args.max_samples,
        streaming=not args.no_streaming
    )

    logger.info(f"Download complete: {output_path} ({samples_count} samples)")

    return output_path


if __name__ == "__main__":
    main()