"""
Performance optimization utilities for the mTBI study pipeline.

Provides functions for:
- Profiling code sections
- Optimizing memory usage
- Parallel processing configuration
- Runtime estimation
"""
import os
import sys
import time
import json
import logging
import cProfile
import pstats
import io
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
import multiprocessing
import resource

from config import get_config, get_memory_limit_gb, get_runtime_limit_hours
from memory_monitor import get_current_ram_gb, is_limit_exceeded
from time_monitor import get_elapsed_time_hours

logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """Context manager for profiling code sections."""
    
    def __init__(self, section_name: str, output_file: Optional[Path] = None):
        self.section_name = section_name
        self.output_file = output_file
        self.pr = None
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.pr = cProfile.Profile()
        self.pr.enable()
        logger.info(f"Profiling started: {self.section_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pr.disable()
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        # Get stats
        s = io.StringIO()
        stats = pstats.Stats(self.pr, stream=s).sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions
        
        logger.info(f"Profiling completed: {self.section_name} (duration: {duration:.2f}s)")
        logger.debug(s.getvalue())
        
        # Save to file if specified
        if self.output_file:
            with open(self.output_file, 'w') as f:
                f.write(f"Section: {self.section_name}\n")
                f.write(f"Duration: {duration:.2f}s\n")
                f.write(s.getvalue())
        
        return False

def profile_function(func: Callable) -> Callable:
    """Decorator to profile a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        with PerformanceProfiler(func_name):
            return func(*args, **kwargs)
    return wrapper

def estimate_runtime(num_subjects: int, avg_time_per_subject: float = 300.0) -> Dict[str, float]:
    """
    Estimate total runtime for processing multiple subjects.
    
    Args:
        num_subjects: Number of subjects to process
        avg_time_per_subject: Average time per subject in seconds
    
    Returns:
        Dictionary with runtime estimates
    """
    total_seconds = num_subjects * avg_time_per_subject
    total_hours = total_seconds / 3600
    
    return {
        'estimated_total_seconds': total_seconds,
        'estimated_total_hours': total_hours,
        'estimated_per_subject_seconds': avg_time_per_subject,
        'num_subjects': num_subjects,
        'within_limit': total_hours <= get_runtime_limit_hours()
    }

def optimize_memory_usage():
    """
    Apply memory optimization strategies.
    
    This function:
    1. Clears Python's internal memory cache
    2. Forces garbage collection
    3. Logs current memory state
    """
    import gc
    
    logger.info("Optimizing memory usage")
    current_ram = get_current_ram_gb()
    logger.info(f"Memory before optimization: {current_ram:.2f} GB")
    
    # Force garbage collection
    gc.collect()
    
    # Clear caches if available
    try:
        if hasattr(gc, 'garbage'):
            gc.garbage.clear()
    except Exception:
        pass
    
    # Try to release memory back to OS (Unix only)
    try:
        resource.setrlimit(resource.RLIMIT_AS, resource.getrlimit(resource.RLIMIT_AS))
    except Exception:
        pass
    
    current_ram = get_current_ram_gb()
    logger.info(f"Memory after optimization: {current_ram:.2f} GB")

def configure_parallel_processing(max_workers: Optional[int] = None) -> int:
    """
    Configure parallel processing settings.
    
    Args:
        max_workers: Maximum number of worker processes (None for auto-detect)
    
    Returns:
        Number of workers to use
    """
    if max_workers is None:
        # Auto-detect based on available cores and memory
        cpu_count = multiprocessing.cpu_count()
        memory_limit = get_memory_limit_gb()
        
        # Conservative estimate: 1 worker per 2GB RAM, max 75% of CPUs
        memory_based_workers = max(1, int(memory_limit / 2))
        cpu_based_workers = max(1, int(cpu_count * 0.75))
        
        max_workers = min(memory_based_workers, cpu_based_workers)
        logger.info(f"Auto-detected {max_workers} workers (CPU: {cpu_count}, RAM: {memory_limit}GB)")
    
    logger.info(f"Configured for {max_workers} parallel workers")
    return max_workers

def get_performance_summary() -> Dict[str, Any]:
    """
    Get current performance metrics summary.
    
    Returns:
        Dictionary with current performance state
    """
    return {
        'current_ram_gb': get_current_ram_gb(),
        'elapsed_hours': get_elapsed_time_hours(),
        'memory_limit_gb': get_memory_limit_gb(),
        'runtime_limit_hours': get_runtime_limit_hours(),
        'cpu_count': multiprocessing.cpu_count(),
        'config': get_config()
    }

def main():
    """Main entry point for performance optimization tools."""
    logger.info("Performance optimization module loaded")
    
    # Run self-test
    summary = get_performance_summary()
    logger.info(f"Performance summary: {json.dumps(summary, indent=2)}")
    
    # Estimate runtime for typical workload
    estimate = estimate_runtime(num_subjects=20, avg_time_per_subject=300)
    logger.info(f"Runtime estimate: {json.dumps(estimate, indent=2)}")

if __name__ == '__main__':
    main()
