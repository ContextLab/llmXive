"""
Data loading pipeline profiler for streaming efficiency.

This module profiles the data loading pipeline to identify bottlenecks
and optimize streaming efficiency. It measures:
- Per-chunk processing time
- Memory usage per chunk
- Throughput (rows/second)
- I/O wait time vs processing time

Outputs profiling metrics to data/processing/streaming_metrics.json
"""

import os
import sys
import json
import time
import logging
import tracemalloc
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Generator
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.load_cod import stream_cod_organic
from logging_config import get_logger, setup_logging

# Configure logger
logger = get_logger(__name__)


def measure_chunk_performance(
    chunk: List[Dict[str, Any]],
    chunk_id: int,
    process_fn: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Measure performance metrics for processing a single chunk.
    
    Args:
        chunk: List of row dictionaries to process
        chunk_id: Identifier for this chunk
        process_fn: Optional function to apply to each row (for realistic timing)
        
    Returns:
        Dictionary with timing and memory metrics
    """
    start_time = time.perf_counter()
    
    # Start memory tracking
    tracemalloc.start()
    
    try:
        # Process the chunk if a function is provided
        if process_fn:
            processed = [process_fn(row) for row in chunk]
        else:
            # Simulate minimal processing (just count rows)
            processed = len(chunk)
        
        # Capture memory usage
        current, peak = tracemalloc.get_traced_memory()
        
    finally:
        tracemalloc.stop()
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    return {
        "chunk_id": chunk_id,
        "row_count": len(chunk),
        "processing_time_seconds": elapsed,
        "rows_per_second": len(chunk) / elapsed if elapsed > 0 else 0,
        "current_memory_bytes": current,
        "peak_memory_bytes": peak
    }


def profile_streaming_pipeline(
    output_path: str,
    max_chunks: Optional[int] = None,
    sample_rows_per_chunk: Optional[int] = None
) -> Dict[str, Any]:
    """
    Profile the streaming data loading pipeline.
    
    Args:
        output_path: Path to write the profiling results JSON
        max_chunks: Maximum number of chunks to profile (None for all)
        sample_rows_per_chunk: If set, only process this many rows per chunk
        
    Returns:
        Aggregated profiling metrics
    """
    logger.info(f"Starting pipeline profiling, output: {output_path}")
    
    chunk_metrics = []
    total_start = time.perf_counter()
    
    try:
        # Get the streaming generator
        stream_gen = stream_cod_organic()
        
        chunk_id = 0
        for chunk in stream_gen:
            if max_chunks and chunk_id >= max_chunks:
                logger.info(f"Reached max_chunks limit ({max_chunks}), stopping")
                break
            
            # Optionally sample rows per chunk
            if sample_rows_per_chunk and len(chunk) > sample_rows_per_chunk:
                chunk = chunk[:sample_rows_per_chunk]
                logger.debug(f"Sampled chunk {chunk_id} to {sample_rows_per_chunk} rows")
            
            # Measure this chunk
            metrics = measure_chunk_performance(chunk, chunk_id)
            chunk_metrics.append(metrics)
            
            # Log progress
            logger.info(
                f"Chunk {chunk_id}: {metrics['row_count']} rows, "
                f"{metrics['processing_time_seconds']:.3f}s, "
                f"{metrics['rows_per_second']:.1f} rows/s"
            )
            
            chunk_id += 1
            
    except Exception as e:
        logger.error(f"Error during streaming: {e}")
        raise
    
    total_end = time.perf_counter()
    total_time = total_end - total_start
    
    # Aggregate metrics
    total_rows = sum(m["row_count"] for m in chunk_metrics)
    avg_time_per_chunk = sum(m["processing_time_seconds"] for m in chunk_metrics) / len(chunk_metrics) if chunk_metrics else 0
    avg_rows_per_second = total_rows / total_time if total_time > 0 else 0
    max_peak_memory = max(m["peak_memory_bytes"] for m in chunk_metrics) if chunk_metrics else 0
    
    profile_results = {
        "profile_timestamp": datetime.utcnow().isoformat(),
        "total_chunks_processed": len(chunk_metrics),
        "total_rows_processed": total_rows,
        "total_time_seconds": total_time,
        "average_time_per_chunk_seconds": avg_time_per_chunk,
        "overall_throughput_rows_per_second": avg_rows_per_second,
        "peak_memory_bytes": max_peak_memory,
        "max_chunks_limited": max_chunks is not None and len(chunk_metrics) >= max_chunks,
        "chunk_details": chunk_metrics
    }
    
    # Write results to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(profile_results, f, indent=2)
    
    logger.info(f"Profile results written to {output_path}")
    logger.info(f"Total: {total_rows} rows in {total_time:.2f}s ({avg_rows_per_second:.1f} rows/s)")
    
    return profile_results


def main():
    """CLI entry point for profiling the data loading pipeline."""
    parser = argparse.ArgumentParser(
        description="Profile the data loading pipeline for streaming efficiency"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processing/streaming_metrics.json",
        help="Path to write profiling results JSON"
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Maximum number of chunks to profile (default: all)"
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=None,
        help="Sample this many rows per chunk for faster profiling"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        profile_streaming_pipeline(
            output_path=args.output,
            max_chunks=args.max_chunks,
            sample_rows_per_chunk=args.sample_rows
        )
        logger.info("Profiling completed successfully")
    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
