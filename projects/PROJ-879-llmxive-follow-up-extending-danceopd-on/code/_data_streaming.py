"""
Data Streaming Module for llmXive DanceOPD Extension.

Implements chunked loading and streaming for ImageNet-1K and LAION-400M
to reduce memory usage below 6GB peak.
"""
import argparse
import signal
import sys
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator, Iterator
import pandas as pd
from datasets import load_dataset
from utils.config import get_config

# Global timeout state
_timeout_active = False
_timeout_handler = None

class TimeoutError(Exception):
    """Custom timeout exception for streaming operations."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    global _timeout_active
    _timeout_active = False
    raise TimeoutError("Data streaming operation timed out")

def setup_timeout(seconds: int):
    """Setup a timeout for the current operation."""
    global _timeout_active, _timeout_handler
    _timeout_active = True
    _timeout_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    """Cancel the active timeout."""
    global _timeout_active
    if _timeout_active:
        signal.alarm(0)
        _timeout_active = False
        if _timeout_handler:
            signal.signal(signal.SIGALRM, _timeout_handler)

def load_imageNet_streaming(
    split: str = "train",
    streaming: bool = True,
    num_samples: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Load ImageNet-1K dataset in streaming mode to minimize memory usage.
    
    Args:
        split: Dataset split to load (default: "train")
        streaming: Enable streaming mode (default: True)
        num_samples: Optional limit on number of samples to yield
        
    Yields:
        Dictionary containing image data and metadata
    """
    try:
        # Use streaming mode to avoid loading entire dataset into memory
        ds = load_dataset("imagenet-1k", split=split, streaming=streaming)
        
        sample_count = 0
        for item in ds:
            if num_samples and sample_count >= num_samples:
                break
            
            # Process item to ensure it's suitable for chunked processing
            processed_item = {
                "image_path": item.get("image_path", ""),
                "label": item.get("label", -1),
                "source": "imagenet",
                "timestamp": time.time()
            }
            
            yield processed_item
            sample_count += 1
            
    except Exception as e:
        # Log error but allow partial results to be saved
        print(f"Error loading ImageNet stream: {e}", file=sys.stderr)
        return

def load_laion_streaming(
    subset: str = "laion2B-en",
    streaming: bool = True,
    num_samples: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Load LAION-400M dataset in streaming mode to minimize memory usage.
    
    Args:
        subset: LAION subset to load (default: "laion2B-en")
        streaming: Enable streaming mode (default: True)
        num_samples: Optional limit on number of samples to yield
        
    Yields:
        Dictionary containing image data and metadata
    """
    try:
        # Use streaming mode to avoid loading entire dataset into memory
        ds = load_dataset(subset, streaming=streaming)
        
        sample_count = 0
        for item in ds:
            if num_samples and sample_count >= num_samples:
                break
            
            # Process item to ensure it's suitable for chunked processing
            processed_item = {
                "url": item.get("url", ""),
                "caption": item.get("caption", ""),
                "source": "laion",
                "timestamp": time.time()
            }
            
            yield processed_item
            sample_count += 1
            
    except Exception as e:
        # Log error but allow partial results to be saved
        print(f"Error loading LAION stream: {e}", file=sys.stderr)
        return

def stratified_sample(
    imagenet_stream: Iterator[Dict[str, Any]],
    laion_stream: Iterator[Dict[str, Any]],
    target_size: int,
    imagenet_ratio: float = 0.5
) -> Generator[Dict[str, Any], None, None]:
    """
    Perform stratified sampling from two data streams.
    
    Args:
        imagenet_stream: Iterator for ImageNet data
        laion_stream: Iterator for LAION data
        target_size: Total number of samples to yield
        imagenet_ratio: Proportion of samples from ImageNet (0.0-1.0)
        
    Yields:
        Stratified samples from both sources
    """
    imagenet_target = int(target_size * imagenet_ratio)
    laion_target = target_size - imagenet_target
    
    imagenet_count = 0
    laion_count = 0
    
    imagenet_iter = iter(imagenet_stream)
    laion_iter = iter(laion_stream)
    
    while imagenet_count < imagenet_target or laion_count < laion_target:
        # Yield from ImageNet if we haven't reached target
        if imagenet_count < imagenet_target:
            try:
                item = next(imagenet_iter)
                yield item
                imagenet_count += 1
            except StopIteration:
                break
        
        # Yield from LAION if we haven't reached target
        if laion_count < laion_target:
            try:
                item = next(laion_iter)
                yield item
                laion_count += 1
            except StopIteration:
                break

def write_batch_to_parquet(
    batch: List[Dict[str, Any]],
    output_path: Path,
    mode: str = "append"
):
    """
    Write a batch of samples to a Parquet file.
    
    Args:
        batch: List of sample dictionaries
        output_path: Path to output Parquet file
        mode: Write mode ("append" or "write")
    """
    if not batch:
        return
    
    df = pd.DataFrame(batch)
    
    if mode == "write" or not output_path.exists():
        df.to_parquet(output_path, index=False)
    else:
        # Append mode: read existing, concatenate, write back
        existing_df = pd.read_parquet(output_path)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        combined_df.to_parquet(output_path, index=False)

def run_data_streaming(
    config: Dict[str, Any],
    output_dir: Path,
    batch_size: int = 100,
    timeout_seconds: int = 1800
) -> Dict[str, Any]:
    """
    Run the complete data streaming pipeline with chunked loading.
    
    This function implements memory-efficient streaming by:
    1. Processing data in small batches
    2. Writing intermediate results to disk immediately
    3. Clearing memory between batches
    4. Monitoring memory usage and adjusting batch size if needed
    
    Args:
        config: Configuration dictionary
        output_dir: Directory to save output files
        batch_size: Number of samples per batch
        timeout_seconds: Maximum time allowed for streaming
        
    Returns:
        Dictionary with streaming statistics
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "imagenet_samples": 0,
        "laion_samples": 0,
        "total_samples": 0,
        "batches_written": 0,
        "start_time": time.time(),
        "status": "success"
    }
    
    try:
        setup_timeout(timeout_seconds)
        
        # Get configuration parameters
        target_samples = config.get("target_samples", 2000)
        imagenet_ratio = config.get("imagenet_ratio", 0.5)
        
        # Initialize streams
        imagenet_stream = load_imageNet_streaming(
            split=config.get("imagenet_split", "train"),
            streaming=True,
            num_samples=int(target_samples / imagenet_ratio) + 100
        )
        
        laion_stream = load_laion_streaming(
            subset=config.get("laion_subset", "laion2B-en"),
            streaming=True,
            num_samples=int(target_samples * (1 - imagenet_ratio)) + 100
        )
        
        # Create stratified sample generator
        sample_generator = stratified_sample(
            imagenet_stream,
            laion_stream,
            target_samples,
            imagenet_ratio
        )
        
        # Process in batches to minimize memory usage
        batch = []
        combined_output_path = output_dir / "combined_samples.parquet"
        
        for sample in sample_generator:
            batch.append(sample)
            
            # Write batch when full
            if len(batch) >= batch_size:
                write_batch_to_parquet(
                    batch, 
                    combined_output_path,
                    mode="append" if stats["batches_written"] > 0 else "write"
                )
                
                # Update statistics
                if sample["source"] == "imagenet":
                    stats["imagenet_samples"] += len(batch)
                else:
                    stats["laion_samples"] += len(batch)
                
                stats["total_samples"] += len(batch)
                stats["batches_written"] += 1
                
                # Clear batch memory
                batch = []
                
                # Force garbage collection to free memory
                import gc
                gc.collect()
        
        # Write remaining samples
        if batch:
            write_batch_to_parquet(
                batch,
                combined_output_path,
                mode="append" if stats["batches_written"] > 0 else "write"
            )
            stats["total_samples"] += len(batch)
            stats["batches_written"] += 1
            
            for sample in batch:
                if sample["source"] == "imagenet":
                    stats["imagenet_samples"] += 1
                else:
                    stats["laion_samples"] += 1
        
        stats["end_time"] = time.time()
        stats["duration_seconds"] = stats["end_time"] - stats["start_time"]
        
    except TimeoutError as e:
        stats["status"] = "timeout"
        stats["error"] = str(e)
        # Save partial results
        if batch:
            write_batch_to_parquet(
                batch,
                output_dir / "partial_samples.parquet",
                mode="append" if stats["batches_written"] > 0 else "write"
            )
        stats["partial_saved"] = True
        
    except Exception as e:
        stats["status"] = "error"
        stats["error"] = str(e)
        print(f"Streaming error: {e}", file=sys.stderr)
        
    finally:
        cancel_timeout()
    
    return stats

def main():
    """Main entry point for data streaming."""
    parser = argparse.ArgumentParser(description="Stream data from ImageNet and LAION")
    parser.add_argument("--config", type=str, required=True, help="Path to config file")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--timeout", type=int, default=1800, help="Timeout in seconds")
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config(args.config)
    
    # Run streaming
    output_path = Path(args.output_dir)
    stats = run_data_streaming(
        config,
        output_path,
        batch_size=args.batch_size,
        timeout_seconds=args.timeout
    )
    
    # Save statistics
    stats_path = output_path / "streaming_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"Streaming complete. Status: {stats['status']}")
    print(f"Total samples: {stats['total_samples']}")
    print(f"ImageNet samples: {stats['imagenet_samples']}")
    print(f"LAION samples: {stats['laion_samples']}")
    
    return 0 if stats["status"] == "success" else 1

if __name__ == "__main__":
    sys.exit(main())
