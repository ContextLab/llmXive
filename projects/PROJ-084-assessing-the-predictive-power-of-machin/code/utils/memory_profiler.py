"""
Memory profiling utilities for the ML pipeline.

This module provides functionality to track RAM usage during model training
and generate a memory profile log. It enforces the 7GB RAM constraint.
"""
import gc
import logging
import tracemalloc
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_MEMORY_GB = 7.0
MAX_MEMORY_MB = MAX_MEMORY_GB * 1024


def start_profiling() -> None:
    """Start the tracemalloc memory profiler."""
    if tracemalloc.is_tracing():
        logger.warning("tracemalloc is already tracing.")
        return
    tracemalloc.start()
    logger.info("tracemalloc started.")


def stop_profiling() -> None:
    """Stop the tracemalloc memory profiler."""
    if not tracemalloc.is_tracing():
        logger.warning("tracemalloc is not tracing.")
        return
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    logger.info(f"tracemalloc stopped. Peak memory: {peak / 1024 / 1024:.2f} MB")
    return current, peak


def get_current_memory_mb() -> float:
    """Get the current memory usage in MB."""
    if not tracemalloc.is_tracing():
        raise RuntimeError("tracemalloc is not tracing. Call start_profiling() first.")
    current, _ = tracemalloc.get_traced_memory()
    return current / 1024 / 1024


def get_peak_memory_mb() -> float:
    """Get the peak memory usage since tracing started in MB."""
    if not tracemalloc.is_tracing():
        raise RuntimeError("tracemalloc is not tracing. Call start_profiling() first.")
    _, peak = tracemalloc.get_traced_memory()
    return peak / 1024 / 1024


def check_memory_limit(peak_mb: float, limit_mb: float = MAX_MEMORY_MB) -> bool:
    """
    Check if peak memory usage is within the limit.
    
    Args:
        peak_mb: Peak memory usage in MB.
        limit_mb: Memory limit in MB (default: 7GB).
        
    Returns:
        True if within limit, False otherwise.
    """
    if peak_mb > limit_mb:
        logger.error(f"Memory limit exceeded: {peak_mb:.2f} MB > {limit_mb:.2f} MB")
        return False
    logger.info(f"Memory check passed: {peak_mb:.2f} MB <= {limit_mb:.2f} MB")
    return True


def force_gc() -> None:
    """Force garbage collection to free up memory."""
    gc.collect()
    logger.debug("Garbage collection forced.")


def profile_training_block(
    training_func,
    *args,
    output_path: Optional[Path] = None,
    **kwargs
) -> Any:
    """
    Profile a training block and optionally save the memory profile log.
    
    This function starts tracing, executes the training function, stops tracing,
    checks the memory limit, and optionally saves a log file.
    
    Args:
        training_func: The training function to profile.
        *args: Positional arguments to pass to the training function.
        output_path: Path to save the memory profile log. If None, no log is saved.
        **kwargs: Keyword arguments to pass to the training function.
        
    Returns:
        The result of the training function.
        
    Raises:
        MemoryError: If peak memory usage exceeds the limit.
    """
    start_profiling()
    try:
        # Force GC before starting
        force_gc()
        
        # Run the training function
        result = training_func(*args, **kwargs)
        
        # Stop profiling
        current, peak = stop_profiling()
        peak_mb = peak / 1024 / 1024
        
        # Check memory limit
        if not check_memory_limit(peak_mb):
            raise MemoryError(
                f"Peak memory usage {peak_mb:.2f} MB exceeds limit of {MAX_MEMORY_GB} GB"
            )
        
        # Save log if path provided
        if output_path:
            save_memory_profile_log(
                current_mb=current / 1024 / 1024,
                peak_mb=peak_mb,
                output_path=output_path
            )
        
        return result
        
    except Exception as e:
        # Ensure profiling is stopped even on error
        if tracemalloc.is_tracing():
            stop_profiling()
        raise e


def save_memory_profile_log(
    current_mb: float,
    peak_mb: float,
    output_path: Path,
    extra_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save the memory profile log to a file.
    
    Args:
        current_mb: Current memory usage in MB.
        peak_mb: Peak memory usage in MB.
        output_path: Path to save the log file.
        extra_info: Optional dictionary of extra information to include in the log.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    log_lines = [
        f"Memory Profile Log",
        f"==================",
        f"Timestamp: {Path(output_path).parent.parent.parent.name if output_path else 'N/A'}", # Placeholder for actual timestamp logic if needed, but using file creation time is better.
        f"Current Memory: {current_mb:.2f} MB",
        f"Peak Memory: {peak_mb:.2f} MB",
        f"Memory Limit: {MAX_MEMORY_GB} GB ({MAX_MEMORY_MB:.2f} MB)",
        f"Status: {'PASS' if peak_mb <= MAX_MEMORY_MB else 'FAIL'}",
    ]
    
    if extra_info:
        log_lines.append(f"\nExtra Information:")
        for key, value in extra_info.items():
            log_lines.append(f"  {key}: {value}")
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(log_lines))
    
    logger.info(f"Memory profile log saved to {output_path}")


def main():
    """
    Main entry point for standalone execution.
    
    This function demonstrates the usage of the memory profiler by running
    a dummy training simulation and generating a memory profile log.
    """
    import time
    import numpy as np
    
    # Define output path
    output_path = Path("data/results/memory_profile.log")
    
    def dummy_training():
        """Simulate a training process that uses memory."""
        logger.info("Starting dummy training simulation...")
        # Allocate some memory
        data = np.random.rand(100000, 100) # ~80 MB
        time.sleep(2) # Simulate work
        del data
        force_gc()
        logger.info("Dummy training simulation completed.")
        return {"status": "success"}
    
    try:
        result = profile_training_block(
            dummy_training,
            output_path=output_path
        )
        logger.info(f"Training result: {result}")
    except MemoryError as e:
        logger.error(f"Memory limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
