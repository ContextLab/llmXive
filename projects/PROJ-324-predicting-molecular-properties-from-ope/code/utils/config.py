import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Performance Configuration Constants
# Determined via hyperparameter tuning constraints (max_depth <= 15)
# Set to 12 to balance model complexity and training time on 2-core runner
MAX_DEPTH = 12

# Memory constraint for joblib parallel backend (6GB)
MAX_MEMORY_GB = 6

# Open Babel subprocess timeout (5 minutes per molecule to ensure 6h total window)
OBABEL_TIMEOUT = 300

# Total pipeline timeout (6 hours)
TOTAL_TIMEOUT_HOURS = 6

# Joblib configuration
N_JOBS = -1

def get_runtime_config() -> Dict[str, Any]:
    """
    Get runtime configuration parameters.
    
    Returns:
        Dictionary of configuration values.
    """
    return {
        "MAX_DEPTH": MAX_DEPTH,
        "MAX_MEMORY_GB": MAX_MEMORY_GB,
        "OBABEL_TIMEOUT": OBABEL_TIMEOUT,
        "TOTAL_TIMEOUT_HOURS": TOTAL_TIMEOUT_HOURS,
        "N_JOBS": N_JOBS
    }

def check_obabel_timeout(start_time: float) -> bool:
    """
    Check if the elapsed time since start exceeds the per-molecule timeout.
    
    Args:
        start_time: Unix timestamp when the operation started.
        
    Returns:
        True if timeout occurred, False otherwise.
    """
    elapsed = time.time() - start_time
    return elapsed > OBABEL_TIMEOUT

def enforce_obabel_subprocess_timeout(
    command: str,
    timeout: int = None
) -> subprocess.CompletedProcess:
    """
    Run an obabel subprocess with a hard timeout.
    
    Args:
        command: Command to run.
        timeout: Timeout in seconds (defaults to OBABEL_TIMEOUT).
        
    Returns:
        Completed process result.
        
    Raises:
        subprocess.TimeoutExpired: If the command exceeds the timeout.
    """
    if timeout is None:
        timeout = OBABEL_TIMEOUT
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            timeout=timeout, 
            check=True,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.TimeoutExpired:
        logging.error(f"Open Babel subprocess timed out after {timeout}s: {command}")
        raise

def validate_runtime_environment() -> bool:
    """
    Validate that the runtime environment meets requirements.
    
    Returns:
        True if environment is valid, False otherwise.
    """
    # Check memory availability (basic check)
    try:
        import psutil
        available_mem = psutil.virtual_memory().available / (1024**3)
        if available_mem < MAX_MEMORY_GB:
            logging.warning(f"Available memory ({available_mem:.2f}GB) is below configured limit ({MAX_MEMORY_GB}GB)")
            return False
    except ImportError:
        logging.warning("psutil not available for memory check")
    
    # Check obabel availability
    try:
        result = subprocess.run(["obabel", "-h"], capture_output=True, timeout=10)
        if result.returncode != 0:
            logging.error("obabel command not found or failed")
            return False
    except FileNotFoundError:
        logging.error("obabel command not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        logging.error("obabel command check timed out")
        return False
        
    return True

def get_joblib_parallel_backend():
    """
    Configure joblib parallel backend with memory constraints.
    
    Returns:
        A context manager or configuration for parallel execution.
    """
    # Note: joblib's memory_limit is available in newer versions.
    # If not, we rely on OS-level OOM handling or manual chunking.
    try:
        from joblib import Parallel, delayed
        # Return a partial configuration or a factory function
        def parallel_factory(n_jobs=N_JOBS):
            return Parallel(n_jobs=n_jobs)
        return parallel_factory
    except ImportError:
        logging.error("joblib not installed. Install with: pip install joblib")
        return None