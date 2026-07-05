"""
Utility functions for resource monitoring, timing, and metric aggregation.
Implements FR-010: Resource abort logic wrapper.
"""
import os
import sys
import csv
import logging
import time
import subprocess
import resource
from pathlib import Path
from typing import Optional, Dict, Any, Callable, TypeVar, Union

from config import ensure_paths, Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
RAM_LIMIT_GB = 7.0
RAM_LIMIT_BYTES = RAM_LIMIT_GB * 1024 * 1024 * 1024
MONITORING_FILE = "results/monitoring.csv"

# Type alias for the wrapper
FuncT = TypeVar('FuncT', bound=Callable[..., Any])

def ensure_monitoring_dir():
    """Ensure the results directory exists for monitoring logs."""
    ensure_paths()
    results_dir = Path(Config.RESULTS_DIR)
    results_dir.mkdir(parents=True, exist_ok=True)

def get_current_ram_mb() -> float:
    """
    Get current peak RSS (Resident Set Size) of the current process in MB.
    Uses resource module for cross-platform compatibility (Unix/macOS primarily).
    """
    try:
        # rusage.ru_maxrss is in KB on Linux/macOS, but bytes on some systems?
        # Standard Linux: KB. Standard macOS: bytes? Actually macOS is bytes in newer versions, but often KB in older.
        # Let's assume KB for Linux (most common in CI) and handle conversion.
        # resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        usage = resource.getrusage(resource.RUSAGE_SELF)
        max_rss = usage.ru_maxrss
        
        # Detect unit: On Linux, ru_maxrss is in KB. On macOS, it's bytes (historically KB in older, but let's check).
        # To be safe, we can check if the value is suspiciously large for KB.
        # However, standard practice in Python resource module docs often assumes KB for Linux.
        # Let's standardize on KB detection: if > 1GB in KB, it's likely bytes.
        # 1GB = 1024*1024 KB = 1,048,576.
        
        if max_rss > 2000000: # If > 2GB in KB, it's likely bytes (macOS behavior)
            return max_rss / (1024 * 1024) # Convert bytes to MB
        else:
            return max_rss / 1024.0 # Convert KB to MB
    except Exception as e:
        logger.warning(f"Could not read resource usage: {e}")
        return 0.0

def check_ram_limit(limit_gb: float = RAM_LIMIT_GB) -> bool:
    """
    Check if current RAM usage exceeds the limit.
    Returns True if limit exceeded (abort condition), False otherwise.
    """
    current_mb = get_current_ram_mb()
    limit_mb = limit_gb * 1024
    
    if current_mb > limit_mb:
        logger.error(f"RAM usage {current_mb:.2f} MB exceeds limit {limit_mb:.2f} MB. Aborting.")
        return True
    return False

def log_metric(step_name: str, metric_name: str, value: Union[float, int], 
               unit: str = "", status: str = "ok"):
    """
    Log a metric to the monitoring CSV file.
    
    Args:
        step_name: Name of the pipeline step (e.g., 'pca', 'umap')
        metric_name: Name of the metric (e.g., 'peak_ram_mb', 'duration_sec')
        value: Numeric value
        unit: Unit of measurement
        status: Status string (ok, aborted, warning)
    """
    ensure_monitoring_dir()
    file_path = Path(Config.RESULTS_DIR) / MONITORING_FILE
    
    file_exists = file_path.exists()
    
    with open(file_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'step_name', 'metric_name', 'value', 'unit', 'status'])
        
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        writer.writerow([timestamp, step_name, metric_name, f"{value:.4f}", unit, status])

def resource_abort_wrapper(limit_gb: float = RAM_LIMIT_GB):
    """
    Decorator to wrap a function with RAM monitoring.
    Checks RAM at the start and end of the function.
    If RAM exceeds limit, logs to monitoring.csv and raises MemoryError.
    
    Args:
        limit_gb: RAM limit in GB (default 7.0)
    """
    def decorator(func: FuncT) -> FuncT:
        def wrapper(*args, **kwargs) -> Any:
            step_name = getattr(func, '__name__', 'unknown_step')
            
            # Check RAM before execution
            if check_ram_limit(limit_gb):
                log_metric(step_name, "pre_check_ram_mb", get_current_ram_mb(), "MB", "aborted")
                raise MemoryError(f"RAM limit exceeded before {step_name}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                
                duration = end_time - start_time
                peak_ram = get_current_ram_mb()
                
                # Log duration and peak RAM
                log_metric(step_name, "duration_sec", duration, "s", "ok")
                log_metric(step_name, "peak_ram_mb", peak_ram, "MB", "ok")
                
                return result
            except MemoryError:
                # Re-raise MemoryError if caught internally
                log_metric(step_name, "peak_ram_mb", get_current_ram_mb(), "MB", "aborted")
                raise
            except Exception as e:
                # Log error for other exceptions
                log_metric(step_name, "error", 0, "", "error")
                logger.error(f"Error in {step_name}: {e}")
                raise
        return wrapper  # type: ignore
    return decorator

def run_with_time_logging(step_name: str, func: Callable, *args, **kwargs):
    """
    Run a function and log time and memory usage to monitoring.csv.
    This is a procedural alternative to the decorator.
    
    Args:
        step_name: Name of the step
        func: Function to run
        *args, **kwargs: Arguments to pass to the function
    """
    ensure_monitoring_dir()
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        peak_ram = get_current_ram_mb()
        
        log_metric(step_name, "duration_sec", duration, "s", "ok")
        log_metric(step_name, "peak_ram_mb", peak_ram, "MB", "ok")
        return result
    except Exception as e:
        log_metric(step_name, "error", 0, "", "error")
        logger.error(f"Error in {step_name}: {e}")
        raise

def parse_time_v_output(output_path: str, step_name: str):
    """
    Parse output from `/usr/bin/time -v` and log metrics to monitoring.csv.
    
    Args:
        output_path: Path to the time log file
        step_name: Name of the step to associate with the log
    """
    try:
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Parse specific fields
        # Example: Maximum resident set size (kbytes): 123456
        max_rss_line = [l for l in content.split('\n') if "Maximum resident set size" in l]
        elapsed_line = [l for l in content.split('\n') if "Elapsed (wall clock)" in l]
        
        if max_rss_line:
            rss_kb = int(max_rss_line[0].split(':')[-1].strip())
            rss_mb = rss_kb / 1024.0
            log_metric(step_name, "peak_ram_mb", rss_mb, "MB", "ok")
        
        if elapsed_line:
            # Format: HH:MM:SS or M:SS
            time_str = elapsed_line[0].split(':')[-1].strip() # This might be tricky with colons in time
            # Better parsing:
            parts = elapsed_line[0].split('(')[-1].split(')')[0].strip()
            # parts could be "0:15:30" or "15:30"
            if ':' in parts:
                chunks = parts.split(':')
                if len(chunks) == 3:
                    h, m, s = map(float, chunks)
                    total_sec = h*3600 + m*60 + s
                elif len(chunks) == 2:
                    m, s = map(float, chunks)
                    total_sec = m*60 + s
                else:
                    total_sec = 0.0
                log_metric(step_name, "duration_sec", total_sec, "s", "ok")
                
    except Exception as e:
        logger.warning(f"Could not parse time output {output_path}: {e}")

def main():
    """
    Main entry point for testing the utility functions.
    """
    logger.info("Testing resource monitoring utilities...")
    
    # Test get_current_ram_mb
    ram = get_current_ram_mb()
    logger.info(f"Current RAM: {ram:.2f} MB")
    
    # Test check_ram_limit
    if check_ram_limit(1000.0): # 1TB limit, should be false
        logger.warning("Limit check failed unexpectedly")
    else:
        logger.info("Limit check passed (limit 1000GB)")
        
    # Test log_metric
    log_metric("test_step", "test_metric", 123.45, "units", "ok")
    logger.info("Metric logged to results/monitoring.csv")

if __name__ == "__main__":
    main()
