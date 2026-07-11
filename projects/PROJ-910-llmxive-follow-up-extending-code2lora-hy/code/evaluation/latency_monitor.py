"""
Latency monitoring for inference evaluation.

Implements FR-004: Instrument the evaluation runner to measure inference latency
per task in milliseconds, saving results to data/results/latency.csv.
"""
import time
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

def measure_inference_latency(
    task_id: str,
    inference_func,
    *args,
    **kwargs
) -> float:
    """
    Measure the inference latency for a single task.
    
    Args:
        task_id: Unique identifier for the task
        inference_func: Callable that performs the inference
        *args, **kwargs: Arguments to pass to the inference function
        
    Returns:
        Latency in milliseconds
    """
    start_time = time.perf_counter()
    
    # Execute the inference
    try:
        result = inference_func(*args, **kwargs)
    except Exception as e:
        # Re-raise to let the caller handle errors
        raise e
    
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000  # Convert to milliseconds
    
    return latency_ms


def save_latency_results(
    results: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Save latency measurement results to a CSV file.
    
    Args:
        results: List of dicts with 'task_id' and 'latency_ms' keys
        output_path: Optional custom output path. Defaults to 
                    'data/results/latency.csv'
                    
    Returns:
        The path where results were saved
    """
    if output_path is None:
        output_path = "data/results/latency.csv"
    
    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['task_id', 'latency_ms']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow({
                'task_id': result['task_id'],
                'latency_ms': result['latency_ms']
            })
    
    return output_path


def collect_latency_stats(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute summary statistics from latency results.
    
    Args:
        results: List of dicts with 'task_id' and 'latency_ms' keys
                
    Returns:
        Dict with 'mean', 'median', 'min', 'max', 'std' latency in ms
    """
    if not results:
        return {
            'mean': 0.0,
            'median': 0.0,
            'min': 0.0,
            'max': 0.0,
            'std': 0.0,
            'count': 0
        }
    
    latencies = [r['latency_ms'] for r in results]
    n = len(latencies)
    
    mean_latency = sum(latencies) / n
    sorted_latencies = sorted(latencies)
    median_latency = sorted_latencies[n // 2] if n % 2 == 1 else (sorted_latencies[n // 2 - 1] + sorted_latencies[n // 2]) / 2
    min_latency = min(latencies)
    max_latency = max(latencies)
    
    # Calculate standard deviation
    if n > 1:
        variance = sum((x - mean_latency) ** 2 for x in latencies) / (n - 1)
        std_latency = variance ** 0.5
    else:
        std_latency = 0.0
    
    return {
        'mean': mean_latency,
        'median': median_latency,
        'min': min_latency,
        'max': max_latency,
        'std': std_latency,
        'count': n
    }
