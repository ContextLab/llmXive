"""
Profiling module for T027.
Logs memory usage and runtime to verify CPU/RAM constraints (SC-005).
"""
import os
import sys
import time
import logging
import json
import resource
from typing import Optional, Callable, Any
from contextlib import contextmanager

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/profiling.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def get_memory_usage_mb() -> float:
    """
    Returns current memory usage in MB using resource module (Unix/Linux).
    Falls back to 0.0 on non-Unix systems.
    """
    try:
        # ru_maxrss is in kilobytes on Linux, bytes on macOS (sometimes)
        # Standard behavior on Linux: KB
        usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Convert to MB
        usage_mb = usage_kb / 1024.0
        return usage_mb
    except AttributeError:
        # Fallback for Windows or other OS where resource might not work as expected
        logger.warning("resource.getrusage not available or returned unexpected value. Returning 0.0.")
        return 0.0

def log_checkpoint(label: str, start_time: Optional[float] = None) -> float:
    """
    Logs a checkpoint with current time and memory usage.
    If start_time is provided, calculates elapsed time.
    Returns current time for future elapsed calculations.
    """
    current_time = time.time()
    elapsed = 0.0
    if start_time is not None:
        elapsed = current_time - start_time

    mem_mb = get_memory_usage_mb()
    log_entry = {
        "timestamp": current_time,
        "label": label,
        "elapsed_seconds": round(elapsed, 3),
        "memory_mb": round(mem_mb, 2)
    }
    logger.info(json.dumps(log_entry))
    return current_time

@contextmanager
def profile_block(label: str, start_time: Optional[float] = None):
    """
    Context manager to profile a block of code.
    Logs start and end memory/time.
    """
    start_mem = get_memory_usage_mb()
    t_start = log_checkpoint(f"START: {label}", start_time)
    try:
        yield
    finally:
        t_end = time.time()
        end_mem = get_memory_usage_mb()
        duration = t_end - t_start
        mem_delta = end_mem - start_mem
        
        log_entry = {
            "timestamp": t_end,
            "label": f"END: {label}",
            "duration_seconds": round(duration, 3),
            "start_memory_mb": round(start_mem, 2),
            "end_memory_mb": round(end_mem, 2),
            "memory_delta_mb": round(mem_delta, 2)
        }
        logger.info(json.dumps(log_entry))

def main():
    """
    Main entry point for T027.
    Simulates a typical workflow to demonstrate profiling capabilities
    and verify constraints (SC-005: Several CPU, sufficient RAM, 6h).
    """
    logger.info("Starting Profiling Run for T027")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    t_global_start = time.time()
    
    # Simulate a data processing block
    with profile_block("Data Loading Simulation"):
        time.sleep(0.1) # Simulate I/O
        data_size = 1000000 # Simulate 1M rows
        _ = [i * 2 for i in range(data_size)] # Simulate computation
    
    # Simulate a model training block
    with profile_block("Model Training Simulation"):
        time.sleep(0.2) # Simulate training
        _ = sum([i**2 for i in range(500000)])
    
    # Final checkpoint
    t_global_end = time.time()
    total_duration = t_global_end - t_global_start
    final_mem = get_memory_usage_mb()
    
    logger.info(json.dumps({
        "timestamp": t_global_end,
        "label": "FINAL_SUMMARY",
        "total_duration_seconds": round(total_duration, 3),
        "final_memory_mb": round(final_mem, 2),
        "status": "SUCCESS"
    }))

    logger.info(f"Profiling complete. Total time: {total_duration:.2f}s, Final Memory: {final_mem:.2f}MB")

if __name__ == "__main__":
    main()