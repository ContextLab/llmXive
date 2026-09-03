"""
Download script for llmXive follow-up: extending Cosmos 3.
Fetches bridge-to-worlds/bridge-data dataset using streaming mode,
filters for instances with 'actions' field, and saves to JSONL.
Optimized for low memory footprint (< 7GB) and high throughput via batching.
"""
import json
import os
import sys
import time
from pathlib import Path

# Add parent directory to path to allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from utils.logger import get_logger, log_script_start, log_script_end, get_memory_usage_mb

# Constants
DATASET_NAME = "bridge-to-worlds/bridge-data"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "bridge_samples.jsonl"
BUFFER_SIZE = 5000  # Increased batch size for throughput optimization
MEMORY_THRESHOLD_MB = 7000  # 7GB limit

logger = get_logger(__name__)


def fetch_and_filter_dataset():
    """
    Fetch the dataset in streaming mode, filter for 'actions' field,
    and yield valid samples.
    Implements memory monitoring to ensure we stay under threshold.
    """
    logger.info(f"Starting fetch of dataset: {DATASET_NAME}")
    
    try:
        # Load dataset in streaming mode to avoid memory issues
        # Use streaming=True to process iteratively without loading full dataset
        dataset = load_dataset(DATASET_NAME, split="train", streaming=True)
    except Exception as e:
        logger.error(f"Failed to load dataset '{DATASET_NAME}': {e}")
        raise RuntimeError(f"Real data fetch failed: {e}")

    count = 0
    start_time = time.time()
    
    for batch_idx, sample in enumerate(dataset):
        # Memory check every 1000 samples
        if batch_idx % 1000 == 0 and batch_idx > 0:
            current_mem = get_memory_usage_mb()
            logger.debug(f"Sample {batch_idx}: Memory usage {current_mem:.2f} MB")
            if current_mem > MEMORY_THRESHOLD_MB:
                raise MemoryError(f"Memory usage {current_mem:.2f} MB exceeded threshold {MEMORY_THRESHOLD_MB} MB")

        # Filter: ensure 'actions' field exists and is not empty
        if "actions" in sample and sample["actions"] is not None:
            yield sample
            count += 1
            
            # Log progress every 1000 samples
            if count % 1000 == 0:
                elapsed = time.time() - start_time
                rate = count / elapsed if elapsed > 0 else 0
                logger.info(f"Processed {count} valid samples ({rate:.1f} samples/sec)...")

    if count == 0:
        logger.warning("No samples with 'actions' field found in the dataset.")
    else:
        elapsed = time.time() - start_time
        rate = count / elapsed if elapsed > 0 else 0
        logger.info(f"Successfully filtered {count} samples containing 'actions' at {rate:.1f} samples/sec.")


def save_to_jsonl(samples_generator, output_path: Path, buffer_size: int = BUFFER_SIZE):
    """
    Consume the generator and write samples to a JSONL file.
    Uses a larger buffer to reduce I/O overhead and improve throughput.
    """
    logger.info(f"Writing filtered data to: {output_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    buffer = []
    written_count = 0
    start_time = time.time()

    with open(output_path, "w", encoding="utf-8") as f:
        for sample in samples_generator:
            buffer.append(sample)
            
            if len(buffer) >= buffer_size:
                # Write batch efficiently
                for item in buffer:
                    f.write(json.dumps(item) + "\n")
                written_count += len(buffer)
                buffer = []
                
                # Log throughput every buffer write
                if written_count % (buffer_size * 10) == 0:
                    elapsed = time.time() - start_time
                    rate = written_count / elapsed if elapsed > 0 else 0
                    logger.debug(f"Wrote {written_count} samples ({rate:.1f} samples/sec)...")

        # Write remaining items
        if buffer:
            for item in buffer:
                f.write(json.dumps(item) + "\n")
            written_count += len(buffer)

    elapsed = time.time() - start_time
    final_rate = written_count / elapsed if elapsed > 0 else 0
    logger.info(f"Download complete. Saved {written_count} samples to {output_path} at {final_rate:.1f} samples/sec.")


def main():
    log_script_start(__file__)
    
    try:
        logger.info("Initializing optimized streaming pipeline...")
        samples = fetch_and_filter_dataset()
        save_to_jsonl(samples, OUTPUT_FILE)
        logger.info("Task T010 completed successfully: data saved to bridge_samples.jsonl")
    except Exception as e:
        logger.error(f"Task T010 failed: {e}")
        # Re-raise to ensure the execution stage sees the failure
        raise
    finally:
        log_script_end(__file__)


if __name__ == "__main__":
    main()
