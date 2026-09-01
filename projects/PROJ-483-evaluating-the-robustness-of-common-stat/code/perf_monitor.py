"""
Performance monitoring utilities for the llmXive automated science pipeline.
Implements FR-008: Log execution time and memory usage to results/perf_log.json.
"""
import os
import json
import time
import tracemalloc
import platform
import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import load_config

def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the Python process in MB.
    
    Returns:
        float: Memory usage in megabytes.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / (1024 * 1024)

def log_performance_metrics(
    task_id: str,
    start_time: float,
    end_time: float,
    output_path: Optional[str] = None,
    additional_metrics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate and log performance metrics to results/perf_log.json.
    
    Args:
        task_id: Identifier for the task being monitored.
        start_time: Start timestamp (from time.time()).
        end_time: End timestamp (from time.time()).
        output_path: Optional custom path for the log file. Defaults to results/perf_log.json.
        additional_metrics: Optional dict of extra metrics to include.
    
    Returns:
        Dict containing the logged metrics.
    """
    # Calculate elapsed time
    elapsed_seconds = end_time - start_time
    
    # Get memory usage
    memory_mb = get_memory_usage_mb()
    
    # Get peak memory if tracemalloc was used
    peak_memory_mb = None
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        peak_memory_mb = peak / (1024 * 1024)
    
    # Build metrics dictionary
    metrics = {
        "task_id": task_id,
        "timestamp": datetime.utcnow().isoformat(),
        "execution_time_seconds": elapsed_seconds,
        "memory_usage_mb": memory_mb,
        "peak_memory_mb": peak_memory_mb,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "config": {
            "random_seed": load_config().get("random_seed", "not_set")
        }
    }
    
    # Add additional metrics if provided
    if additional_metrics:
        metrics.update(additional_metrics)
    
    # Determine output path
    if output_path is None:
        output_path = "results/perf_log.json"
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing logs if file exists
    existing_logs = []
    if output_path_obj.exists():
        try:
            with open(output_path_obj, 'r') as f:
                existing_logs = json.load(f)
                if not isinstance(existing_logs, list):
                    existing_logs = [existing_logs]
        except (json.JSONDecodeError, IOError):
            existing_logs = []
    
    # Append new metrics
    existing_logs.append(metrics)
    
    # Write back to file
    with open(output_path_obj, 'w') as f:
        json.dump(existing_logs, f, indent=2)
    
    return metrics

def measure_execution(
    task_id: str,
    func,
    *args,
    output_path: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Decorator-like function to measure execution time and memory of a function.
    
    Args:
        task_id: Identifier for the task being monitored.
        func: Function to execute.
        *args: Positional arguments for the function.
        output_path: Optional custom path for the log file.
        **kwargs: Keyword arguments for the function.
    
    Returns:
        The return value of the executed function.
    """
    # Start memory tracing
    tracemalloc.start()
    start_time = time.time()
    
    try:
        # Execute the function
        result = func(*args, **kwargs)
    finally:
        end_time = time.time()
        # Stop memory tracing
        tracemalloc.stop()
    
    # Log the metrics
    log_performance_metrics(
        task_id=task_id,
        start_time=start_time,
        end_time=end_time,
        output_path=output_path
    )
    
    return result

def main():
    """
    Standalone test to verify performance logging functionality.
    """
    print("Testing performance monitoring...")
    
    # Simulate some work
    start = time.time()
    tracemalloc.start()
    
    # Create some data to use memory
    data = [i ** 2 for i in range(1000000)]
    _ = sum(data)
    
    end = time.time()
    tracemalloc.stop()
    
    # Log the metrics
    metrics = log_performance_metrics(
        task_id="T032b_test",
        start_time=start,
        end_time=end,
        additional_metrics={
            "test_description": "Performance monitoring verification"
        }
    )
    
    print(f"Execution time: {metrics['execution_time_seconds']:.4f} seconds")
    print(f"Memory usage: {metrics['memory_usage_mb']:.2f} MB")
    if metrics.get('peak_memory_mb'):
        print(f"Peak memory: {metrics['peak_memory_mb']:.2f} MB")
    print(f"Metrics logged to: results/perf_log.json")
    
    # Verify file exists
    if Path("results/perf_log.json").exists():
        print("SUCCESS: Performance log file created.")
    else:
        print("ERROR: Performance log file not created.")

if __name__ == "__main__":
    main()
