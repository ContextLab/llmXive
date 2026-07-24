import os
import sys
import gc
import json
import logging
import time
import resource
from typing import Optional, List, Dict, Any, Iterator
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
GC_THRESHOLD = 100  # MB to trigger forced GC

class MemoryExceededError(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

def get_current_memory_mb() -> float:
    """Get current memory usage in MB using resource module."""
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on macOS
        if sys.platform == 'darwin':
            return usage.ru_maxrss / (1024 * 1024)
        else:
            return usage.ru_maxrss / 1024
    except Exception as e:
        logger.warning(f"Could not read memory usage: {e}")
        return 0.0

def check_memory_limit(limit_mb: Optional[float] = None) -> bool:
    """Check if current memory usage is within limits."""
    if limit_mb is None:
        limit_mb = MEMORY_LIMIT_MB
    
    current_mb = get_current_memory_mb()
    logger.debug(f"Current memory usage: {current_mb:.2f} MB / {limit_mb:.2f} MB limit")
    
    if current_mb > limit_mb:
        logger.error(f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB")
        return False
    return True

def force_gc(threshold_mb: float = GC_THRESHOLD) -> int:
    """Force garbage collection if memory is high. Returns memory freed in MB."""
    current = get_current_memory_mb()
    if current > threshold_mb:
        logger.info(f"Memory usage ({current:.2f} MB) exceeds threshold ({threshold_mb:.2f} MB). Running GC.")
        gc.collect()
        new_current = get_current_memory_mb()
        freed = current - new_current
        logger.info(f"GC freed {freed:.2f} MB. New usage: {new_current:.2f} MB")
        return freed
    return 0.0

class MemoryMonitor:
    """Context manager and utility for monitoring memory during operations."""
    
    def __init__(self, limit_mb: float = MEMORY_LIMIT_MB, check_interval: float = 1.0):
        self.limit_mb = limit_mb
        self.check_interval = check_interval
        self.start_time: Optional[float] = None
        self.max_memory_mb: float = 0.0
        self.samples: List[Dict[str, Any]] = []
    
    def __enter__(self):
        self.start_time = time.time()
        self.max_memory_mb = get_current_memory_mb()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time if self.start_time else 0
        logger.info(f"MemoryMonitor: Max usage {self.max_memory_mb:.2f} MB over {elapsed:.2f}s")
        if self.max_memory_mb > self.limit_mb:
            logger.error(f"Memory limit exceeded during operation: {self.max_memory_mb:.2f} MB > {self.limit_mb:.2f} MB")
        return False
    
    def check(self, force_gc_if_high: bool = True) -> bool:
        """Check memory and optionally force GC. Returns True if within limits."""
        current = get_current_memory_mb()
        self.max_memory_mb = max(self.max_memory_mb, current)
        
        if current > self.limit_mb:
            logger.error(f"Memory limit exceeded: {current:.2f} MB > {self.limit_mb:.2f} MB")
            return False
        
        if force_gc_if_high and current > self.limit_mb * 0.9:
            force_gc()
        
        return True
    
    def get_report(self) -> Dict[str, Any]:
        """Generate a memory usage report."""
        return {
            "max_memory_mb": self.max_memory_mb,
            "limit_mb": self.limit_mb,
            "status": "OK" if self.max_memory_mb <= self.limit_mb else "EXCEEDED",
            "samples_count": len(self.samples)
        }

def stream_csv_batch(
    input_path: str,
    output_path: str,
    batch_size: int = 10000,
    memory_limit_mb: float = MEMORY_LIMIT_MB
) -> str:
    """
    Process a large CSV file in batches to stay under memory limits.
    Reads, processes (identity transform for optimization), and writes in chunks.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV
        batch_size: Number of rows per batch
        memory_limit_mb: Maximum memory allowed in MB
    
    Returns:
        Path to the output file
    """
    logger.info(f"Starting batch processing of {input_path} with batch_size={batch_size}")
    
    if not check_memory_limit(memory_limit_mb):
        raise MemoryExceededError(f"Initial memory usage exceeds limit: {get_current_memory_mb():.2f} MB")
    
    total_rows = 0
    monitor = MemoryMonitor(limit_mb=memory_limit_mb)
    
    with monitor:
        # Use chunks to read
        chunks = pd.read_csv(input_path, chunksize=batch_size)
        
        # Write header only once
        first_chunk = True
        
        for i, chunk in enumerate(chunks):
            if not monitor.check(force_gc_if_high=True):
                raise MemoryExceededError(f"Memory limit exceeded at batch {i}")
            
            # Optimize dtypes in-place to reduce memory
            chunk = optimize_dataframe_dtypes(chunk)
            
            # Write to output
            mode = 'w' if first_chunk else 'a'
            header = first_chunk
            chunk.to_csv(output_path, mode=mode, index=False, header=header)
            first_chunk = False
            total_rows += len(chunk)
            
            if i % 10 == 0:
                logger.info(f"Processed {total_rows} rows. Current memory: {get_current_memory_mb():.2f} MB")
        
        logger.info(f"Completed processing {total_rows} rows. Final memory: {get_current_memory_mb():.2f} MB")
    
    return output_path

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
            # Check if it's a numpy array or torch tensor
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

def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize memory usage of a pandas DataFrame by downcasting numeric types
    and converting object columns to categorical where appropriate.
    
    Args:
        df: Input DataFrame
    
    Returns:
        Optimized DataFrame
    """
    logger.debug(f"Optimizing DataFrame with {len(df)} rows and {len(df.columns)} columns")
    initial_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type == object:
            # Check if categorical makes sense
            unique_count = df[col].nunique()
            total_count = len(df)
            if unique_count < total_count * 0.5:
                df[col] = df[col].astype('category')
        elif col_type == np.float64:
            df[col] = pd.to_numeric(df[col], downcast='float')
        elif col_type == np.int64:
            df[col] = pd.to_numeric(df[col], downcast='integer')
    
    final_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
    logger.debug(f"DataFrame memory: {initial_memory:.2f} MB -> {final_memory:.2f} MB")
    return df

def main():
    """Main entry point for memory optimization demonstration and validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Optimization Tool")
    parser.add_argument("--input", type=str, help="Input CSV file to process")
    parser.add_argument("--output", type=str, help="Output CSV file path")
    parser.add_argument("--batch-size", type=int, default=10000, help="Batch size for streaming")
    parser.add_argument("--limit", type=float, default=MEMORY_LIMIT_MB, help="Memory limit in MB")
    args = parser.parse_args()
    
    if args.input and args.output:
        try:
            output_path = stream_csv_batch(args.input, args.output, args.batch_size, args.limit)
            print(f"Successfully processed file. Output: {output_path}")
            print(f"Final memory usage: {get_current_memory_mb():.2f} MB")
        except MemoryExceededError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)
    else:
        print("Usage: python memory_monitor.py --input <file> --output <file>")
        sys.exit(1)

if __name__ == "__main__":
    main()
