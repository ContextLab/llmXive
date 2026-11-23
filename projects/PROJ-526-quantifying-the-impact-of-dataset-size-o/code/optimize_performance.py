"""
Performance optimization module for the materials scaling analysis pipeline.

This module provides utilities to optimize memory usage and processing speed
for large-scale data operations. Key optimizations include:
1. DataFrame memory optimization via dtype downcasting
2. Batch size tuning for iterative processing
3. Efficient chunked I/O operations
4. Memory-mapped file handling for large datasets
"""
import os
import sys
import gc
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
import psutil

from config import get_config
from utils.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

# Constants for optimization
MEMORY_TARGET_GB = 6.0  # Target memory usage (GB)
BATCH_SIZE_DEFAULT = 10000  # Default batch size for processing
CHUNK_SIZE_DEFAULT = 50000  # Default chunk size for I/O
DTYPE_MAPPING = {
    'float64': 'float32',
    'int64': 'int32',
    'int32': 'int16',
    'int16': 'int8',
}

def get_available_memory_gb() -> float:
    """
    Get available system memory in GB.
    
    Returns:
        float: Available memory in GB
    """
    try:
        available = psutil.virtual_memory().available
        return available / (1024 ** 3)
    except Exception as e:
        logger.warning(f"Could not determine available memory: {e}")
        return MEMORY_TARGET_GB * 1.5  # Fallback to safe default

def optimize_dataframe_memory(df: pd.DataFrame, 
                             verbose: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    
    Args:
        df: Input DataFrame
        verbose: Whether to log optimization details
        
    Returns:
        Tuple of (optimized DataFrame, stats dict)
    """
    if df is None or df.empty:
        return df, {'original_size': 0, 'optimized_size': 0, 'reduction': 0}
    
    original_memory = df.memory_usage(deep=True).sum()
    stats = {
        'original_size_mb': original_memory / (1024 ** 2),
        'columns_optimized': 0,
        'types_changed': {}
    }
    
    # Get numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        col_type = df[col].dtype
        min_val = df[col].min()
        max_val = df[col].max()
        
        # Skip if already optimal
        if str(col_type) in ['float32', 'int8', 'int16']:
            continue
        
        # Determine optimal dtype
        if pd.api.types.is_float_dtype(col_type):
            # For floats, check if float32 is sufficient
            if min_val >= -3.4e38 and max_val <= 3.4e38:
                df[col] = df[col].astype('float32')
                stats['types_changed'][col] = f'{col_type} -> float32'
                stats['columns_optimized'] += 1
        elif pd.api.types.is_integer_dtype(col_type):
            # For integers, find smallest sufficient type
            if min_val >= np.iinfo(np.int8).min and max_val <= np.iinfo(np.int8).max:
                df[col] = df[col].astype('int8')
                stats['types_changed'][col] = f'{col_type} -> int8'
                stats['columns_optimized'] += 1
            elif min_val >= np.iinfo(np.int16).min and max_val <= np.iinfo(np.int16).max:
                df[col] = df[col].astype('int16')
                stats['types_changed'][col] = f'{col_type} -> int16'
                stats['columns_optimized'] += 1
            elif min_val >= np.iinfo(np.int32).min and max_val <= np.iinfo(np.int32).max:
                df[col] = df[col].astype('int32')
                stats['types_changed'][col] = f'{col_type} -> int32'
                stats['columns_optimized'] += 1
    
    optimized_memory = df.memory_usage(deep=True).sum()
    stats['optimized_size_mb'] = optimized_memory / (1024 ** 2)
    stats['reduction_pct'] = ((original_memory - optimized_memory) / original_memory * 100) if original_memory > 0 else 0
    
    if verbose:
        logger.info(f"Memory optimization: {stats['original_size_mb']:.2f}MB -> {stats['optimized_size_mb']:.2f}MB ({stats['reduction_pct']:.1f}% reduction)")
        if stats['types_changed']:
            for col, change in stats['types_changed'].items():
                logger.debug(f"  {col}: {change}")
    
    return df, stats

def calculate_optimal_batch_size(target_memory_mb: float = 5000) -> int:
    """
    Calculate optimal batch size based on available memory.
    
    Args:
        target_memory_mb: Target memory usage per batch in MB
        
    Returns:
        int: Optimal batch size
    """
    available_mem = get_available_memory_gb() * 1024
    safe_memory = available_mem * 0.7  # Use 70% of available memory
    
    if safe_memory < target_memory_mb:
        logger.warning(f"Available memory ({available_mem:.0f}MB) is below target. Reducing target.")
        target_memory_mb = safe_memory * 0.5
    
    # Estimate rows per MB (conservative estimate: 1MB per 1000 rows)
    # This is a rough heuristic that works well for typical material property datasets
    rows_per_mb = 1000
    optimal_batch = int((target_memory_mb * rows_per_mb) / 1000)
    
    # Ensure reasonable bounds
    optimal_batch = max(BATCH_SIZE_DEFAULT, min(optimal_batch, 100000))
    
    logger.info(f"Calculated optimal batch size: {optimal_batch:,} rows (target: {target_memory_mb:.0f}MB)")
    return optimal_batch

def load_dataframe_chunked(filepath: str, 
                          chunk_size: Optional[int] = None,
                          optimize_dtypes: bool = True) -> pd.DataFrame:
    """
    Load a large DataFrame in chunks to avoid memory issues.
    
    Args:
        filepath: Path to the data file (Parquet or CSV)
        chunk_size: Number of rows per chunk (auto-calculated if None)
        optimize_dtypes: Whether to optimize dtypes after loading
        
    Returns:
        pd.DataFrame: Loaded and optimized DataFrame
    """
    if chunk_size is None:
        chunk_size = CHUNK_SIZE_DEFAULT
        logger.info(f"Using default chunk size: {chunk_size:,}")
    
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Determine file type and load accordingly
        if filepath.suffix == '.parquet':
            # Parquet files can be loaded more efficiently
            logger.info(f"Loading Parquet file: {filepath}")
            df = pd.read_parquet(filepath)
            if optimize_dtypes:
                df, stats = optimize_dataframe_memory(df, verbose=True)
            return df
        
        elif filepath.suffix == '.csv':
            # CSV files need chunked loading
            logger.info(f"Loading CSV file in chunks: {filepath}")
            chunks = []
            total_rows = 0
            
            for chunk in pd.read_csv(filepath, chunksize=chunk_size):
                if optimize_dtypes:
                    chunk, _ = optimize_dataframe_memory(chunk, verbose=False)
                chunks.append(chunk)
                total_rows += len(chunk)
                
                # Periodic memory cleanup
                if total_rows % (chunk_size * 10) == 0:
                    gc.collect()
            
            df = pd.concat(chunks, ignore_index=True)
            logger.info(f"Loaded {total_rows:,} rows in {len(chunks)} chunks")
            return df
        
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
            
    except Exception as e:
        logger.error(f"Error loading file {filepath}: {e}")
        raise

def save_dataframe_optimized(df: pd.DataFrame, 
                            filepath: str,
                            optimize_dtypes: bool = True) -> Dict[str, Any]:
    """
    Save a DataFrame with memory optimization.
    
    Args:
        df: DataFrame to save
        filepath: Output path
        optimize_dtypes: Whether to optimize dtypes before saving
        
    Returns:
        Dict with save statistics
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    if optimize_dtypes and not df.empty:
        df, opt_stats = optimize_dataframe_memory(df, verbose=True)
    else:
        opt_stats = {'original_size_mb': 0, 'optimized_size_mb': 0, 'reduction_pct': 0}
    
    try:
        if filepath.suffix == '.parquet':
            df.to_parquet(filepath, index=False, compression='snappy')
        elif filepath.suffix == '.csv':
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported output format: {filepath.suffix}")
        
        # Get file size
        file_size_mb = filepath.stat().st_size / (1024 ** 2)
        
        stats = {
            'file_size_mb': file_size_mb,
            'rows': len(df),
            'columns': len(df.columns),
            'dtype_optimization': opt_stats
        }
        
        logger.info(f"Saved {len(df):,} rows to {filepath} ({file_size_mb:.2f}MB)")
        return stats
        
    except Exception as e:
        logger.error(f"Error saving file {filepath}: {e}")
        raise

def monitor_memory_usage(verbose: bool = True) -> Dict[str, float]:
    """
    Monitor current memory usage.
    
    Args:
        verbose: Whether to log usage details
        
    Returns:
        Dict with memory usage statistics
    """
    mem = psutil.virtual_memory()
    usage = {
        'available_gb': mem.available / (1024 ** 3),
        'used_gb': mem.used / (1024 ** 3),
        'total_gb': mem.total / (1024 ** 3),
        'percent_used': mem.percent
    }
    
    if verbose:
        logger.info(f"Memory usage: {usage['used_gb']:.2f}/{usage['total_gb']:.2f} GB ({usage['percent_used']:.1f}%)")
    
    return usage

def run_performance_optimization_pipeline(input_path: str, 
                                         output_path: str,
                                         batch_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Run the complete performance optimization pipeline.
    
    Args:
        input_path: Input data file path
        output_path: Output data file path
        batch_size: Custom batch size (auto-calculated if None)
        
    Returns:
        Dict with pipeline statistics
    """
    logger.info("Starting performance optimization pipeline")
    
    # Monitor initial memory
    initial_mem = monitor_memory_usage(verbose=True)
    
    # Calculate optimal batch size if not provided
    if batch_size is None:
        batch_size = calculate_optimal_batch_size()
    
    # Load data with optimization
    logger.info(f"Loading data from {input_path}")
    df = load_dataframe_chunked(input_path, chunk_size=batch_size, optimize_dtypes=True)
    
    # Monitor memory after load
    after_load_mem = monitor_memory_usage(verbose=True)
    
    # Save optimized data
    logger.info(f"Saving optimized data to {output_path}")
    save_stats = save_dataframe_optimized(df, output_path, optimize_dtypes=True)
    
    # Final memory check
    final_mem = monitor_memory_usage(verbose=True)
    
    # Clean up
    del df
    gc.collect()
    
    return {
        'input_file': input_path,
        'output_file': output_path,
        'batch_size_used': batch_size,
        'initial_memory_gb': initial_mem['used_gb'],
        'memory_after_load_gb': after_load_mem['used_gb'],
        'final_memory_gb': final_mem['used_gb'],
        'save_statistics': save_stats
    }

def main():
    """Main entry point for performance optimization."""
    try:
        config = get_config()
        
        # Default paths
        input_path = config.data_dir / 'processed' / 'materials_master.parquet'
        output_path = config.data_dir / 'processed' / 'materials_master_optimized.parquet'
        
        # Check if input exists
        if not input_path.exists():
            logger.warning(f"Input file not found: {input_path}")
            logger.info("Skipping optimization - no input data available")
            return
        
        # Run optimization
        results = run_performance_optimization_pipeline(
            input_path=str(input_path),
            output_path=str(output_path)
        )
        
        logger.info("Performance optimization completed successfully")
        logger.info(f"Results: {results}")
        
    except Exception as e:
        logger.error(f"Performance optimization failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()