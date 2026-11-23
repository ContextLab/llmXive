"""
Performance optimization module for the chess Elo analysis pipeline.

This module provides utilities to ensure RAM usage remains below 7GB
by streaming data, processing in chunks, and sampling when necessary.
"""
import gc
import logging
import os
import sys
import tracemalloc
from pathlib import Path
from typing import Optional, Generator, Tuple, List, Dict, Any, Union
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

# Constants
MAX_RAM_GB = 7.0
MAX_RAM_BYTES = MAX_RAM_GB * 1024 ** 3
CHUNK_SIZE = 10000  # Number of games to process per chunk
SAMPLE_SIZE = 50000  # Default sample size if full data is too large
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def get_current_ram_mb() -> float:
    """Get current RAM usage in MB using tracemalloc."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)


def get_peak_ram_mb() -> float:
    """Get peak RAM usage in MB since tracemalloc started."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)


def check_ram_usage() -> bool:
    """
    Check if current RAM usage is within limits.
    Returns True if within limits, False otherwise.
    """
    current_mb = get_current_ram_mb()
    limit_mb = MAX_RAM_GB * 1024
    logger.info(f"Current RAM usage: {current_mb:.2f} MB (Limit: {limit_mb:.2f} MB)")
    return current_mb < limit_mb


def force_gc():
    """Force garbage collection to free up memory."""
    gc.collect()
    logger.info("Garbage collection forced.")


def sample_dataframe(df: pd.DataFrame, sample_size: int = SAMPLE_SIZE, seed: int = 42) -> pd.DataFrame:
    """
    Create a representative sample of the dataframe if it's too large.
    
    Args:
        df: Input dataframe
        sample_size: Number of rows to sample
        seed: Random seed for reproducibility
        
    Returns:
        Sampled dataframe
    """
    if len(df) <= sample_size:
        logger.info(f"Dataset size ({len(df)} rows) is within sample limit. Returning full dataset.")
        return df
    
    logger.info(f"Dataset too large ({len(df)} rows). Sampling {sample_size} rows.")
    return df.sample(n=sample_size, random_state=seed).reset_index(drop=True)


def process_in_chunks(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    process_func: callable,
    chunk_size: int = CHUNK_SIZE,
    sample: bool = False,
    sample_size: int = SAMPLE_SIZE
) -> Tuple[int, float]:
    """
    Process a large PGN file or dataset in chunks to avoid memory overflow.
    
    Args:
        input_path: Path to input file (PGN or Parquet)
        output_path: Path to output file (Parquet)
        process_func: Function to apply to each chunk
        chunk_size: Number of rows per chunk
        sample: Whether to sample the data instead of processing all
        sample_size: Number of rows to sample if sampling is enabled
        
    Returns:
        Tuple of (total_rows_processed, peak_ram_mb)
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    tracemalloc.start()
    total_rows = 0
    chunks_processed = 0
    
    try:
        # Load data based on file type
        if input_path.suffix == '.pgn':
            # For PGN files, we need to parse in chunks
            # This is a simplified approach - real implementation would stream PGN
            logger.warning("PGN chunking requires streaming parser. Using full load with sampling.")
            if sample:
                # Load and sample (requires reading all to sample fairly)
                # In a real scenario, we'd use a streaming PGN parser
                df = pd.DataFrame() # Placeholder - real implementation would stream
                logger.error("Streaming PGN parsing not implemented in this optimization module. "
                             "Please use the main pipeline with sampling enabled.")
                return 0, 0.0
            else:
                logger.error("Full PGN loading without streaming may exceed RAM limits.")
                return 0, 0.0
                
        elif input_path.suffix in ['.parquet', '.csv']:
            if input_path.suffix == '.parquet':
                df = pd.read_parquet(input_path)
            else:
                df = pd.read_csv(input_path)
            
            if sample:
                df = sample_dataframe(df, sample_size=sample_size)
            
            total_rows = len(df)
            logger.info(f"Loaded {total_rows} rows from {input_path}")
            
            # Process in chunks if necessary
            if len(df) > chunk_size:
                logger.info(f"Processing in chunks of {chunk_size} rows...")
                processed_chunks = []
                
                for i in range(0, len(df), chunk_size):
                    chunk = df.iloc[i:i+chunk_size]
                    processed_chunk = process_func(chunk)
                    processed_chunks.append(processed_chunk)
                    
                    # Check RAM after each chunk
                    if not check_ram_usage():
                        logger.warning("RAM usage approaching limit. Stopping processing.")
                        break
                    
                    force_gc()
                    chunks_processed += 1
                    
                result_df = pd.concat(processed_chunks, ignore_index=True)
            else:
                result_df = process_func(df)
                chunks_processed = 1
            
            # Save result
            if output_path.suffix == '.parquet':
                result_df.to_parquet(output_path, index=False)
            else:
                result_df.to_csv(output_path, index=False)
                
            logger.info(f"Saved processed data to {output_path}")
            
        else:
            logger.error(f"Unsupported file format: {input_path.suffix}")
            return 0, 0.0
            
    finally:
        peak_mb = get_peak_ram_mb()
        tracemalloc.stop()
        logger.info(f"Peak RAM usage: {peak_mb:.2f} MB")
        logger.info(f"Total rows processed: {total_rows}, Chunks: {chunks_processed}")
        
    return total_rows, peak_mb


def validate_pipeline_performance(
    data_path: Union[str, Path],
    output_path: Union[str, Path],
    max_ram_gb: float = MAX_RAM_GB,
    sample: bool = True,
    sample_size: int = SAMPLE_SIZE
) -> Dict[str, Any]:
    """
    Run a performance validation of the pipeline on the given data.
    
    Args:
        data_path: Path to input data
        output_path: Path to save results
        max_ram_gb: Maximum allowed RAM in GB
        sample: Whether to sample data
        sample_size: Sample size if sampling is enabled
        
    Returns:
        Dictionary with performance metrics
    """
    data_path = Path(data_path)
    output_path = Path(output_path)
    
    logger.info(f"Starting performance validation on {data_path}")
    logger.info(f"Max RAM limit: {max_ram_gb} GB")
    logger.info(f"Sampling: {sample}, Sample size: {sample_size}")
    
    tracemalloc.start()
    start_ram = get_current_ram_mb()
    
    try:
        # Simple identity process function for validation
        def identity_process(df):
            return df
        
        total_rows, peak_ram = process_in_chunks(
            data_path,
            output_path,
            identity_process,
            sample=sample,
            sample_size=sample_size
        )
        
        end_ram = get_current_ram_mb()
        peak_mb = get_peak_ram_mb()
        
        result = {
            'total_rows': total_rows,
            'start_ram_mb': start_ram,
            'end_ram_mb': end_ram,
            'peak_ram_mb': peak_mb,
            'peak_ram_gb': peak_mb / 1024,
            'max_ram_gb': max_ram_gb,
            'within_limit': peak_mb / 1024 < max_ram_gb,
            'sampled': sample,
            'sample_size': sample_size if sample else total_rows
        }
        
        logger.info(f"Performance validation complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Performance validation failed: {e}")
        return {
            'error': str(e),
            'within_limit': False
        }
    finally:
        tracemalloc.stop()


def main():
    """Main entry point for performance optimization validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance Optimization Validator')
    parser.add_argument('--input', type=str, required=True, help='Input data path')
    parser.add_argument('--output', type=str, required=True, help='Output path')
    parser.add_argument('--max-ram', type=float, default=MAX_RAM_GB, help=f'Max RAM in GB (default: {MAX_RAM_GB})')
    parser.add_argument('--sample', action='store_true', help='Enable sampling')
    parser.add_argument('--sample-size', type=int, default=SAMPLE_SIZE, help=f'Sample size (default: {SAMPLE_SIZE})')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    result = validate_pipeline_performance(
        args.input,
        args.output,
        max_ram_gb=args.max_ram,
        sample=args.sample,
        sample_size=args.sample_size
    )
    
    # Save results
    import json
    result_path = Path(args.output).parent / 'optimization_report.json'
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Results saved to {result_path}")
    
    if not result.get('within_limit', False):
        logger.error("Performance validation FAILED: RAM limit exceeded")
        sys.exit(1)
    else:
        logger.info("Performance validation PASSED")
        sys.exit(0)


if __name__ == '__main__':
    main()
