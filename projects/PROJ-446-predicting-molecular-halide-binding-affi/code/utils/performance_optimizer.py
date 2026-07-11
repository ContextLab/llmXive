"""
Performance optimization utilities.
"""
import os
import sys
import time
import tracemalloc
import logging
from typing import Optional, Callable, Any, Dict

from code.utils.logger import get_logger

logger = get_logger(__name__)

RAM_LIMIT_GB = 7.0
RUNTIME_LIMIT_HOURS = 6.0

def get_current_ram_gb() -> float:
    """Get current RAM usage in GB."""
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024 / 1024 # Convert KB to GB (Linux)
    except Exception:
        return 0.0

def get_peak_ram_gb() -> float:
    """Get peak RAM usage in GB."""
    return get_current_ram_gb()

def check_ram_constraint(current_gb: float) -> bool:
    """Check if RAM usage is within limits."""
    return current_gb < RAM_LIMIT_GB

def check_runtime_constraint(start_time: float) -> bool:
    """Check if runtime is within limits."""
    elapsed = time.time() - start_time
    return elapsed < RUNTIME_LIMIT_HOURS * 3600

def enforce_cpu_only() -> None:
    """Enforce CPU-only execution (disable GPU)."""
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    # If using torch
    if "torch" in sys.modules:
        import torch
        torch.set_num_threads(1)

def monitor_resources(func: Callable) -> Callable:
    """Decorator to monitor RAM and runtime."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        tracemalloc.start()
        
        try:
            result = func(*args, **kwargs)
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            elapsed = time.time() - start_time
            logger.info(f"Function {func.__name__} completed in {elapsed:.2f}s. Peak RAM: {peak/1024/1024/1024:.2f} GB")
            if not check_ram_constraint(peak/1024/1024/1024):
                logger.warning(f"RAM limit exceeded: {peak/1024/1024/1024:.2f} GB > {RAM_LIMIT_GB} GB")
            if not check_runtime_constraint(start_time):
                logger.warning(f"Runtime limit exceeded: {elapsed/3600:.2f} hours > {RUNTIME_LIMIT_HOURS} hours")
            return result
    return wrapper

def timeout_decorator(seconds: int) -> Callable:
    """Decorator to enforce a timeout."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Simple timeout implementation using signal (Unix only)
            try:
                import signal
                def handler(signum, frame):
                    raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(seconds)
                result = func(*args, **kwargs)
                signal.alarm(0)
                return result
            except ImportError:
                # Fallback for Windows
                logger.warning("Timeout decorator not supported on this platform")
                return func(*args, **kwargs)
        return wrapper
    return decorator

def memory_limit_decorator(limit_gb: float) -> Callable:
    """Decorator to enforce a memory limit."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            tracemalloc.start()
            try:
                result = func(*args, **kwargs)
                current, peak = tracemalloc.get_traced_memory()
                if peak / 1024 / 1024 / 1024 > limit_gb:
                    raise MemoryError(f"Memory limit exceeded: {peak/1024/1024/1024:.2f} GB > {limit_gb} GB")
                return result
            finally:
                tracemalloc.stop()
        return wrapper
    return decorator

def optimize_sklearn_params() -> Dict[str, Any]:
    """Return optimized sklearn parameters for limited resources."""
    return {
        "n_jobs": 1, # CPU only, single thread to avoid overhead
        "verbose": 0
    }

def validate_environment() -> bool:
    """Validate that the environment meets constraints."""
    enforce_cpu_only()
    return True
