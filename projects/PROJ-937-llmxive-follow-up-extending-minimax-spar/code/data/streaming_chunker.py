"""
Streaming Chunker for RULER Dataset.

Implements chunked processing of the RULER dataset using HuggingFace's streaming API
to ensure memory safety and compliance with FR-007 (7GB RAM limit).

This module explicitly logs the streaming configuration to provide a verifiable record
that the full dataset is processed in chunks rather than loaded into memory.
"""
import logging
from typing import Generator, Dict, Any, Optional, Iterator
from datasets import load_dataset
from utils.logger import get_logger_for_task

# Initialize logger for this module
logger = get_logger_for_task("T052_streaming_chunker")

def stream_chunker(
    dataset_name: str = "lmsys/lmsys-ruler",
    split: str = "train",
    chunk_size: int = 100,
    streaming: bool = True,
    **load_kwargs
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream and chunk the RULER dataset.
    
    This function explicitly logs the streaming configuration to satisfy T052 requirements:
    - Logs the `streaming=True` flag
    - Logs the `chunk_size` used
    - Provides verifiable evidence that data is processed in chunks
    
    Args:
        dataset_name: HuggingFace dataset identifier
        split: Dataset split to load (e.g., 'train', 'validation')
        chunk_size: Number of samples per chunk
        streaming: MUST be True for memory safety. Logs warning if False.
        **load_kwargs: Additional arguments passed to load_dataset
    
    Yields:
        Dict containing a chunk of dataset samples (list of dicts)
    
    Raises:
        ValueError: If streaming=False is passed (violates memory constraints)
        RuntimeError: If dataset fetch fails (fails loudly, no synthetic fallback)
    """
    
    # T052: Explicit logging of streaming configuration
    logger.info(f"Initializing streaming chunker for dataset: {dataset_name}")
    logger.info(f"Stream configuration: streaming={streaming}, chunk_size={chunk_size}")
    
    # Enforce streaming mode for memory safety
    if not streaming:
        error_msg = (
            "CRITICAL: Streaming mode disabled. This violates FR-007 (7GB RAM limit). "
            "The streaming_chunker MUST run with streaming=True to process the full dataset "
            "in chunks. Aborting to prevent OOM crash."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Fetching dataset with streaming=True from HuggingFace: {dataset_name}")
    
    try:
        # Load dataset in streaming mode
        # This does NOT download the full dataset to disk or RAM
        ds = load_dataset(
            dataset_name,
            split=split,
            streaming=True,
            trust_remote_code=True,
            **load_kwargs
        )
        
        logger.info(f"Successfully initialized streaming iterator for {dataset_name}/{split}")
        logger.info("Starting chunked iteration over dataset...")
        
        # Iterate and yield chunks
        current_chunk: list = []
        sample_count = 0
        
        for sample in ds:
            current_chunk.append(sample)
            sample_count += 1
            
            if len(current_chunk) >= chunk_size:
                logger.debug(f"Yielding chunk of {len(current_chunk)} samples (total processed: {sample_count})")
                yield current_chunk
                current_chunk = []
        
        # Yield remaining samples as final chunk
        if current_chunk:
            logger.debug(f"Yielding final chunk of {len(current_chunk)} samples (total processed: {sample_count})")
            yield current_chunk
        
        logger.info(f"Chunked iteration complete. Total samples processed: {sample_count}")
        
    except Exception as e:
        # T043 compliance: Fail loudly, no synthetic fallback
        error_msg = (
            f"CRITICAL: Failed to fetch real RULER dataset from HuggingFace. "
            f"Streaming load failed with error: {type(e).__name__}: {e}. "
            f"No synthetic data fallback available. Aborting execution."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def process_dataset_in_chunks(
    dataset_name: str = "lmsys/lmsys-ruler",
    split: str = "train",
    chunk_size: int = 100,
    process_fn: Optional[callable] = None,
    **kwargs
) -> Dict[str, int]:
    """
    Process the dataset in chunks with a user-provided function.
    
    Args:
        dataset_name: HuggingFace dataset identifier
        split: Dataset split to load
        chunk_size: Number of samples per chunk
        process_fn: Function to apply to each chunk (chunk: List[Dict] -> Any)
        **kwargs: Additional arguments for stream_chunker
    
    Returns:
        Dict with processing statistics
    """
    stats = {
        "total_chunks": 0,
        "total_samples": 0,
        "streaming_enabled": True,
        "chunk_size": chunk_size
    }
    
    logger.info(f"Starting chunked processing with chunk_size={chunk_size}")
    
    for chunk in stream_chunker(
        dataset_name=dataset_name,
        split=split,
        chunk_size=chunk_size,
        streaming=True,
        **kwargs
    ):
        stats["total_chunks"] += 1
        stats["total_samples"] += len(chunk)
        
        if process_fn:
            try:
                process_fn(chunk)
            except Exception as e:
                logger.error(f"Error processing chunk {stats['total_chunks']}: {e}")
                raise
        
        # Log progress every 10 chunks
        if stats["total_chunks"] % 10 == 0:
            logger.info(
                f"Progress: {stats['total_chunks']} chunks processed, "
                f"{stats['total_samples']} samples total"
            )
    
    logger.info(
        f"Processing complete. Chunks: {stats['total_chunks']}, "
        f"Samples: {stats['total_samples']}, "
        f"Streaming: {stats['streaming_enabled']}"
    )
    
    return stats

def main():
    """
    Main entry point for testing the streaming chunker.
    
    This function demonstrates the streaming chunker with explicit logging
    of the streaming configuration to satisfy T052 requirements.
    """
    logger.info("=== T052 Streaming Chunker Test ===")
    logger.info("Testing streaming chunker with explicit logging of configuration...")
    
    # Test configuration
    test_config = {
        "dataset_name": "lmsys/lmsys-ruler",
        "split": "train",
        "chunk_size": 50
    }
    
    logger.info(f"Test configuration: {test_config}")
    
    try:
        # Run the chunker
        stats = process_dataset_in_chunks(**test_config)
        
        logger.info("=== T052 Test Results ===")
        logger.info(f"Streaming enabled: {stats['streaming_enabled']}")
        logger.info(f"Chunk size used: {stats['chunk_size']}")
        logger.info(f"Total chunks processed: {stats['total_chunks']}")
        logger.info(f"Total samples processed: {stats['total_samples']}")
        logger.info("SUCCESS: Streaming chunker executed with verified configuration.")
        
    except Exception as e:
        logger.error(f"FAILED: {type(e).__name__}: {e}")
        raise

if __name__ == "__main__":
    main()