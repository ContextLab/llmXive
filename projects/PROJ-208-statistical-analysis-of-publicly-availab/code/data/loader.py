"""
Streaming Data Loader for GitHub Issues Dataset.

Implements memory-efficient streaming of the full real dataset from HuggingFace
using the `datasets` library's streaming mode. This ensures memory usage stays
below 7GB regardless of dataset size.

Per Constitution Principle II and Task T047 requirements:
- Uses datasets.load_dataset(..., streaming=True)
- Processes data in chunks/iteratively
- FAILS LOUDLY if the real source is unavailable (no synthetic fallback)
- If streaming is impossible due to environment constraints, raises an exception
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Generator, Optional, Iterator

try:
    from datasets import load_dataset
except ImportError:
    logging.error("The 'datasets' library is required. Install with: pip install datasets")
    sys.exit(1)

from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# HuggingFace Dataset Configuration
# Verified real source: akhousker/github-issues (as per Plan Phase 0.5 and task context)
HF_DATASET_NAME = "akhousker/github-issues"
HF_DATASET_SPLIT = "train"  # or appropriate split if available

# Memory constraints
MAX_MEMORY_GB = 7.0


def load_streaming_dataset(
    dataset_name: str = HF_DATASET_NAME,
    split: str = HF_DATASET_SPLIT,
    streaming: bool = True
) -> Iterator[Dict[str, Any]]:
    """
    Load the GitHub issues dataset in streaming mode to ensure low memory footprint.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to load (e.g., 'train', 'test').
        streaming: Whether to enable streaming mode. MUST be True for memory safety.

    Returns:
        An iterator yielding one row (dict) at a time from the dataset.

    Raises:
        ConnectionError: If the dataset cannot be fetched from HuggingFace.
        ValueError: If streaming is disabled or the dataset format is unsupported.
        RuntimeError: If the real source is unavailable and no fallback is permitted.
    """
    if not streaming:
        raise ValueError(
            "Streaming mode is REQUIRED for T047 to maintain memory usage <7GB. "
            "Set streaming=True."
        )

    logger.info(f"Attempting to stream dataset: {dataset_name} (split={split})...")

    try:
        # Load dataset in streaming mode
        # This does NOT download the full dataset to disk; it streams rows on demand
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            trust_remote_code=False  # Security best practice
        )
        
        logger.info(f"Successfully initialized stream for {dataset_name}.")
        return iter(dataset)

    except Exception as e:
        # FAIL LOUDLY: Do not fall back to synthetic data
        error_msg = (
            f"CRITICAL: Failed to load real dataset '{dataset_name}' from HuggingFace. "
            f"Streaming failed with error: {type(e).__name__}: {e}. "
            "Per T047 and Constitution Principle II, NO synthetic fallback is allowed. "
            "The pipeline must fail here to indicate a missing real data source."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def process_stream_in_chunks(
    stream: Iterator[Dict[str, Any]],
    chunk_size: int = 1000
) -> Generator[list, None, None]:
    """
    Process the streaming dataset in configurable chunks.
    
    This allows downstream tasks (like aggregation or filtering) to handle
    data in manageable batches without loading everything into memory.

    Args:
        stream: The iterator from load_streaming_dataset.
        chunk_size: Number of rows per chunk.

    Yields:
        Lists of rows (dictionaries) of size `chunk_size`.
    """
    chunk = []
    count = 0
    for row in stream:
        chunk.append(row)
        count += 1
        if count >= chunk_size:
            yield chunk
            chunk = []
            count = 0
    
    # Yield remaining rows
    if chunk:
        yield chunk


def get_dataset_statistics(
    stream: Iterator[Dict[str, Any]],
    sample_limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate basic statistics over the streaming dataset without loading it all.
    
    This is useful for quick validation (e.g., row count estimation, column presence)
    while maintaining low memory usage. If the dataset is too large to count fully
    within time/memory constraints, it can stop after a sample_limit.

    Args:
        stream: The dataset iterator.
        sample_limit: Optional max number of rows to process for stats.

    Returns:
        Dictionary with 'total_rows_processed', 'columns', 'sample_row'.
    """
    stats = {
        "total_rows_processed": 0,
        "columns": None,
        "sample_row": None,
        "error": None
    }

    try:
        for i, row in enumerate(stream):
            if stats["columns"] is None:
                stats["columns"] = list(row.keys())
                stats["sample_row"] = {k: str(v)[:100] for k, v in row.items()}
            
            stats["total_rows_processed"] += 1

            if sample_limit and stats["total_rows_processed"] >= sample_limit:
                logger.info(f"Reached sample limit of {sample_limit} rows for statistics.")
                break
    except Exception as e:
        stats["error"] = str(e)
        logger.error(f"Error while calculating statistics: {e}")

    return stats


def main():
    """
    Main entry point for testing the streaming loader.
    
    This script attempts to stream the dataset, calculates basic statistics,
    and prints a summary. It serves as a verification that the streaming
    loader works correctly with real data.
    """
    config = get_config()
    logger.info("Starting Streaming Data Loader (T047) verification...")

    # 1. Load the stream
    try:
        dataset_stream = load_streaming_dataset(
            dataset_name=HF_DATASET_NAME,
            split=HF_DATASET_SPLIT,
            streaming=True
        )
    except RuntimeError as e:
        # Re-raise the loud failure
        raise e
    except Exception as e:
        logger.error(f"Unexpected error initializing stream: {e}")
        raise

    # 2. Process a sample to verify connectivity and schema
    # We limit to 1000 rows for a quick verification run
    logger.info("Processing first 1000 rows to verify stream...")
    stats = get_dataset_statistics(dataset_stream, sample_limit=1000)

    if stats["error"]:
        logger.error(f"Stream processing failed: {stats['error']}")
        sys.exit(1)

    logger.info(f"Verification Successful:")
    logger.info(f"  - Rows processed: {stats['total_rows_processed']}")
    logger.info(f"  - Columns available: {stats['columns']}")
    if stats['sample_row']:
        logger.info(f"  - Sample row preview: {stats['sample_row']}")
    
    logger.info("Streaming loader is functional and connected to real data source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
