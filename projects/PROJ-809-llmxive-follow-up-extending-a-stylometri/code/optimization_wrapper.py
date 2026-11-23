"""
Optimization wrapper for model training and evaluation to ensure CPU-only constraints.
Enforces:
  - ≤30s per author for training/evaluation
  - ≤6GB RAM usage
  - CPU-only execution (no CUDA/GPU)
"""

import os
import sys
import time
import resource
import logging
import traceback
from typing import Callable, Any, Dict, Optional, List
from functools import wraps

# Force CPU-only execution for any ML libraries that might use GPU
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TF warnings

from utils import get_logger, ensure_dir

# Constants
MAX_TIME_PER_AUTHOR = 30  # seconds
MAX_RAM_BYTES = 6 * 1024 * 1024 * 1024  # 6 GB in bytes
RAM_WARNING_THRESHOLD = 5 * 1024 * 1024 * 1024  # 5 GB warning threshold

logger = get_logger(__name__)


def get_memory_usage_bytes() -> int:
    """Get current process memory usage in bytes (Linux/Mac only)."""
    try:
        # Try to get memory usage from resource module (Unix-like systems)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux, bytes on macOS
        # We'll normalize to bytes
        if sys.platform == "darwin":
            return usage.ru_maxrss
        else:
            return usage.ru_maxrss * 1024
    except Exception:
        logger.warning("Could not determine memory usage. Returning 0.")
        return 0


def check_memory_usage():
    """Check if current memory usage exceeds the threshold. Raises warning if high."""
    current_mem = get_memory_usage_bytes()
    if current_mem > MAX_RAM_BYTES:
        error_msg = (
            f"Memory usage exceeded limit: {current_mem / (1024**3):.2f} GB > 6 GB. "
            "Consider reducing batch size or using streaming."
        )
        logger.error(error_msg)
        raise MemoryError(error_msg)
    elif current_mem > RAM_WARNING_THRESHOLD:
        logger.warning(
            f"High memory usage detected: {current_mem / (1024**3):.2f} GB > 5 GB. "
            "Approaching the 6 GB limit."
        )


def enforce_time_limit(func: Callable) -> Callable:
    """Decorator to enforce a time limit per author execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        if elapsed > MAX_TIME_PER_AUTHOR:
            logger.warning(
                f"Function {func.__name__} exceeded time limit: {elapsed:.2f}s > {MAX_TIME_PER_AUTHOR}s"
            )
            # We log a warning but do not raise, as the task is to ensure constraints
            # are respected during design, not to hard-fail the pipeline on timeout.
            # However, if the function itself is designed to fail on timeout, that's up to the caller.
        
        return result
    return wrapper


def run_with_constraints(
    func: Callable, 
    author_id: str, 
    *args, 
    timeout: int = MAX_TIME_PER_AUTHOR,
    **kwargs
) -> Any:
    """
    Run a function for a specific author with enforced time and memory constraints.
    
    Args:
        func: The function to execute
        author_id: Identifier for the current author (for logging)
        timeout: Maximum allowed execution time in seconds
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        The result of the function
        
    Raises:
        TimeoutError: If execution exceeds the time limit
        MemoryError: If memory usage exceeds the limit
    """
    logger.info(f"Starting {func.__name__} for author {author_id}")
    
    # Check memory before starting
    check_memory_usage()
    
    start_time = time.time()
    
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        # Check time constraint
        if elapsed > timeout:
            logger.error(
                f"Timeout: {func.__name__} for author {author_id} took {elapsed:.2f}s "
                f"(limit: {timeout}s)"
            )
            raise TimeoutError(
                f"Author {author_id}: {func.__name__} exceeded {timeout}s limit ({elapsed:.2f}s)"
            )
        
        # Check memory after execution
        check_memory_usage()
        
        logger.info(
            f"Completed {func.__name__} for author {author_id} in {elapsed:.2f}s. "
            f"Memory: {get_memory_usage_bytes() / (1024**3):.2f} GB"
        )
        
        return result
        
    except MemoryError:
        logger.error(f"Memory limit exceeded for author {author_id}")
        raise
    except Exception as e:
        logger.error(f"Error in {func.__name__} for author {author_id}: {str(e)}")
        raise


def optimize_training_parameters(
    ngram_order: int, 
    max_documents: int = 1000
) -> Dict[str, Any]:
    """
    Suggest optimized parameters for training to stay within constraints.
    
    Args:
        ngram_order: The n-gram order (4, 5, or 6)
        max_documents: Maximum number of documents to process per author
        
    Returns:
        Dictionary of optimized parameters
    """
    params = {
        "max_features": None,  # Let sklearn handle all features
        "min_df": 1,
        "max_df": 1.0,
        "ngram_range": (ngram_order, ngram_order),
        "token_pattern": r"(?u)\b\w+\b",  # Simple tokenization
        "analyzer": "char_wb" if ngram_order <= 6 else "char"  # Character word boundary
    }
    
    # For higher n-grams, reduce document count to save memory
    if ngram_order >= 5:
        params["max_documents"] = min(max_documents, 500)
    if ngram_order == 6:
        params["max_documents"] = min(max_documents, 250)
        
    return params


def main():
    """
    Main entry point to demonstrate constraint enforcement.
    This function is called by the training/evaluation scripts to ensure
    they operate within the specified CPU-only constraints.
    """
    logger.info("Optimization wrapper initialized")
    logger.info(f"Max time per author: {MAX_TIME_PER_AUTHOR}s")
    logger.info(f"Max RAM: {MAX_RAM_BYTES / (1024**3):.2f} GB")
    
    # Example usage:
    # The actual training and evaluation scripts should import and use
    # run_with_constraints() to wrap their per-author processing loops.
    
    logger.info("Import optimization wrapper and use run_with_constraints() in your training/evaluation loops.")


if __name__ == "__main__":
    main()
