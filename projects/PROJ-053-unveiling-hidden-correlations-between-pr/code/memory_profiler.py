"""
Memory profiling and optimization for the preprocessing pipeline.
Profiles memory usage of preprocess.py and applies optimizations if necessary.
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    get_project_root,
    get_processed_data_dir,
    get_raw_data_dir,
    get_results_dir,
    get_logs_dir,
    ensure_directories,
    get_logger
)
from data.preprocess import setup_logger, load_raw_csv, detect_missing_values, compute_medians, impute_missing_values, filter_derived_columns, encode_categorical, check_zero_variance, check_sample_count, split_and_scale, save_normalization_bounds, validate_and_preprocess


def profile_memory_usage(func, *args, **kwargs):
    """
    Profile memory usage of a function using memory_profiler or fallback to psutil.
    Returns (result, max_memory_mb).
    """
    max_memory_mb = 0.0
    
    try:
        from memory_profiler import memory_usage
        # Run the function and profile memory
        mem_usage, result = memory_usage((func, args, kwargs), max_iterations=1, timeout=300)
        if mem_usage:
            max_memory_mb = max(mem_usage)
    except ImportError:
        # Fallback to psutil if memory_profiler is not available
        try:
            import psutil
            process = psutil.Process(os.getpid())
            initial_mem = process.memory_info().rss / 1024 / 1024
            result = func(*args, **kwargs)
            final_mem = process.memory_info().rss / 1024 / 1024
            max_memory_mb = final_mem - initial_mem
        except ImportError:
            # If neither is available, just run the function
            result = func(*args, **kwargs)
            logging.warning("Neither memory_profiler nor psutil available. Memory profiling skipped.")
    
    return result, max_memory_mb


def optimize_dataframe(df: pd.DataFrame, logger: logging.Logger) -> tuple:
    """
    Optimize memory usage of a DataFrame by:
    1. Converting numeric columns to float32
    2. Using categorical dtype for low-cardinality string columns
    3. Dropping unused columns immediately
    
    Returns (optimized_df, memory_before_mb, memory_after_mb, savings_mb)
    """
    memory_before = df.memory_usage(deep=True).sum() / 1024 / 1024
    
    # Convert numeric columns to float32
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df[col] = df[col].astype(np.float32)
    
    # Convert string/object columns to categorical if low cardinality
    for col in df.select_dtypes(include=['object', 'string']).columns:
        if df[col].nunique() / len(df) < 0.5:  # Low cardinality threshold
            df[col] = df[col].astype('category')
    
    memory_after = df.memory_usage(deep=True).sum() / 1024 / 1024
    savings = memory_before - memory_after
    
    logger.info(f"Memory optimization: {memory_before:.2f} MB -> {memory_after:.2f} MB (saved {savings:.2f} MB)")
    
    return df, memory_before, memory_after, savings


def run_memory_profile():
    """
    Main function to profile memory usage and apply optimizations if necessary.
    """
    # Setup
    project_root = get_project_root()
    results_dir = get_results_dir()
    logs_dir = get_logs_dir()
    ensure_directories()
    
    logger = setup_logger('memory_profiler', logs_dir)
    logger.info("Starting memory profiling...")
    
    # Path to raw data
    raw_data_path = get_raw_data_dir() / "am_data.csv"
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found: {raw_data_path}")
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
    
    # Profile initial loading and preprocessing
    logger.info("Profiling initial data loading and preprocessing...")
    
    try:
        # Profile the full preprocessing pipeline
        result, max_memory_mb = profile_memory_usage(
            validate_and_preprocess,
            str(raw_data_path),
            logger
        )
        
        logger.info(f"Preprocessing completed. Max memory usage: {max_memory_mb:.2f} MB")
        
        # Log initial profile
        profile_result = {
            "max_memory_mb": max_memory_mb,
            "status": "initial_profile",
            "data_path": str(raw_data_path),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Check if optimization is needed
        if max_memory_mb >= 7000:
            logger.warning(f"Memory usage ({max_memory_mb:.2f} MB) exceeds threshold (7000 MB). Applying optimizations...")
            
            # Reload data with optimizations
            logger.info("Reloading data with memory optimizations...")
            
            # Load raw CSV with chunked reading
            chunk_size = 10000
            chunks = []
            memory_savings = 0
            
            for chunk in pd.read_csv(raw_data_path, chunksize=chunk_size):
                # Optimize each chunk
                chunk, _, _, savings = optimize_dataframe(chunk, logger)
                memory_savings += savings
                chunks.append(chunk)
            
            # Combine chunks
            df_optimized = pd.concat(chunks, ignore_index=True)
            
            # Drop unused columns immediately
            # (This is already handled by filter_derived_columns and other steps)
            
            logger.info(f"Total memory savings from optimization: {memory_savings:.2f} MB")
            
            # Re-run preprocessing with optimized data
            logger.info("Re-running preprocessing with optimized data...")
            
            # Save optimized data temporarily
            temp_path = get_raw_data_dir() / "am_data_optimized.csv"
            df_optimized.to_csv(temp_path, index=False)
            
            # Profile again
            result_optimized, max_memory_mb_optimized = profile_memory_usage(
                validate_and_preprocess,
                str(temp_path),
                logger
            )
            
            logger.info(f"Optimized preprocessing completed. Max memory usage: {max_memory_mb_optimized:.2f} MB")
            
            # Update profile result
            profile_result.update({
                "status": "optimized",
                "initial_memory_mb": max_memory_mb,
                "optimized_memory_mb": max_memory_mb_optimized,
                "memory_savings_mb": max_memory_mb - max_memory_mb_optimized,
                "optimization_applied": True
            })
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            
        else:
            logger.info(f"Memory usage ({max_memory_mb:.2f} MB) is within acceptable limits. No optimization needed.")
            profile_result["optimization_applied"] = False
            profile_result["optimized_memory_mb"] = max_memory_mb
        
        # Save profile result
        profile_path = results_dir / "memory_profile.log"
        with open(profile_path, 'w') as f:
            json.dump(profile_result, f, indent=2)
        
        logger.info(f"Memory profile saved to {profile_path}")
        
        return profile_result
        
    except Exception as e:
        logger.error(f"Memory profiling failed: {str(e)}", exc_info=True)
        raise


def main():
    """Entry point for memory profiling."""
    try:
        result = run_memory_profile()
        print(f"Memory profiling completed successfully.")
        print(f"Max memory usage: {result['max_memory_mb']:.2f} MB")
        if result.get('optimization_applied'):
            print(f"Optimized memory usage: {result['optimized_memory_mb']:.2f} MB")
            print(f"Memory savings: {result['memory_savings_mb']:.2f} MB")
    except Exception as e:
        print(f"Memory profiling failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()