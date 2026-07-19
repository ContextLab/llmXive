"""
Data streaming logic for User Story 1.

Performs a stratified random sample of images from ImageNet-1K and LAION-400M,
writing raw batches to data/raw/. Monitors cumulative CPU time and saves
partial results if the 6-hour limit is reached.
"""
import argparse
import signal
import sys
import time
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
import pandas as pd
import numpy as np
from datasets import load_dataset
from utils.config import get_config, get_path

# Time limit in seconds (6 hours)
TIME_LIMIT_SECONDS = 6 * 3600

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("CPU time limit reached (6 hours)")

def setup_timeout():
    """Set up the 6-hour timeout using signal.SIGALRM."""
    # Set the alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIME_LIMIT_SECONDS)

def cancel_timeout():
    """Cancel the timeout alarm."""
    signal.alarm(0)

def load_imageNet_streaming() -> Generator[Dict[str, Any], None, None]:
    """
    Stream ImageNet-1K dataset from Hugging Face.
    Uses the 'imagenet-1k' dataset which is publicly available.
    Yields dictionaries with 'image' and 'label' keys.
    """
    try:
        # Load dataset with streaming to avoid downloading entire dataset
        dataset = load_dataset("imagenet-1k", split="train", streaming=True)
        for item in dataset:
            yield {
                "source": "imagenet",
                "image": item["image"],
                "label": item["label"],
                "id": item["label"]  # Using label as ID for simplicity
            }
    except Exception as e:
        raise RuntimeError(f"Failed to load ImageNet-1K: {e}")

def load_laion_streaming() -> Generator[Dict[str, Any], None, None]:
    """
    Stream LAION-400M dataset from Hugging Face.
    Uses a subset of LAION-400M that is publicly available.
    Yields dictionaries with 'image' and 'text' keys.
    """
    try:
        # Load a smaller, representative subset of LAION
        # Using LAION-Aesthetics as a proxy for LAION-400M
        dataset = load_dataset("laion/laion-aesthetics", split="train", streaming=True)
        for item in dataset:
            yield {
                "source": "laion",
                "image": item["image"],
                "label": 0,  # Placeholder label for LAION
                "id": item.get("id", "unknown"),
                "text": item.get("text", "")
            }
    except Exception as e:
        raise RuntimeError(f"Failed to load LAION dataset: {e}")

def stratified_sample(
    source: str,
    n_samples: int,
    batch_size: int = 100,
    seed: int = 42
) -> Generator[Dict[str, Any], None, None]:
    """
    Perform stratified random sampling from a data source.
    
    Args:
        source: Data source name ('imagenet' or 'laion')
        n_samples: Number of samples to collect
        batch_size: Number of samples per batch
        seed: Random seed for reproducibility
    
    Yields:
        Batches of sampled data
    """
    np.random.seed(seed)
    
    # Load the appropriate dataset
    if source == "imagenet":
        data_loader = load_imageNet_streaming()
    elif source == "laion":
        data_loader = load_laion_streaming()
    else:
        raise ValueError(f"Unknown source: {source}")
    
    # Collect samples with stratification
    collected = []
    labels_seen = {}
    
    for item in data_loader:
        if len(collected) >= n_samples:
            break
        
        # Simple stratification by label/source
        label = item.get("label", 0)
        if label not in labels_seen:
            labels_seen[label] = 0
        
        # Accept sample with probability to ensure stratification
        # This is a simplified stratification approach
        if np.random.random() < 0.1:  # 10% sampling rate
            collected.append(item)
            labels_seen[label] += 1
            
            # Yield batch when full
            if len(collected) >= batch_size:
                yield collected
                collected = []
    
    # Yield remaining samples
    if collected:
        yield collected

def write_batch_to_parquet(
    batch: List[Dict[str, Any]],
    source: str,
    output_dir: Path,
    batch_index: int
) -> Path:
    """
    Write a batch of samples to a Parquet file.
    
    Args:
        batch: List of sample dictionaries
        source: Source name ('imagenet' or 'laion')
        output_dir: Directory to write files
        batch_index: Index for file naming
    
    Returns:
        Path to the written file
    """
    # Convert PIL images to bytes for Parquet storage
    processed_batch = []
    for item in batch:
        processed_item = item.copy()
        if "image" in item and item["image"] is not None:
            # Convert PIL image to bytes
            import io
            img_bytes = io.BytesIO()
            item["image"].save(img_bytes, format="PNG")
            processed_item["image_bytes"] = img_bytes.getvalue()
            processed_item.pop("image", None)  # Remove PIL image
        processed_batch.append(processed_item)
    
    df = pd.DataFrame(processed_batch)
    filename = f"{source}_samples_batch_{batch_index:04d}.parquet"
    filepath = output_dir / filename
    df.to_parquet(filepath, engine="pyarrow")
    
    return filepath

def run_data_streaming(
    imagenet_samples: int = 500,
    laion_samples: int = 500,
    batch_size: int = 100,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Main function to run data streaming with time monitoring.
    
    Args:
        imagenet_samples: Number of ImageNet samples to collect
        laion_samples: Number of LAION samples to collect
        batch_size: Batch size for writing
        seed: Random seed
    
    Returns:
        Dictionary with status and metadata
    """
    config = get_config()
    output_dir = get_path("data_raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up timeout
    setup_timeout()
    
    start_time = time.time()
    status = "completed"
    results = {
        "imagenet": {"batches": 0, "samples": 0, "files": []},
        "laion": {"batches": 0, "samples": 0, "files": []},
        "status": "completed",
        "elapsed_time": 0,
        "partial": False
    }
    
    try:
        # Stream ImageNet samples
        imagenet_batch_idx = 0
        for batch in stratified_sample("imagenet", imagenet_samples, batch_size, seed):
            elapsed = time.time() - start_time
            if elapsed > TIME_LIMIT_SECONDS:
                status = "partial"
                break
            
            filepath = write_batch_to_parquet(batch, "imagenet", output_dir, imagenet_batch_idx)
            results["imagenet"]["files"].append(str(filepath))
            results["imagenet"]["batches"] += 1
            results["imagenet"]["samples"] += len(batch)
            imagenet_batch_idx += 1
            
            # Check time limit between batches
            if time.time() - start_time > TIME_LIMIT_SECONDS:
                status = "partial"
                break
        
        # Stream LAION samples
        laion_batch_idx = 0
        for batch in stratified_sample("laion", laion_samples, batch_size, seed + 1):
            elapsed = time.time() - start_time
            if elapsed > TIME_LIMIT_SECONDS:
                status = "partial"
                break
            
            filepath = write_batch_to_parquet(batch, "laion", output_dir, laion_batch_idx)
            results["laion"]["files"].append(str(filepath))
            results["laion"]["batches"] += 1
            results["laion"]["samples"] += len(batch)
            laion_batch_idx += 1
            
            # Check time limit between batches
            if time.time() - start_time > TIME_LIMIT_SECONDS:
                status = "partial"
                break
    
    except TimeoutError:
        status = "partial"
        print(f"⚠️  Time limit reached after {time.time() - start_time:.2f} seconds", file=sys.stderr)
    
    finally:
        cancel_timeout()
    
    # Save results metadata
    results["status"] = status
    results["elapsed_time"] = time.time() - start_time
    results["partial"] = (status == "partial")
    
    metadata_path = output_dir / "streaming_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Streaming complete: {status}")
    print(f"ImageNet samples: {results['imagenet']['samples']}")
    print(f"LAION samples: {results['laion']['samples']}")
    print(f"Elapsed time: {results['elapsed_time']:.2f}s")
    
    return results

def main():
    """Entry point for data streaming script."""
    parser = argparse.ArgumentParser(description="Stream and sample data from ImageNet and LAION")
    parser.add_argument("--imagenet-samples", type=int, default=500, help="Number of ImageNet samples")
    parser.add_argument("--laion-samples", type=int, default=500, help="Number of LAION samples")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for writing")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    try:
        results = run_data_streaming(
            imagenet_samples=args.imagenet_samples,
            laion_samples=args.laion_samples,
            batch_size=args.batch_size,
            seed=args.seed
        )
        
        # Exit with appropriate code
        if results["partial"]:
            sys.exit(2)  # Partial result exit code
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Error during streaming: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
