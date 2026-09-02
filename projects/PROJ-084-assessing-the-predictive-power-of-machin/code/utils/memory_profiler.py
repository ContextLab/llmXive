"""
Memory profiling utilities for memory-bounded execution.

This module provides functions to profile memory usage, enforce memory limits,
and generate memory profiling reports during training.
"""

import gc
import logging
import tracemalloc
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import psutil
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/memory_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Global profiling state
_profiling_active = False
_memory_samples: List[Dict[str, Any]] = []
_peak_memory_mb = 0.0
_start_time: Optional[float] = None

def start_profiling():
    """Start memory profiling."""
    global _profiling_active, _memory_samples, _peak_memory_mb, _start_time
    
    if _profiling_active:
        logger.warning("Profiling already active")
        return
    
    logger.info("Starting memory profiling")
    tracemalloc.start()
    _profiling_active = True
    _memory_samples = []
    _peak_memory_mb = 0.0
    _start_time = time.time()
    
    # Initial sample
    _sample_memory()

def stop_profiling():
    """Stop memory profiling."""
    global _profiling_active
    
    if not _profiling_active:
        logger.warning("Profiling not active")
        return
    
    logger.info("Stopping memory profiling")
    _sample_memory()
    tracemalloc.stop()
    _profiling_active = False

def _sample_memory():
    """Sample current memory usage and update peak."""
    global _peak_memory_mb
    
    try:
        # Get current memory usage
        process = psutil.Process()
        mem_info = process.memory_info()
        current_mb = mem_info.rss / (1024 * 1024)
        
        # Get tracemalloc stats if available
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            current_mb = max(current_mb, current / (1024 * 1024))
            peak_mb = peak / (1024 * 1024)
            _peak_memory_mb = max(_peak_memory_mb, peak_mb)
        else:
            _peak_memory_mb = max(_peak_memory_mb, current_mb)
        
        # Record sample
        sample = {
            'timestamp': time.time() - (_start_time or time.time()),
            'memory_mb': current_mb,
            'peak_memory_mb': _peak_memory_mb
        }
        _memory_samples.append(sample)
        
        logger.debug(f"Memory sample: {current_mb:.2f} MB, Peak: {_peak_memory_mb:.2f} MB")
        
    except Exception as e:
        logger.error(f"Error sampling memory: {e}")

def get_current_memory_mb() -> float:
    """Get current memory usage in MB."""
    try:
        process = psutil.Process()
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024)
    except Exception as e:
        logger.error(f"Error getting current memory: {e}")
        return 0.0

def get_peak_memory_mb() -> float:
    """Get peak memory usage during profiling in MB."""
    if _memory_samples:
        return max(sample['peak_memory_mb'] for sample in _memory_samples)
    return _peak_memory_mb

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """
    Check if current memory usage is within limit.
    
    Args:
        limit_gb: Memory limit in GB
        
    Returns:
        True if within limit, False otherwise
        
    Raises:
        MemoryError if limit exceeded
    """
    current_mb = get_current_memory_mb()
    limit_mb = limit_gb * 1024
    
    if current_mb > limit_mb:
        error_msg = f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB"
        logger.error(error_msg)
        raise MemoryError(error_msg)
    
    logger.debug(f"Memory check passed: {current_mb:.2f} MB < {limit_mb:.2f} MB")
    return True

def force_gc():
    """Force garbage collection."""
    logger.debug("Forcing garbage collection")
    gc.collect()
    gc.collect()
    gc.collect()

def profile_training_block(func, *args, **kwargs) -> Any:
    """
    Profile a training block with memory monitoring.
    
    Args:
        func: Function to profile
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Result of the function
    """
    start_mem = get_current_memory_mb()
    logger.info(f"Starting block, initial memory: {start_mem:.2f} MB")
    
    try:
        result = func(*args, **kwargs)
        end_mem = get_current_memory_mb()
        delta_mem = end_mem - start_mem
        logger.info(f"Block completed, memory delta: {delta_mem:.2f} MB")
        return result
    except MemoryError as e:
        logger.error(f"MemoryError in block: {e}")
        raise
    finally:
        force_gc()

def save_memory_profile_log(output_path: str):
    """
    Save memory profile log to file.
    
    Args:
        output_path: Path to output log file
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write("Memory Profile Log\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total samples: {len(_memory_samples)}\n")
            f.write(f"Peak memory: {_peak_memory_mb:.2f} MB\n")
            f.write("=" * 50 + "\n\n")
            
            if _memory_samples:
                f.write("Time (s)\tMemory (MB)\tPeak (MB)\n")
                for sample in _memory_samples:
                    f.write(f"{sample['timestamp']:.2f}\t{sample['memory_mb']:.2f}\t{sample['peak_memory_mb']:.2f}\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("Summary\n")
            f.write(f"Peak memory: {_peak_memory_mb:.2f} MB\n")
            if _memory_samples:
                f.write(f"Final memory: {_memory_samples[-1]['memory_mb']:.2f} MB\n")
                f.write(f"Memory increase: {_memory_samples[-1]['memory_mb'] - _memory_samples[0]['memory_mb']:.2f} MB\n")
        
        logger.info(f"Memory profile log saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving memory profile log: {e}")
        raise

def main():
    """Test memory profiling functionality."""
    logger.info("Testing memory profiling")
    
    start_profiling()
    
    # Simulate some memory usage
    data = []
    for i in range(1000):
        data.append(np.random.randn(1000, 100))
        if i % 100 == 0:
            _sample_memory()
            current_mem = get_current_memory_mb()
            logger.info(f"Progress {i}/1000, memory: {current_mem:.2f} MB")
    
    # Check memory limit
    try:
        check_memory_limit(7.0)
        logger.info("Memory limit check passed")
    except MemoryError as e:
        logger.error(f"Memory limit check failed: {e}")
    
    stop_profiling()
    
    # Save log
    save_memory_profile_log('data/results/memory_profile.log')
    
    logger.info("Memory profiling test completed")

if __name__ == '__main__':
    main()