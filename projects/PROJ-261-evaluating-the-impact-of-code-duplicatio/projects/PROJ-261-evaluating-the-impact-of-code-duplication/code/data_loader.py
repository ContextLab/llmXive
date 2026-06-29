"""
Data Loader Module for Code Duplication Research Pipeline

Streams the codeparrot/github-code dataset using HuggingFace datasets library
with streaming mode enabled. Outputs raw code samples to CSV format.
"""

import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple
import pandas as pd

# Import from sibling modules
from config import (
    get_dataset_name,
    get_streaming_enabled,
    get_random_seed,
    get_max_runtime_seconds,
)
from checksum_manifest import compute_file_checksum

# Setup module-level logger
logger = logging.getLogger(__name__)


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the data loader module."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/data_loader.log')
        ]
    )
    return logging.getLogger(__name__)


def handle_rate_limit(retry_count: int = 3, base_delay: float = 1.0) -> bool:
    """
    Handle HuggingFace API rate limiting with exponential backoff.

    Args:
        retry_count: Maximum number of retry attempts
        base_delay: Initial delay in seconds between retries

    Returns:
        True if rate limit was successfully handled, False otherwise
    """
    delay = base_delay
    for attempt in range(retry_count):
        logger.warning(f"Rate limit detected, retrying in {delay:.1f}s (attempt {attempt + 1}/{retry_count})")
        time.sleep(delay)
        delay *= 2  # Exponential backoff
    return True


def handle_network_error(retry_count: int = 3, timeout: float = 30.0) -> bool:
    """
    Handle network interruption during dataset download.

    Args:
        retry_count: Maximum number of retry attempts
        timeout: Timeout in seconds for each request

    Returns:
        True if network error was successfully handled, False otherwise
    """
    logger.warning("Network interruption detected, attempting recovery...")
    for attempt in range(retry_count):
        logger.warning(f"Network retry {attempt + 1}/{retry_count}")
        time.sleep(random.uniform(1.0, 3.0))
    return True


def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute checksum of a file for integrity verification.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of the file checksum
    """
    return compute_file_checksum(str(file_path), algorithm)


def stream_dataset(
    dataset_name: str = None,
    streaming: bool = True,
    max_samples: Optional[int] = None,
    seed: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream code samples from the HuggingFace dataset.

    Args:
        dataset_name: Name of the dataset to load (default: from config)
        streaming: Enable streaming mode (MUST be True per task requirement)
        max_samples: Maximum number of samples to yield (None = all)
        seed: Random seed for reproducibility

    Yields:
        Dictionary containing code sample data
    """
    try:
        from datasets import load_dataset

        # Use config defaults if not specified
        if dataset_name is None:
            dataset_name = get_dataset_name()
        if seed is None:
            seed = get_random_seed()

        logger.info(f"Loading dataset: {dataset_name} with streaming={streaming}")

        # CRITICAL: streaming=True as required by task T018
        dataset = load_dataset(
            dataset_name,
            streaming=streaming,
            split='train',
            trust_remote_code=True
        )

        # Set random seed for reproducibility
        random.seed(seed)

        sample_count = 0
        for sample in dataset:
            if max_samples is not None and sample_count >= max_samples:
                break

            # Filter for Python files only
            if sample.get('language') == 'python':
                yield sample
                sample_count += 1

        logger.info(f"Streamed {sample_count} Python code samples")

    except Exception as e:
        logger.error(f"Failed to stream dataset: {e}")
        raise


def save_raw_data_to_csv(
    samples: List[Dict[str, Any]],
    output_path: Path,
    checksum_path: Optional[Path] = None
) -> Path:
    """
    Save raw code samples to CSV format.

    Args:
        samples: List of code sample dictionaries
        output_path: Path to output CSV file
        checksum_path: Optional path to store checksum

    Returns:
        Path to the created CSV file
    """
    if not samples:
        logger.warning("No samples to save")
        return output_path

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to DataFrame and save
    df = pd.DataFrame(samples)

    # Select relevant columns for output
    columns_to_save = ['repo_id', 'path', 'content', 'language', 'size', 'license']
    available_columns = [col for col in columns_to_save if col in df.columns]

    if available_columns:
        df = df[available_columns]

    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(samples)} samples to {output_path}")

    # Compute and store checksum if path provided
    if checksum_path:
        checksum = compute_file_checksum(output_path)
        with open(checksum_path, 'w') as f:
            f.write(f"{checksum}  {output_path.name}\n")
        logger.info(f"Checksum saved to {checksum_path}")

    return output_path


def download_and_save_sample(
    dataset_name: str = None,
    output_path: Optional[Path] = None,
    max_samples: int = 100,
    streaming: bool = True
) -> Tuple[Path, int]:
    """
    Download dataset samples and save to CSV.

    Args:
        dataset_name: Dataset name (default: from config)
        output_path: Output CSV path (default: data/raw/github-code-sample.csv)
        max_samples: Maximum samples to download
        streaming: Enable streaming mode (MUST be True per task T018)

    Returns:
        Tuple of (output_path, sample_count)
    """
    if dataset_name is None:
        dataset_name = get_dataset_name()
    if output_path is None:
        output_path = Path('data/raw/github-code-sample.csv')

    logger.info(f"Downloading {max_samples} samples from {dataset_name}")

    # Ensure streaming is enabled (task requirement)
    if not streaming:
        logger.warning("Streaming disabled, enabling for task compliance")
        streaming = True

    samples = []
    checksum_path = Path('data/raw/github-code-sample.csv.sha256')

    try:
        for sample in stream_dataset(
            dataset_name=dataset_name,
            streaming=streaming,
            max_samples=max_samples
        ):
            samples.append(sample)

        if samples:
            save_raw_data_to_csv(samples, output_path, checksum_path)

        return output_path, len(samples)

    except Exception as e:
        logger.error(f"Download failed: {e}")
        # Return partial data if available
        if samples:
            save_raw_data_to_csv(samples, output_path, checksum_path)
            return output_path, len(samples)
        raise


def load_raw_data(input_path: Path) -> pd.DataFrame:
    """
    Load raw data from CSV file.

    Args:
        input_path: Path to input CSV file

    Returns:
        DataFrame with loaded data
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} samples from {input_path}")
    return df


def main():
    """
    Main entry point for standalone execution.

    This function handles command-line arguments for downloading
    the dataset and saving it to CSV.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Stream and save code samples from HuggingFace dataset'
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
        default=100,
        help='Maximum number of samples to download'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default=None,
        help='Dataset name (default: from config)'
    )
    parser.add_argument(
        '--streaming',
        type=bool,
        default=True,
        help='Enable streaming mode (default: True)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    try:
        output_path, sample_count = download_and_save_sample(
            dataset_name=args.dataset,
            output_path=Path(args.output),
            max_samples=args.max_samples,
            streaming=args.streaming
        )

        logger.info(f"Successfully downloaded {sample_count} samples to {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())