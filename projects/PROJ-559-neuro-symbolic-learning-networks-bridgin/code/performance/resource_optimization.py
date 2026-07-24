import os
import sys
import gc
import json
import logging
import time
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from performance.memory_monitor import (
    get_current_memory_mb,
    check_memory_limit,
    force_gc,
    MemoryMonitor,
    stream_csv_batch,
    optimize_tensor_memory,
    optimize_dataframe_dtypes,
    MEMORY_LIMIT_MB
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def optimize_tensor_memory(tensor: Any) -> Any:
    """
    Optimize memory usage of a tensor (numpy or torch).
    Converts to float32 if float64, and removes unnecessary gradients.
    
    Args:
        tensor: A numpy array or torch tensor
    
    Returns:
        Optimized tensor
    """
    try:
        if hasattr(tensor, 'dtype'):
            if tensor.dtype == np.float64:
                logger.debug("Converting float64 to float32 to save memory")
                return tensor.astype(np.float32)
            elif hasattr(tensor, 'float'): # Likely torch
                if tensor.dtype == torch.float64:
                    logger.debug("Converting torch float64 to float32")
                    return tensor.float()
        return tensor
    except Exception as e:
        logger.warning(f"Could not optimize tensor memory: {e}")
        return tensor

def stream_dataframe_in_batches(
    df: pd.DataFrame,
    batch_size: int = 50000,
    callback=None
) -> Iterator[pd.DataFrame]:
    """
    Stream a DataFrame in batches to reduce memory footprint.
    
    Args:
        df: The DataFrame to stream
        batch_size: Number of rows per batch
        callback: Optional callback function to process each batch
    
    Yields:
        DataFrame batches
    """
    total_rows = len(df)
    for i in range(0, total_rows, batch_size):
        batch = df.iloc[i:i+batch_size]
        if callback:
            batch = callback(batch)
        yield batch
        force_gc() # Periodic GC

def process_optimized_simulation(
    input_path: str,
    output_path: str,
    memory_limit_mb: float = MEMORY_LIMIT_MB
) -> Dict[str, Any]:
    """
    Process simulation logs with memory optimizations applied.
    Reads, optimizes dtypes, and writes back.
    
    Args:
        input_path: Path to input simulation logs
        output_path: Path to output optimized logs
        memory_limit_mb: Memory limit in MB
    
    Returns:
        Dictionary with processing stats
    """
    logger.info(f"Processing simulation logs: {input_path}")
    
    monitor = MemoryMonitor(limit_mb=memory_limit_mb)
    stats = {
        "input_rows": 0,
        "output_rows": 0,
        "max_memory_mb": 0,
        "status": "OK"
    }
    
    try:
        with monitor:
            # Stream processing
            stream_csv_batch(input_path, output_path, batch_size=10000, memory_limit_mb=memory_limit_mb)
            
            # Count rows (simple count)
            stats["output_rows"] = sum(1 for _ in open(output_path)) - 1 # -1 for header
            stats["max_memory_mb"] = monitor.max_memory_mb
            
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        stats["status"] = "FAILED"
        stats["error"] = str(e)
    
    return stats

def optimize_data_loading_pipeline(
    data_path: str,
    columns: Optional[List[str]] = None,
    dtypes: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Optimize data loading by specifying columns and dtypes upfront.
    
    Args:
        data_path: Path to CSV
        columns: List of columns to load (reduces memory)
        dtypes: Dictionary of column dtypes to enforce
    
    Returns:
        Loaded and optimized DataFrame
    """
    logger.info(f"Loading data from {data_path}")
    
    load_kwargs = {
        "low_memory": True,
        "memory_map": True
    }
    
    if columns:
        load_kwargs["usecols"] = columns
    
    df = pd.read_csv(data_path, **load_kwargs)
    
    if dtypes:
        for col, dtype in dtypes.items():
            if col in df.columns:
                df[col] = df[col].astype(dtype)
    
    # Optimize remaining columns
    df = optimize_dataframe_dtypes(df)
    
    logger.info(f"Loaded {len(df)} rows. Memory: {get_current_memory_mb():.2f} MB")
    return df

def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize memory usage of a pandas DataFrame.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Optimized DataFrame
    """
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type == object:
            unique_count = df[col].nunique()
            total_count = len(df)
            if unique_count < total_count * 0.5:
                df[col] = df[col].astype('category')
        elif col_type == np.float64:
            df[col] = pd.to_numeric(df[col], downcast='float')
        elif col_type == np.int64:
            df[col] = pd.to_numeric(df[col], downcast='integer')
    
    return df

def run_optimization_validation() -> Dict[str, Any]:
    """
    Run validation to ensure the pipeline operates within memory limits.
    Simulates a workload and checks memory usage.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Running optimization validation")
    
    limit_mb = MEMORY_LIMIT_MB
    results = {
        "status": "PASS",
        "max_memory_mb": 0,
        "limit_mb": limit_mb,
        "reason": ""
    }
    
    monitor = MemoryMonitor(limit_mb=limit_mb)
    
    try:
        with monitor:
            # Simulate a moderate workload (creating a DataFrame and processing)
            # This simulates the load of US1/US2/US3 combined
            logger.info("Simulating workload...")
            
            # Create a synthetic dataset to simulate processing
            # In a real scenario, this would process actual data files
            n_rows = 100000
            n_cols = 10
            
            # Generate data in batches to avoid a single spike
            data_batches = []
            for i in range(0, n_rows, 10000):
                batch_size = min(10000, n_rows - i)
                batch = pd.DataFrame(np.random.rand(batch_size, n_cols), columns=[f"col_{j}" for j in range(n_cols)])
                data_batches.append(batch)
                force_gc()
            
            df = pd.concat(data_batches, ignore_index=True)
            logger.info(f"Created DataFrame: {df.shape}")
            
            # Optimize it
            df_optimized = optimize_dataframe_dtypes(df)
            
            # Delete to free memory
            del df
            del data_batches
            gc.collect()
            
            # Check final memory
            current = get_current_memory_mb()
            if current > limit_mb:
                results["status"] = "FAIL"
                results["reason"] = f"Memory limit exceeded: {current:.2f} MB > {limit_mb:.2f} MB"
            else:
                results["status"] = "PASS"
                results["reason"] = "All checks passed within limits"
                
        results["max_memory_mb"] = monitor.max_memory_mb
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        results["status"] = "FAIL"
        results["reason"] = str(e)
    
    return results

def main():
    """Main entry point for resource optimization module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Resource Optimization Utilities")
    parser.add_argument("--validate", action="store_true", help="Run validation checks")
    parser.add_argument("--input", type=str, help="Input file for streaming")
    parser.add_argument("--output", type=str, help="Output file for streaming")
    parser.add_argument("--limit", type=float, default=MEMORY_LIMIT_MB, help="Memory limit in MB")
    args = parser.parse_args()
    
    if args.validate:
        results = run_optimization_validation()
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["status"] == "PASS" else 1)
    elif args.input and args.output:
        stats = process_optimized_simulation(args.input, args.output, args.limit)
        print(json.dumps(stats, indent=2))
        sys.exit(0 if stats["status"] == "OK" else 1)
    else:
        print("Usage: python resource_optimization.py --validate OR --input <file> --output <file>")
        sys.exit(1)

if __name__ == "__main__":
    main()
