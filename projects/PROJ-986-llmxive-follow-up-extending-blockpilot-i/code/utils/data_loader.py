from typing import Iterator, Dict, Any, Optional, Literal
from datasets import load_dataset
import logging
import json
from pathlib import Path
import os
import time

logger = logging.getLogger(__name__)

# Ensure output directory exists for logging
LOG_DIR = Path("data/processed")
LOG_DIR.mkdir(parents=True, exist_ok=True)
STREAMING_LOG_PATH = LOG_DIR / "streaming_config.log"

def _log_streaming_config(dataset_name: str, split: str, strategy: str, estimated_size_mb: Optional[float] = None, sample_count: int = 0):
    """
    Logs streaming configuration to data/processed/streaming_config.log.
    This ensures explicit logging of sample size and streaming strategy as required.
    """
    log_entry = {
        "dataset": dataset_name,
        "split": split,
        "strategy": strategy,
        "estimated_size_mb": estimated_size_mb,
        "sample_count_processed": sample_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Append to log file
    with open(STREAMING_LOG_PATH, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")
    
    logger.info(f"Streaming config logged: {dataset_name} -> {strategy} (samples: {sample_count})")

def load_dataset_streaming(
    dataset_name: str, 
    split: str = "train", 
    streaming: bool = True,
    dataset_config: Optional[Dict[str, Any]] = None
) -> Iterator[Dict[str, Any]]:
    """
    Load a dataset with streaming support.
    
    This function strictly enforces real data sourcing. If the dataset 
    cannot be fetched from the Hugging Face Hub or the specified source,
    it raises a RuntimeError. NO synthetic or mock data is generated.
    
    For large datasets (e.g., CommonCrawl), streaming=True ensures that
    data is processed in chunks to fit within memory constraints (~7GB RAM).
    
    Args:
        dataset_name: The name of the dataset on Hugging Face Hub.
        split: The split to load (e.g., 'train', 'test').
        streaming: If True, returns an iterator.
        dataset_config: Optional config dict for specific dataset handling.
        
    Returns:
        An iterator yielding dataset samples.
        
    Raises:
        RuntimeError: If the dataset fetch fails (network error, missing dataset, etc.).
    """
    strategy = "streaming" if streaming else "full_load"
    
    # Estimate size logic for specific datasets
    estimated_size = None 
    if "common_crawl" in dataset_name.lower():
        estimated_size = 50000.0 # Large dataset indicator
        strategy = "streaming_large_chunked"
    elif "dolly" in dataset_name.lower():
        estimated_size = 500.0
        strategy = "streaming_standard"
    elif "gsm8k" in dataset_name.lower():
        estimated_size = 50.0
        strategy = "streaming_standard"
    elif "humaneval" in dataset_name.lower():
        estimated_size = 10.0
        strategy = "streaming_standard"

    try:
        logger.info(f"Attempting to stream dataset: {dataset_name} (split={split}, streaming={streaming})")
        
        # Load with streaming enabled
        ds = load_dataset(
            dataset_name, 
            split=split, 
            streaming=streaming,
            **(dataset_config or {})
        )
        
        # Log the streaming configuration immediately upon successful load
        _log_streaming_config(dataset_name, split, strategy, estimated_size, sample_count=0)
        
        return iter(ds)
    except Exception as e:
        # Fail loudly: Do not catch and return synthetic data.
        # Propagate the error so the pipeline stops and the user knows
        # the real source is unavailable.
        logger.error(f"CRITICAL: Failed to load real dataset '{dataset_name}'. "
                     "No fallback to synthetic data allowed. Error: {e}")
        raise RuntimeError(f"Failed to load real dataset '{dataset_name}': {e}") from e

def load_gsm8k_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load GSM8K dataset in streaming mode.
    
    Enforces strict real data loading. Raises if GSM8K is unavailable.
    """
    return load_dataset_streaming("gsm8k", split="train", streaming=True)

def load_humaneval_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load HumanEval dataset in streaming mode.
    
    Enforces strict real data loading. Raises if HumanEval is unavailable.
    """
    return load_dataset_streaming("openai_humaneval", split="test", streaming=True)

def load_common_crawl_streaming(subset: str = "cc-en", split: str = "train") -> Iterator[Dict[str, Any]]:
    """
    Load CommonCrawl subset in streaming mode for large-scale natural language tasks.
    
    This function is specifically designed to handle large datasets by streaming
    chunks of data to avoid memory overflow.
    
    Args:
        subset: The specific subset of CommonCrawl (e.g., 'cc-en').
        split: The split to load.
        
    Returns:
        An iterator yielding dataset samples.
    """
    return load_dataset_streaming(f"common_crawl/{subset}", split=split, streaming=True)

def load_dolly_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load Dolly dataset in streaming mode.
    
    Args:
        subset: The specific subset of Dolly.
        split: The split to load.
        
    Returns:
        An iterator yielding dataset samples.
    """
    return load_dataset_streaming("databricks/dolly-15k", split="train", streaming=True)

def process_streamed_dataset_with_logging(
    dataset_name: str, 
    split: str, 
    process_fn: callable,
    max_samples: Optional[int] = None
) -> int:
    """
    Utility to process a streamed dataset, counting samples and logging the final count.
    This ensures the logging requirement for sample size is met for any processing task.
    
    Args:
        dataset_name: Name of the dataset.
        split: Split name.
        process_fn: Function to apply to each sample.
        max_samples: Optional limit on number of samples to process.
        
    Returns:
        Total number of samples processed.
    """
    iterator = load_dataset_streaming(dataset_name, split=split, streaming=True)
    count = 0
    
    logger.info(f"Starting stream processing for {dataset_name}...")
    start_time = time.time()
    
    for sample in iterator:
        if max_samples and count >= max_samples:
            break
        
        process_fn(sample)
        count += 1
        
        # Log progress every 1000 samples for large streams
        if count % 1000 == 0:
            logger.info(f"Processed {count} samples...")
    
    elapsed = time.time() - start_time
    _log_streaming_config(dataset_name, split, "streaming_processed", sample_count=count)
    logger.info(f"Completed processing {count} samples in {elapsed:.2f}s")
    
    return count