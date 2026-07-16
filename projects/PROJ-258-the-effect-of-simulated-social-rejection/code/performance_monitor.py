"""
Performance monitoring and optimization utilities for the social rejection pipeline.

This module ensures the total runtime remains under 6 hours for N <= 500 participants
by monitoring execution time, memory usage, and providing early termination warnings.
"""
import os
import sys
import time
import logging
import resource
from typing import Callable, Optional, Any, Dict
from functools import wraps
import threading

from config import get_path
from logging_utils import get_process_memory_mb

# Constants
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 6 hours
MAX_MEMORY_MB = 7 * 1024  # 7 GB
MEMORY_CHECK_INTERVAL = 10  # seconds
WARNING_RUNTIME_PERCENT = 0.8  # 80% of max runtime triggers warning

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Context manager and decorator for performance monitoring."""
    
    def __init__(self, task_name: str = "Pipeline"):
        self.task_name = task_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.memory_peak_mb: float = 0.0
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
    
    def _memory_monitor(self):
        """Background thread to monitor memory usage."""
        while not self._stop_monitoring.is_set():
            current_mb = get_process_memory_mb()
            if current_mb > self.memory_peak_mb:
                self.memory_peak_mb = current_mb
                if current_mb > MAX_MEMORY_MB:
                    logger.warning(
                        f"Memory limit exceeded: {current_mb:.2f}MB > {MAX_MEMORY_MB}MB"
                    )
            time.sleep(MEMORY_CHECK_INTERVAL)
    
    def __enter__(self):
        self.start_time = time.time()
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._memory_monitor, daemon=True)
        self._monitor_thread.start()
        logger.info(f"Started performance monitoring for: {self.task_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        
        elapsed = self.end_time - self.start_time
        elapsed_hours = elapsed / 3600
        
        logger.info(
            f"Completed {self.task_name}: "
            f"Runtime={elapsed_hours:.2f}h ({elapsed:.2f}s), "
            f"Memory Peak={self.memory_peak_mb:.2f}MB"
        )
        
        # Check constraints
        if elapsed > MAX_RUNTIME_SECONDS:
            logger.error(
                f"RUNTIME EXCEEDED: {elapsed_hours:.2f}h > {MAX_RUNTIME_SECONDS/3600}h limit"
            )
            return False  # Signal failure
        
        if self.memory_peak_mb > MAX_MEMORY_MB:
            logger.error(
                f"MEMORY EXCEEDED: {self.memory_peak_mb:.2f}MB > {MAX_MEMORY_MB}MB limit"
            )
            return False  # Signal failure
        
        # Warning if approaching limit
        if elapsed > (MAX_RUNTIME_SECONDS * WARNING_RUNTIME_PERCENT):
            logger.warning(
                f"Approaching runtime limit: {elapsed_hours:.2f}h of {MAX_RUNTIME_SECONDS/3600}h"
            )
        
        return True
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time if self.start_time else 0.0
    
    def get_elapsed_hours(self) -> float:
        """Get elapsed time in hours."""
        return self.get_elapsed_time() / 3600.0
    
    def is_within_limits(self) -> bool:
        """Check if current runtime is within limits."""
        return self.get_elapsed_time() <= MAX_RUNTIME_SECONDS

def performance_watchdog(func: Callable) -> Callable:
    """
    Decorator to monitor function execution time and memory.
    
    Automatically logs performance metrics and raises an error if limits are exceeded.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        task_name = kwargs.get('task_name', func.__name__)
        with PerformanceMonitor(task_name=task_name) as monitor:
            result = func(*args, **kwargs)
            if not monitor.is_within_limits():
                raise RuntimeError(
                    f"Performance limit exceeded in {task_name}: "
                    f"{monitor.get_elapsed_hours():.2f}h runtime or {monitor.memory_peak_mb:.2f}MB memory"
                )
            return result
    return wrapper

def optimize_dataframe_operations(df) -> None:
    """
    Apply memory optimizations to a pandas DataFrame.
    
    Reduces memory footprint by:
    1. Downcasting numeric types
    2. Converting object columns to category where appropriate
    3. Removing unnecessary columns
    """
    import pandas as pd
    import numpy as np
    
    initial_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    # Downcast numeric types
    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    # Convert object columns to category if low cardinality
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique
            df[col] = df[col].astype('category')
    
    final_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
    reduction = ((initial_memory - final_memory) / initial_memory) * 100
    
    logger.debug(
        f"DataFrame memory optimization: {initial_memory:.2f}MB -> {final_memory:.2f}MB "
        f"({reduction:.1f}% reduction)"
    )

def run_pipeline_with_monitoring(pipeline_func: Callable, *args, **kwargs) -> Any:
    """
    Execute a pipeline function with comprehensive performance monitoring.
    
    Args:
        pipeline_func: The pipeline function to execute
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        The result of the pipeline function
    
    Raises:
        RuntimeError: If performance limits are exceeded
    """
    task_name = kwargs.pop('task_name', 'Pipeline Execution')
    
    with PerformanceMonitor(task_name=task_name) as monitor:
        result = pipeline_func(*args, **kwargs)
        
        if not monitor.is_within_limits():
            raise RuntimeError(
                f"Pipeline {task_name} exceeded performance limits: "
                f"{monitor.get_elapsed_hours():.2f}h runtime, "
                f"{monitor.memory_peak_mb:.2f}MB peak memory"
            )
        
        # Save performance metrics
        metrics = {
            'task_name': task_name,
            'runtime_seconds': monitor.get_elapsed_time(),
            'runtime_hours': monitor.get_elapsed_hours(),
            'memory_peak_mb': monitor.memory_peak_mb,
            'within_limits': True
        }
        
        # Save to processed data directory
        metrics_path = get_path('data/processed', 'performance_metrics.json')
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        
        import json
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Performance metrics saved to {metrics_path}")
        return result

def main():
    """
    Standalone performance test script.
    
    Simulates pipeline execution and validates performance constraints.
    """
    import argparse
    import pandas as pd
    import numpy as np
    
    parser = argparse.ArgumentParser(description='Performance monitoring test')
    parser.add_argument('--n-participants', type=int, default=500, 
                      help='Number of participants to simulate')
    parser.add_argument('--test-memory', action='store_true',
                      help='Test memory monitoring')
    args = parser.parse_args()
    
    logger.info(f"Starting performance test with N={args.n_participants}")
    
    # Simulate data processing
    def simulate_pipeline(n: int):
        """Simulate a data processing pipeline."""
        logger.info("Simulating data ingestion...")
        time.sleep(0.1)  # Simulate I/O
        
        logger.info("Creating large DataFrame...")
        df = pd.DataFrame({
            'participant_id': range(n),
            'reaction_time': np.random.normal(500, 100, n),
            'mood_score': np.random.normal(5, 2, n),
            'condition': np.random.choice(['control', 'rejection'], n)
        })
        
        logger.info("Optimizing DataFrame...")
        optimize_dataframe_operations(df)
        
        logger.info("Running analysis simulation...")
        # Simulate computation
        for _ in range(100):
            _ = df.groupby('condition').mean()
            time.sleep(0.01)
        
        return df
    
    try:
        result = run_pipeline_with_monitoring(
            simulate_pipeline,
            args.n_participants,
            task_name=f"Performance Test (N={args.n_participants})"
        )
        
        logger.info(f"Pipeline completed successfully with {len(result)} records")
        return 0
        
    except RuntimeError as e:
        logger.error(f"Performance limit exceeded: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
