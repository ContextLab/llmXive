"""
Embedding extraction with resource logging.

This module extends the embedding extraction process to include detailed
resource usage logging (time per batch, peak RAM) as required by T016.
It wraps the existing embedding extraction logic to add profiling capabilities.

Output:
    - data/embeddings.parquet: The extracted embeddings
    - data/resource_log.json: Resource usage statistics
"""
import os
import sys
import json
import logging
import time
import traceback
import tracemalloc
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# Import from existing API surface
from src.data.embed import (
    load_model_and_processor,
    extract_embeddings_batch,
    load_audio_file,
    process_dataset,
    main as embed_main
)
from src.utils.config import get_path, ensure_dir, get_artifact_hash
from src.utils.logging_config import get_module_logger

# Configure logger for this module
logger = get_module_logger(__name__)


def get_peak_memory_mb() -> float:
    """
    Get the peak memory usage in MB using tracemalloc.
    
    Returns:
        float: Peak memory usage in MB
    """
    if not tracemalloc.is_tracing():
        return 0.0
    
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)  # Convert bytes to MB


def start_profiling() -> None:
    """Start memory profiling."""
    tracemalloc.start()
    logger.info("Memory profiling started")


def stop_profiling() -> float:
    """
    Stop memory profiling and return peak memory usage.
    
    Returns:
        float: Peak memory usage in MB
    """
    if not tracemalloc.is_tracing():
        return 0.0
    
    peak_mb = get_peak_memory_mb()
    tracemalloc.stop()
    logger.info(f"Memory profiling stopped. Peak: {peak_mb:.2f} MB")
    return peak_mb


def log_batch_timing(batch_idx: int, batch_size: int, elapsed_time: float) -> Dict[str, Any]:
    """
    Log timing information for a single batch.
    
    Args:
        batch_idx: Index of the batch
        batch_size: Number of items in the batch
        elapsed_time: Time taken to process the batch in seconds
    
    Returns:
        Dict with batch timing information
    """
    timing_info = {
        "batch_idx": batch_idx,
        "batch_size": batch_size,
        "elapsed_time_seconds": elapsed_time,
        "items_per_second": batch_size / elapsed_time if elapsed_time > 0 else 0
    }
    logger.info(
        f"Batch {batch_idx}: {batch_size} items in {elapsed_time:.2f}s "
        f"({timing_info['items_per_second']:.2f} items/sec)"
    )
    return timing_info


def extract_embeddings_with_logging(
    audio_files: List[str],
    labels: List[str],
    model_name: str = "distil-whisper-base",
    batch_size: int = 32,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract embeddings with detailed resource logging.
    
    This function wraps the embedding extraction process to log:
    - Time per batch
    - Peak RAM usage
    - Total processing time
    
    Args:
        audio_files: List of paths to audio files
        labels: List of corresponding labels
        model_name: Name of the model to use for embedding extraction
        batch_size: Number of samples to process in each batch
        output_path: Path to save the output embeddings (if None, uses default)
    
    Returns:
        Dict containing:
            - output_path: Path to the saved embeddings
            - resource_log: Dict with timing and memory statistics
            - total_samples: Number of samples processed
            - success: Boolean indicating if extraction succeeded
    """
    if output_path is None:
        output_path = get_path("data", "embeddings.parquet")
    
    ensure_dir(output_path)
    
    # Initialize resource log
    resource_log = {
        "model_name": model_name,
        "batch_size": batch_size,
        "total_samples": len(audio_files),
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "batches": [],
        "peak_memory_mb": 0.0,
        "total_time_seconds": 0.0
    }
    
    try:
        logger.info(f"Starting embedding extraction for {len(audio_files)} samples")
        logger.info(f"Output path: {output_path}")
        
        # Start memory profiling
        start_profiling()
        
        # Load model and processor
        logger.info(f"Loading model: {model_name}")
        model, processor = load_model_and_processor(model_name)
        
        # Process in batches
        total_start_time = time.time()
        num_batches = (len(audio_files) + batch_size - 1) // batch_size
        
        all_embeddings = []
        all_labels = []
        all_file_paths = []
        
        for batch_idx in range(num_batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, len(audio_files))
            
            batch_files = audio_files[batch_start:batch_end]
            batch_labels = labels[batch_start:batch_end]
            batch_paths = batch_files  # Using file paths as identifiers
            
            batch_start_time = time.time()
            
            # Extract embeddings for this batch
            batch_embeddings, processed_labels = extract_embeddings_batch(
                model, processor, batch_files
            )
            
            batch_elapsed = time.time() - batch_start_time
            
            # Log batch timing
            batch_timing = log_batch_timing(batch_idx, len(batch_files), batch_elapsed)
            resource_log["batches"].append(batch_timing)
            
            # Accumulate results
            all_embeddings.extend(batch_embeddings)
            all_labels.extend(processed_labels)
            all_file_paths.extend(batch_paths)
        
        total_time = time.time() - total_start_time
        
        # Stop profiling and get peak memory
        peak_memory = stop_profiling()
        
        # Create DataFrame
        df_data = {
            "file_path": all_file_paths,
            "label": all_labels,
            "embedding": all_embeddings
        }
        
        # Convert embeddings to numpy arrays for Parquet storage
        df = pd.DataFrame(df_data)
        df["embedding"] = df["embedding"].apply(lambda x: x.tolist() if isinstance(x, np.ndarray) else x)
        
        # Save to Parquet
        df.to_parquet(output_path, index=False)
        
        # Update resource log
        resource_log["peak_memory_mb"] = peak_memory
        resource_log["total_time_seconds"] = total_time
        resource_log["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        resource_log["success"] = True
        
        logger.info(f"Embedding extraction completed successfully")
        logger.info(f"Total time: {total_time:.2f} seconds")
        logger.info(f"Peak memory: {peak_memory:.2f} MB")
        logger.info(f"Output saved to: {output_path}")
        
        # Save resource log
        resource_log_path = get_path("data", "resource_log.json")
        ensure_dir(resource_log_path)
        with open(resource_log_path, "w") as f:
            json.dump(resource_log, f, indent=2)
        
        logger.info(f"Resource log saved to: {resource_log_path}")
        
        return {
            "output_path": output_path,
            "resource_log": resource_log,
            "total_samples": len(audio_files),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error during embedding extraction: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Stop profiling even on error
        try:
            if tracemalloc.is_tracing():
                stop_profiling()
        except:
            pass
        
        resource_log["success"] = False
        resource_log["error"] = str(e)
        
        # Save error resource log
        resource_log_path = get_path("data", "resource_log.json")
        ensure_dir(resource_log_path)
        with open(resource_log_path, "w") as f:
            json.dump(resource_log, f, indent=2)
        
        return {
            "output_path": output_path,
            "resource_log": resource_log,
            "total_samples": len(audio_files),
            "success": False
        }


def main():
    """
    Main entry point for embedding extraction with logging.
    
    This function demonstrates the resource logging functionality by:
    1. Loading a sample dataset (or generating synthetic data if needed)
    2. Extracting embeddings with detailed logging
    3. Saving the resource log to data/resource_log.json
    """
    logger.info("Starting embedding extraction with resource logging")
    
    # For demonstration, we'll use the existing process_dataset function
    # to load real data, then wrap it with our logging
    
    try:
        # Load dataset using existing function
        audio_files, labels = process_dataset(
            max_samples=100,  # Limit for demonstration
            sample_rate=16000
        )
        
        if not audio_files:
            logger.warning("No audio files found. Generating synthetic benign data...")
            # Import and use the download module to generate synthetic data
            from src.data.download import generate_synthetic_benign_data
            audio_files, labels = generate_synthetic_benign_data(num_samples=100)
        
        logger.info(f"Loaded {len(audio_files)} audio files for processing")
        
        # Extract embeddings with logging
        result = extract_embeddings_with_logging(
            audio_files=audio_files,
            labels=labels,
            model_name="distil-whisper-base",
            batch_size=32,
            output_path=get_path("data", "embeddings.parquet")
        )
        
        if result["success"]:
            logger.info("✅ Embedding extraction completed successfully")
            logger.info(f"   Total samples: {result['total_samples']}")
            logger.info(f"   Total time: {result['resource_log']['total_time_seconds']:.2f}s")
            logger.info(f"   Peak memory: {result['resource_log']['peak_memory_mb']:.2f} MB")
            logger.info(f"   Output: {result['output_path']}")
            logger.info(f"   Resource log: {get_path('data', 'resource_log.json')}")
        else:
            logger.error("❌ Embedding extraction failed")
            logger.error(f"   Error: {result['resource_log'].get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()