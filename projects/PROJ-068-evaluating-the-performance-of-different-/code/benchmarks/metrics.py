from dataclasses import dataclass
from typing import Optional, Callable, Any, Tuple
from datetime import datetime
import time
import tracemalloc

@dataclass
class BenchmarkRun:
    dataset_size: int
    fpr: float
    implementation_type: str
    peak_memory_mb: float
    query_latency_ms: float
    repetition_id: int
    query_count: int
    insert_time_ms: Optional[float] = None
    false_positive_rate: Optional[float] = None

def measure_memory(func: Callable[[], Any]) -> float:
    """
    Measure peak memory usage of a function in MB.
    
    Args:
        func: Function to measure memory usage for
    
    Returns:
        Peak memory usage in megabytes
    """
    tracemalloc.start()
    try:
        func()
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)  # Convert to MB
    finally:
        tracemalloc.stop()

def measure_latency(func: Callable[[], Any], iterations: int = 100) -> float:
    """
    Measure average latency of a function in milliseconds.
    
    Args:
        func: Function to measure latency for
        iterations: Number of iterations to average over
    
    Returns:
        Average latency in milliseconds
    """
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()
    
    total_time_ms = (end - start) * 1000
    return total_time_ms / iterations
