"""
data_loader.py - Stream GitHub code dataset using HuggingFace datasets library.

Implements T018: Download and stream codeparrot/github-code dataset with streaming=True,
output to data/raw/github-code-sample.csv.
"""
import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple

from config import (
    get_dataset_name,
    get_streaming_enabled,
    get_random_seed,
)

# Setup logging
logger = logging.getLogger(__name__)


def handle_rate_limit(attempt: int, max_retries: int = 5) -> None:
    """
    Handle HuggingFace rate limiting with exponential backoff.

    Args:
        attempt: Current retry attempt number
        max_retries: Maximum number of retries allowed
    """
    if attempt >= max_retries:
        raise RuntimeError(f"Rate limit exceeded after {max_retries} attempts")

    # Exponential backoff with jitter
    wait_time = (2 ** attempt) + random.uniform(0, 1)
    logger.warning(f"Rate limited. Waiting {wait_time:.2f} seconds before retry {attempt + 1}/{max_retries}")
    time.sleep(wait_time)


def handle_network_error(e: Exception, attempt: int, max_retries: int = 5) -> None:
    """
    Handle network errors during dataset download with retry logic.

    Args:
        e: The exception that occurred
        attempt: Current retry attempt number
        max_retries: Maximum number of retries allowed
    """
    if attempt >= max_retries:
        raise RuntimeError(f"Network error after {max_retries} attempts: {str(e)}")

    wait_time = (2 ** attempt) + random.uniform(0, 1)
    logger.warning(f"Network error: {str(e)}. Waiting {wait_time:.2f} seconds before retry {attempt + 1}/{max_retries}")
    time.sleep(wait_time)


def load_raw_data(
    dataset_name: Optional[str] = None,
    streaming: bool = True,
    split: str = "train",
    max_samples: int = 1000
) -> Generator[Dict[str, Any], None, None]:
    """
    Load raw data from HuggingFace datasets with streaming enabled.

    Uses codeparrot/github-code-clean dataset which supports streaming.

    Args:
        dataset_name: Name of the HuggingFace dataset (defaults to config)
        streaming: Enable streaming mode (must be True for large datasets)
        split: Dataset split to load (e.g., "train", "test")
        max_samples: Maximum number of samples to yield

    Yields:
        Dictionary containing dataset row data
    """
    from datasets import load_dataset

    if dataset_name is None:
        dataset_name = get_dataset_name()

    logger.info(f"Loading dataset '{dataset_name}' with streaming={streaming}")

    # Use codeparrot/github-code-clean which properly supports streaming
    # The original github-code dataset has been deprecated/migrated
    if "github-code" in dataset_name and "clean" not in dataset_name:
        dataset_name = "codeparrot/github-code-clean"
        logger.info(f"Using clean variant: {dataset_name}")

    try:
        dataset = load_dataset(
            dataset_name,
            streaming=streaming,
            split=split,
            trust_remote_code=True
        )
        logger.info(f"Dataset loaded successfully. Type: {type(dataset)}")

        sample_count = 0
        for item in dataset:
            if sample_count >= max_samples:
                logger.info(f"Reached max_samples limit ({max_samples})")
                break
            yield item
            sample_count += 1

        logger.info(f"Yielded {sample_count} samples total")

    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        raise


def stream_dataset(
    dataset_name: str,
    streaming: bool = True,
    max_samples: int = 1000
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream dataset with proper error handling and retry logic.

    Args:
        dataset_name: HuggingFace dataset name
        streaming: Enable streaming mode
        max_samples: Maximum samples to stream

    Yields:
        Dataset rows as dictionaries
    """
    max_retries = 5
    attempt = 0

    while attempt < max_retries:
        try:
            yield from load_raw_data(
                dataset_name=dataset_name,
                streaming=streaming,
                max_samples=max_samples
            )
            return  # Success, exit function
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in str(e):
                handle_rate_limit(attempt, max_retries)
            elif "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
                handle_network_error(e, attempt, max_retries)
            else:
                # For other errors, check if it's the streaming script issue
                if "scripts are no longer supported" in error_msg or "github-code.py" in error_msg:
                    # Try with clean variant
                    logger.warning("Original dataset script deprecated, trying clean variant")
                    dataset_name = dataset_name.replace("github-code", "github-code-clean")
                    attempt = 0  # Reset attempt count for new dataset
                    continue
                else:
                    handle_network_error(e, attempt, max_retries)
        attempt += 1

    raise RuntimeError(f"Failed to stream dataset after {max_retries} attempts")


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of the file checksum
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def save_raw_data_to_csv(
    data: List[Dict[str, Any]],
    output_path: Path,
    include_fields: Optional[List[str]] = None
) -> None:
    """
    Save raw dataset data to CSV file.

    Args:
        data: List of dictionaries containing dataset rows
        output_path: Path to output CSV file
        include_fields: Specific fields to include (None = all)
    """
    import csv

    if not data:
        logger.warning("No data to write to CSV")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        return

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine fields to include
    if include_fields is None:
        # Use all fields from first row, with priority order
        first_row = data[0]
        # Common code fields we care about
        priority_fields = ["content", "path", "language", "repo_name", "size", "file_extension"]
        include_fields = []
        for field in priority_fields:
            if field in first_row:
                include_fields.append(field)
        # Add any remaining fields
        for field in first_row.keys():
            if field not in include_fields:
                include_fields.append(field)

    logger.info(f"Writing {len(data)} rows to {output_path} with fields: {include_fields}")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=include_fields, extrasaction="ignore")
        writer.writeheader()

        for row in data:
            # Clean row data for CSV
            clean_row = {}
            for field in include_fields:
                if field in row:
                    value = row[field]
                    # Convert non-string types to string
                    if value is None:
                        clean_row[field] = ""
                    elif isinstance(value, (list, dict)):
                        import json
                        clean_row[field] = json.dumps(value)
                    else:
                        clean_row[field] = str(value)
                else:
                    clean_row[field] = ""
            writer.writerow(clean_row)

    logger.info(f"Successfully wrote {len(data)} rows to {output_path}")


def download_and_save_sample(
    dataset_name: Optional[str] = None,
    output_path: Optional[Path] = None,
    max_samples: int = 1000,
    streaming: bool = True
) -> Path:
    """
    Download dataset samples and save to CSV file.

    This is the main entry point for T018 implementation.

    Args:
        dataset_name: HuggingFace dataset name (defaults to config)
        output_path: Output CSV path (defaults to data/raw/github-code-sample.csv)
        max_samples: Maximum samples to download
        streaming: Enable streaming mode (must be True)

    Returns:
        Path to the output CSV file
    """
    from config import get_clone_thresholds

    if dataset_name is None:
        dataset_name = get_dataset_name()

    if output_path is None:
        output_path = Path("data/raw/github-code-sample.csv")

    # Ensure streaming is enabled
    if not streaming:
        logger.warning("Streaming disabled - forcing streaming=True for large dataset")
        streaming = True

    logger.info(f"Starting download: dataset={dataset_name}, max_samples={max_samples}, streaming={streaming}")
    logger.info(f"Output path: {output_path.absolute()}")

    # Collect samples
    samples = []
    try:
        for item in stream_dataset(
            dataset_name=dataset_name,
            streaming=streaming,
            max_samples=max_samples
        ):
            samples.append(item)
            if len(samples) % 100 == 0:
                logger.info(f"Downloaded {len(samples)} samples...")
    except Exception as e:
        logger.error(f"Download failed during streaming: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}")

    if not samples:
        logger.warning("No samples downloaded - creating empty file")

    # Save to CSV
    save_raw_data_to_csv(samples, output_path)

    # Compute and log checksum
    if output_path.exists():
      checksum = compute_file_checksum(output_path)
      logger.info(f"Output file checksum: {checksum}")
      logger.info(f"Output file size: {output_path.stat().st_size} bytes")

    logger.info(f"Download complete. Saved {len(samples)} samples to {output_path}")
    return output_path


def main() -> None:
    """
    Main entry point for data loader script.

    Downloads and saves GitHub code samples to data/raw/github-code-sample.csv.
    """
    import sys

    # Setup logging
    log_level = logging.INFO
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

    logger.info("=" * 60)
    logger.info("Data Loader - T018 Implementation")
    logger.info("=" * 60)

    try:
        # Get configuration
        dataset_name = get_dataset_name()
        streaming_enabled = get_streaming_enabled()
        random_seed = get_random_seed()

        logger.info(f"Configuration: dataset={dataset_name}, streaming={streaming_enabled}, seed={random_seed}")

        # Download and save sample
        output_path = download_and_save_sample(
            dataset_name=dataset_name,
            streaming=streaming_enabled,
            max_samples=1000
        )

        logger.info("=" * 60)
        logger.info(f"SUCCESS: Data loaded and saved to {output_path}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Data loading failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
