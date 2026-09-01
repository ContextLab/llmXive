import os
import sys
import json
import time
import tracemalloc
import argparse
from typing import Dict, Any, Optional

# Import from existing API surface
from data.loader import load_epochs_chunked, estimate_memory_usage
from config import load_config, get_config_value


def get_peak_memory_mb() -> float:
    """
    Get the current peak memory usage of the process in Megabytes.
    """
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)


def run_memory_check(
    data_dir: str,
    output_path: str,
    chunk_size: int = 10,
    max_memory_gb: float = 6.5
) -> Dict[str, Any]:
    """
    Verify chunked loading logic by processing a subset of the dataset
    and measuring peak memory usage to ensure it stays within limits.

    Args:
        data_dir: Path to the directory containing the processed data.
        output_path: Path where the JSON report will be written.
        chunk_size: Number of epochs to load per chunk.
        max_memory_gb: Maximum allowed memory usage in GB.

    Returns:
        A dictionary containing the memory check results.
    """
    config = load_config()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Starting memory check on data in: {data_dir}")
    print(f"Chunk size: {chunk_size}, Max allowed memory: {max_memory_gb} GB")

    tracemalloc.start()
    start_time = time.time()

    try:
        # Estimate expected memory usage based on config or default
        estimated_peak = estimate_memory_usage(
            data_dir=data_dir,
            chunk_size=chunk_size,
            config=config
        )
        
        print(f"Estimated peak memory usage: {estimated_peak:.2f} MB")

        # Run the chunked loader to get actual measurements
        # We iterate through chunks to simulate the full pipeline load
        total_epochs_loaded = 0
        chunk_count = 0
        
        # Use a generator to load chunks without holding all in memory
        # We pass a subset limit to ensure we don't run on the full dataset
        # if the dataset is huge, but enough to test the logic
        for chunk in load_epochs_chunked(
            data_dir=data_dir,
            chunk_size=chunk_size,
            max_chunks=5  # Limit to 5 chunks for the check to keep it fast but representative
        ):
            chunk_count += 1
            total_epochs_loaded += len(chunk)
            
            # Explicitly delete chunk to force garbage collection if needed
            del chunk
            time.sleep(0.1)  # Small delay to allow GC

        elapsed_time = time.time() - start_time
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_memory_mb = peak_mem / (1024 * 1024)
        peak_memory_gb = peak_memory_mb / 1024.0

        status = "passed" if peak_memory_gb <= max_memory_gb else "failed"

        report = {
            "status": status,
            "message": f"Memory check {'passed' if status == 'passed' else 'failed'}. Peak: {peak_memory_gb:.2f} GB.",
            "peak_memory_mb": round(peak_memory_mb, 2),
            "peak_memory_gb": round(peak_memory_gb, 4),
            "max_allowed_gb": max_memory_gb,
            "estimated_peak_mb": round(estimated_peak, 2),
            "chunks_processed": chunk_count,
            "total_epochs_loaded": total_epochs_loaded,
            "elapsed_seconds": round(elapsed_time, 2),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        print(f"Memory Check Result: {status}")
        print(f"Peak Memory: {peak_memory_gb:.2f} GB (Limit: {max_memory_gb} GB)")
        print(f"Processed {chunk_count} chunks ({total_epochs_loaded} epochs)")

    except Exception as e:
        tracemalloc.stop()
        report = {
            "status": "error",
            "message": str(e),
            "peak_memory_mb": 0.0,
            "peak_memory_gb": 0.0,
            "max_allowed_gb": max_memory_gb,
            "chunks_processed": 0,
            "total_epochs_loaded": 0,
            "elapsed_seconds": 0.0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        print(f"Memory check failed with error: {e}")

    # Write the report to disk
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Report written to: {output_path}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Verify chunked loading logic and memory usage."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Path to the processed data directory."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/memory_check_report.json",
        help="Path to the output JSON report."
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10,
        help="Number of epochs to load per chunk."
    )
    parser.add_argument(
        "--max-memory-gb",
        type=float,
        default=6.5,
        help="Maximum allowed memory usage in GB."
    )

    args = parser.parse_args()

    run_memory_check(
        data_dir=args.data_dir,
        output_path=args.output,
        chunk_size=args.chunk_size,
        max_memory_gb=args.max_memory_gb
    )


if __name__ == "__main__":
    main()