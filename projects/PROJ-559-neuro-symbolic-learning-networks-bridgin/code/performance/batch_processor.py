import os
import sys
import json
import logging
import argparse
import pandas as pd
from typing import List, Dict, Any, Optional

from performance.memory_monitor import stream_csv_batch, optimize_dataframe_dtypes, MEMORY_LIMIT_MB, MemoryMonitor, get_current_memory_mb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_simulation_logs_batch(
    input_path: str,
    output_path: str,
    batch_size: int = 5000,
    memory_limit_mb: float = MEMORY_LIMIT_MB
) -> Dict[str, Any]:
    """
    Process simulation logs in batches to ensure memory efficiency.
    
    Args:
        input_path: Path to input simulation logs CSV
        output_path: Path to output processed CSV
        batch_size: Number of rows per batch
        memory_limit_mb: Maximum memory allowed in MB
    
    Returns:
        Dictionary with processing statistics
    """
    logger.info(f"Processing simulation logs: {input_path}")
    
    stats = {
        "input_path": input_path,
        "output_path": output_path,
        "status": "OK",
        "max_memory_mb": 0
    }
    
    monitor = MemoryMonitor(limit_mb=memory_limit_mb)
    
    try:
        with monitor:
            stream_csv_batch(input_path, output_path, batch_size=batch_size, memory_limit_mb=memory_limit_mb)
            stats["max_memory_mb"] = monitor.max_memory_mb
            logger.info(f"Batch processing completed. Max memory: {stats['max_memory_mb']:.2f} MB")
            
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        stats["status"] = "FAILED"
        stats["error"] = str(e)
    
    return stats

def merge_datasets_streaming(
    paths: List[str],
    output_path: str,
    batch_size: int = 5000,
    memory_limit_mb: float = MEMORY_LIMIT_MB
) -> Dict[str, Any]:
    """
    Merge multiple large CSV datasets in a streaming fashion to avoid memory overflow.
    
    Args:
        paths: List of input CSV paths
        output_path: Path to output merged CSV
        batch_size: Number of rows per batch
        memory_limit_mb: Maximum memory allowed in MB
    
    Returns:
        Dictionary with merge statistics
    """
    logger.info(f"Merging {len(paths)} datasets into {output_path}")
    
    stats = {
        "input_paths": paths,
        "output_path": output_path,
        "total_rows": 0,
        "status": "OK",
        "max_memory_mb": 0
    }
    
    monitor = MemoryMonitor(limit_mb=memory_limit_mb)
    
    try:
        with monitor:
            # Process first file to get headers
            if not paths:
                logger.error("No input paths provided")
                return stats
            
            # Use the streaming function which handles headers correctly
            # We just need to call it sequentially or use pandas concat in chunks if needed
            # For simplicity in this streaming merge, we assume the structure is identical
            # and we append.
            
            first = True
            for path in paths:
                logger.info(f"Processing {path}")
                # Read in chunks and append
                for chunk in pd.read_csv(path, chunksize=batch_size):
                    if not monitor.check(force_gc_if_high=True):
                        raise MemoryError(f"Memory limit exceeded during merge")
                    
                    mode = 'w' if first else 'a'
                    header = first
                    chunk.to_csv(output_path, mode=mode, index=False, header=header)
                    first = False
                    stats["total_rows"] += len(chunk)
                
                gc.collect() # Force GC between files
            
            stats["max_memory_mb"] = monitor.max_memory_mb
            logger.info(f"Merge completed. Total rows: {stats['total_rows']}, Max memory: {stats['max_memory_mb']:.2f} MB")
            
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        stats["status"] = "FAILED"
        stats["error"] = str(e)
    
    return stats

def main():
    """Main entry point for batch processor."""
    parser = argparse.ArgumentParser(description="Batch Processor for Large Datasets")
    parser.add_argument("--mode", choices=["process", "merge"], required=True, help="Operation mode")
    parser.add_argument("--input", nargs="+", help="Input file(s)")
    parser.add_argument("--output", required=True, help="Output file")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size")
    parser.add_argument("--limit", type=float, default=MEMORY_LIMIT_MB, help="Memory limit in MB")
    args = parser.parse_args()
    
    if args.mode == "process":
        if not args.input or len(args.input) != 1:
            print("Error: --input must be a single file for process mode")
            sys.exit(1)
        stats = process_simulation_logs_batch(args.input[0], args.output, args.batch_size, args.limit)
    elif args.mode == "merge":
        if not args.input:
            print("Error: --input must contain at least one file for merge mode")
            sys.exit(1)
        stats = merge_datasets_streaming(args.input, args.output, args.batch_size, args.limit)
    
    print(json.dumps(stats, indent=2))
    sys.exit(0 if stats.get("status") == "OK" else 1)

if __name__ == "__main__":
    main()
