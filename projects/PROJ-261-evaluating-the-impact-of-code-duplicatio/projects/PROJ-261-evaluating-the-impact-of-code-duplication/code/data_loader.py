"""
Data loader module for streaming codeparrot/github-code dataset.

This module implements streaming download of the codeparrot/github-code dataset
using the HuggingFace datasets library with streaming mode enabled.

Output:
    data/raw/github-code-sample.csv - CSV file with sampled code segments
"""

import csv
import logging
import os
import time
from pathlib import Path
from typing import Generator, Dict, Any, Optional

from datasets import load_dataset

from config import get_config
from parse_failure_logger import init_logger, log_parse_failure

# Configure module logger
logger = logging.getLogger(__name__)


def stream_code_dataset(
    dataset_name: str = "codeparrot/github-code",
    streaming: bool = True,
    language: Optional[str] = "python",
    max_samples: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream code segments from a HuggingFace dataset.

    Args:
        dataset_name: Name of the HuggingFace dataset to load
        streaming: Whether to use streaming mode (True for memory efficiency)
        language: Filter by programming language if supported
        max_samples: Maximum number of samples to yield (None for unlimited)

    Yields:
        Dictionary containing code segment data with 'content' field

    Raises:
        Exception: On network errors or dataset loading failures
    """
    config = get_config()

    logger.info(f"Loading dataset '{dataset_name}' with streaming={streaming}")

    try:
        # Load dataset with streaming mode enabled as required by T018
        dataset = load_dataset(
            dataset_name,
            streaming=streaming,
            trust_remote_code=True
        )

        # Get the split iterator - use 'train' split if available
        if "train" in dataset:
            split_name = "train"
        else:
            split_name = list(dataset.keys())[0]

        logger.info(f"Using split: {split_name}")
        split = dataset[split_name]

        # Apply language filter if specified and supported
        if language and hasattr(split, 'filter'):
            logger.info(f"Filtering by language: {language}")
            split = split.filter(lambda x: x.get('language', '').lower() == language.lower())

        sample_count = 0
        for sample in split:
            if max_samples and sample_count >= max_samples:
                logger.info(f"Reached max_samples limit: {max_samples}")
                break

            # Validate sample has required content
            if 'content' in sample and sample['content']:
                sample_count += 1
                yield sample
            else:
                # Log parse failure for invalid samples
                log_parse_failure(
                    reason="missing_content",
                    file_path=sample.get('path', 'unknown'),
                    details=f"Sample missing 'content' field: {sample.keys()}"
                )

    except Exception as e:
        logger.error(f"Dataset loading failed: {type(e).__name__}: {e}")
        raise


def save_streamed_data(
    output_path: str,
    dataset_name: str = "codeparrot/github-code",
    streaming: bool = True,
    language: Optional[str] = "python",
    max_bytes: Optional[int] = 500 * 1024 * 1024,  # 500 MB default
    max_samples: Optional[int] = None
) -> int:
    """
    Stream data from dataset and save to CSV file.

    Args:
        output_path: Path to output CSV file
        dataset_name: HuggingFace dataset name
        streaming: Enable streaming mode (must be True per T018)
        language: Filter by programming language
        max_bytes: Maximum total bytes to download (None for unlimited)
        max_samples: Maximum number of samples (None for unlimited)

    Returns:
        Number of samples saved

    Raises:
        RuntimeError: If streaming is not enabled
    """
    # Verify streaming is enabled as required by task T018
    if not streaming:
        raise RuntimeError("streaming must be True for T018 - memory constraints require streaming")

    config = get_config()
    output_file = Path(output_path)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting data download to: {output_path}")
    logger.info(f"Dataset: {dataset_name}, streaming={streaming}")

    total_bytes = 0
    sample_count = 0
    start_time = time.time()

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = None

            for sample in stream_code_dataset(
                dataset_name=dataset_name,
                streaming=streaming,
                language=language,
                max_samples=max_samples
            ):
                # Estimate sample size and check byte limit
                sample_size = len(str(sample))
                if max_bytes and (total_bytes + sample_size) > max_bytes:
                    logger.info(f"Reached byte limit: {total_bytes} / {max_bytes}")
                    break

                # Write first sample to determine fieldnames
                if writer is None:
                    fieldnames = list(sample.keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    logger.info(f"CSV fieldnames: {fieldnames}")

                # Write sample
                writer.writerow(sample)
                total_bytes += sample_size
                sample_count += 1

                # Progress logging every 100 samples
                if sample_count % 100 == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"Progress: {sample_count} samples, {total_bytes / 1024 / 1024:.2f} MB, {elapsed:.1f}s")

        elapsed = time.time() - start_time
        logger.info(f"Download complete: {sample_count} samples, {total_bytes / 1024 / 1024:.2f} MB in {elapsed:.1f}s")

        return sample_count

    except Exception as e:
        logger.error(f"Failed to save data: {type(e).__name__}: {e}")
        # Clean up partial file on failure
        if output_file.exists():
            output_file.unlink()
        raise


def main():
    """
    Main entry point for data loader script.

    Downloads codeparrot/github-code dataset with streaming enabled
    and saves to data/raw/github-code-sample.csv.
    """
    # Initialize logging
    init_logger()

    config = get_config()

    # Output path as specified in tasks.md
    output_path = "projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/raw/github-code-sample.csv"

    # Parameters from config with task-specific overrides
    dataset_name = config.get('dataset_name', 'codeparrot/github-code')
    streaming = True  # Required by T018
    language = config.get('language', 'python')
    max_bytes = config.get('max_corpus_bytes', 500 * 1024 * 1024)

    logger.info("=" * 60)
    logger.info("T018: Data Loader - Streaming codeparrot/github-code")
    logger.info("=" * 60)
    logger.info(f"Output: {output_path}")
    logger.info(f"Streaming enabled: {streaming}")
    logger.info(f"Max corpus size: {max_bytes / 1024 / 1024:.0f} MB")

    try:
        sample_count = save_streamed_data(
            output_path=output_path,
            dataset_name=dataset_name,
            streaming=streaming,
            language=language,
            max_bytes=max_bytes
        )

        logger.info(f"SUCCESS: Downloaded {sample_count} samples to {output_path}")
        return 0

    except Exception as e:
        logger.error(f"FAILED: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
