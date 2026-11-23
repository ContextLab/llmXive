"""
Performance optimization utilities for the molecular halide binding affinity pipeline.

This module provides tools to enforce CPU-only execution, monitor RAM usage,
and optimize scikit-learn parameters for constrained environments.
"""
import os
import sys
import time
import tracemalloc
import logging
import threading
from typing import Optional, Callable, Any, Dict, Tuple
from functools import wraps

# Try to import psutil for accurate memory monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not installed. Memory monitoring will use fallback methods.")

logger = logging.getLogger(__name__)

# Constants
MAX_RAM_GB = 7.0
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
CPU_COUNT = os.cpu_count() or 1

def get_current_ram_gb() -> float:
    """
    Get current RAM usage in GB.
    
    Returns:
        Current RAM usage in GB.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    else:
        # Fallback: use resource module (Unix only) or estimate
        if sys.platform != 'win32':
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / (1024 * 1024)  # Convert KB to GB (approximate)
        return 0.0

def get_peak_ram_gb() -> float:
    """
    Get peak RAM usage in GB during this process lifetime.
    
    Returns:
        Peak RAM usage in GB.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        # Note: psutil doesn't track peak RSS directly, we track it manually
        return tracemalloc.get_traced_memory()[1] / (1024 ** 3) if tracemalloc.is_tracing() else 0.0
    else:
        if sys.platform != 'win32':
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / (1024 * 1024)  # Convert KB to GB
        return 0.0

def check_ram_constraint(current_gb: Optional[float] = None) -> Tuple[bool, str]:
    """
    Check if current RAM usage is within the 7GB constraint.
    
    Args:
        current_gb: Current RAM usage in GB. If None, measured automatically.
        
    Returns:
        Tuple of (is_within_limit, message)
    """
    if current_gb is None:
        current_gb = get_current_ram_gb()
    
    if current_gb > MAX_RAM_GB:
        return False, f"RAM usage {current_gb:.2f}GB exceeds limit of {MAX_RAM_GB}GB"
    return True, f"RAM usage {current_gb:.2f}GB is within limit"

def check_runtime_constraint(start_time: float) -> Tuple[bool, str]:
    """
    Check if runtime is within the 6-hour constraint.
    
    Args:
        start_time: Process start time (from time.time()).
        
    Returns:
        Tuple of (is_within_limit, message)
    """
    elapsed = time.time() - start_time
    if elapsed > MAX_RUNTIME_SECONDS:
        return False, f"Runtime {elapsed:.0f}s exceeds limit of {MAX_RUNTIME_SECONDS}s"
    return True, f"Runtime {elapsed:.0f}s is within limit"

def enforce_cpu_only(n_jobs: int = 1) -> int:
    """
    Enforce CPU-only execution by setting n_jobs to 1 for scikit-learn.
    
    Args:
        n_jobs: Requested number of jobs.
        
    Returns:
        Actual number of jobs to use (always 1 for CPU constraint).
    """
    if n_jobs != 1:
        logger.warning(f"n_jobs={n_jobs} overridden to 1 for CPU-only constraint")
    return 1

def monitor_resources(start_time: float, check_interval: float = 60.0) -> None:
    """
    Background thread to monitor RAM and runtime constraints.
    
    Args:
        start_time: Process start time.
        check_interval: How often to check constraints (seconds).
    """
    def monitor_loop():
        while True:
            # Check RAM
            current_ram = get_current_ram_gb()
            if current_ram > MAX_RAM_GB:
                logger.error(f"RAM limit exceeded: {current_ram:.2f}GB > {MAX_RAM_GB}GB")
                raise RuntimeError(f"RAM limit exceeded: {current_ram:.2f}GB > {MAX_RAM_GB}GB")
            
            # Check runtime
            elapsed = time.time() - start_time
            if elapsed > MAX_RUNTIME_SECONDS:
                logger.error(f"Runtime limit exceeded: {elapsed:.0f}s > {MAX_RUNTIME_SECONDS}s")
                raise RuntimeError(f"Runtime limit exceeded: {elapsed:.0f}s > {MAX_RUNTIME_SECONDS}s")
            
            time.sleep(check_interval)
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    logger.info(f"Resource monitor started (interval: {check_interval}s)")

def timeout_decorator(timeout_seconds: float):
    """
    Decorator to enforce a timeout on a function.
    
    Args:
        timeout_seconds: Maximum allowed execution time in seconds.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)
            
            if thread.is_alive():
                raise TimeoutError(f"Function {func.__name__} exceeded timeout of {timeout_seconds}s")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        return wrapper
    return decorator

def memory_limit_decorator(limit_gb: float):
    """
    Decorator to enforce a memory limit on a function.
    
    Args:
        limit_gb: Maximum allowed RAM usage in GB.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tracemalloc.start()
            try:
                result = func(*args, **kwargs)
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                if peak / (1024 ** 3) > limit_gb:
                    raise MemoryError(f"Memory limit exceeded: {peak / (1024 ** 3):.2f}GB > {limit_gb}GB")
                
                return result
            except Exception:
                tracemalloc.stop()
                raise
        return wrapper
    return decorator

def optimize_sklearn_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize scikit-learn parameters for constrained environments.
    
    Args:
        params: Original parameter dictionary.
        
    Returns:
        Optimized parameter dictionary.
    """
    optimized = params.copy()
    
    # Force single-threaded execution
    if 'n_jobs' in optimized:
        optimized['n_jobs'] = 1
    
    # Reduce complexity for Random Forest if not specified
    if 'n_estimators' in optimized and optimized['n_estimators'] > 100:
        logger.warning(f"Reducing n_estimators from {optimized['n_estimators']} to 100 for performance")
        optimized['n_estimators'] = 100
    
    # Reduce max_depth if not specified or too high
    if 'max_depth' not in optimized or optimized.get('max_depth', 20) > 20:
        logger.warning("Setting max_depth to 20 for performance")
        optimized['max_depth'] = 20
    
    return optimized

def validate_environment() -> Dict[str, Any]:
    """
    Validate the execution environment meets performance constraints.
    
    Returns:
        Dictionary with validation results.
    """
    return {
        'cpu_count': CPU_COUNT,
        'has_psutil': HAS_PSUTIL,
        'current_ram_gb': get_current_ram_gb(),
        'max_ram_gb': MAX_RAM_GB,
        'max_runtime_seconds': MAX_RUNTIME_SECONDS,
        'constraints_met': get_current_ram_gb() <= MAX_RAM_GB
    }
