"""
GSM8K Data Loader with Streaming Support.

This module implements a streaming data loader for the GSM8K dataset from HuggingFace.
It is designed to process large datasets without loading them entirely into RAM,
adhering to the strict memory constraints (7GB) of the CPU-only execution environment.

Key Features:
- Streaming mode to avoid full dataset download into memory.
- Chunked iteration for batch processing.
- Strict "fail loudly" policy: raises exceptions if real data fetch fails.
- No synthetic fallbacks.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List

# Import real dependencies
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "gsm8k"
DATASET_CONFIG = "main"
SPLIT_NAME = "train"
MIN_PROBLEMS = 1000
CHUNK_SIZE = 100

class GSM8KStreamingLoader:
    """
    A streaming loader for the GSM8K dataset.

    This class wraps the HuggingFace datasets streaming functionality to provide
    an iterator over the dataset in chunks, ensuring memory efficiency.
    """

    def __init__(
        self,
        split: str = SPLIT_NAME,
        config: str = DATASET_CONFIG,
        chunk_size: int = CHUNK_SIZE
    ):
        """
        Initialize the streaming loader.

        Args:
            split: The dataset split to load (default: 'train').
            config: The dataset configuration (default: 'main').
            chunk_size: Number of examples to yield per iteration chunk.
        """
        self.split = split
        self.config = config
        self.chunk_size = chunk_size
        self.dataset = None
        self._streamer = None

    def load(self) -> Iterator[Dict[str, Any]]:
        """
        Load the dataset in streaming mode.

        This method fetches the dataset from HuggingFace Hub in streaming mode.
        It raises an exception immediately if the fetch fails, adhering to the
        "fail loudly" policy.

        Returns:
            An iterator yielding dictionaries representing dataset examples.

        Raises:
            ConnectionError: If the dataset cannot be fetched from HuggingFace.
            RuntimeError: If the dataset is empty or invalid.
        """
        logger.info(f"Loading GSM8K dataset in streaming mode: {self.split}")
        try:
            # Use streaming=True to avoid downloading the full dataset
            self.dataset = load_dataset(
                DATASET_NAME,
                self.config,
                split=self.split,
                streaming=True,
                trust_remote_code=True
            )
        except Exception as e:
            logger.error(f"Failed to load GSM8K dataset: {e}")
            raise ConnectionError(
                f"Failed to fetch real GSM8K data from HuggingFace. "
                f"Verify internet connection and dataset availability. Error: {e}"
            ) from e

        if self.dataset is None:
            raise RuntimeError("Dataset stream is None after initialization.")

        logger.info("Dataset stream initialized successfully.")
        return iter(self.dataset)

    def iter_chunks(self) -> Iterator[List[Dict[str, Any]]]:
        """
        Iterate over the dataset in chunks.

        This method yields lists of examples, where each list contains
        up to `chunk_size` examples. This is useful for batch processing.

        Yields:
            A list of dictionaries, each representing a batch of examples.
        """
        if self.dataset is None:
            self.load()

        buffer = []
        for example in self.dataset:
            buffer.append(example)
            if len(buffer) >= self.chunk_size:
                yield buffer
                buffer = []

        # Yield remaining examples
        if buffer:
            yield buffer

    def get_sample(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get a small sample of examples for inspection.

        This method consumes a small number of examples from the stream
        for debugging or validation purposes.

        Args:
            n: Number of examples to retrieve.

        Returns:
            A list of n examples.
        """
        if self.dataset is None:
            self.load()

        sample = []
        for i, example in enumerate(self.dataset):
            if i >= n:
                break
            sample.append(example)
        return sample

def load_gsm8k_streaming(
    split: str = SPLIT_NAME,
    chunk_size: int = CHUNK_SIZE
) -> Iterator[List[Dict[str, Any]]]:
    """
    Convenience function to load GSM8K in streaming mode and iterate in chunks.

    Args:
        split: Dataset split to load.
        chunk_size: Size of each chunk.

    Returns:
        An iterator yielding chunks of examples.
    """
    loader = GSM8KStreamingLoader(split=split, chunk_size=chunk_size)
    loader.load()  # Initialize stream
    return loader.iter_chunks()

def verify_data_integrity(
    loader: GSM8KStreamingLoader,
    min_examples: int = MIN_PROBLEMS
) -> bool:
    """
    Verify that the loaded dataset contains at least the minimum required examples.

    This function iterates through the stream to count examples without
    loading the entire dataset into memory.

    Args:
        loader: The streaming loader instance.
        min_examples: Minimum number of examples required.

    Returns:
        True if the dataset meets the minimum requirement, False otherwise.

    Raises:
        RuntimeError: If the dataset has fewer than min_examples.
    """
    count = 0
    for chunk in loader.iter_chunks():
        count += len(chunk)
        if count >= min_examples:
            logger.info(f"Verified dataset integrity: {count} examples found (>= {min_examples}).")
            return True

    if count < min_examples:
        error_msg = f"Dataset integrity check failed: Found {count} examples, required {min_examples}."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    return True

def main():
    """
    Main function to demonstrate the streaming loader.

    This function loads the GSM8K dataset in streaming mode, verifies its integrity,
    and prints a sample of the data.
    """
    logger.info("Starting GSM8K Streaming Loader Demo")

    try:
        loader = GSM8KStreamingLoader()
        loader.load()

        # Verify integrity
        verify_data_integrity(loader, min_examples=MIN_PROBLEMS)

        # Get a sample
        sample = loader.get_sample(5)
        logger.info(f"Sample data retrieved: {len(sample)} examples")

        # Print sample structure
        if sample:
            logger.info(f"Sample keys: {sample[0].keys()}")
            logger.info(f"Sample first question (truncated): {sample[0]['question'][:100]}...")

        logger.info("GSM8K Streaming Loader Demo completed successfully.")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
