from dataclasses import dataclass
from typing import Optional, Callable, Any, Tuple
from datetime import datetime
import time
import tracemalloc

@dataclass
class BenchmarkRun:
    """
    Data schema for a single benchmark run result.
    
    Fields:
        dataset_size: Number of elements inserted into the Bloom filter.
        fpr_target: Target False Positive Rate (e.g., 0.01, 0.001).
        implementation_type: String identifier for the implementation (e.g., 'array', 'vector', 'bitset').
        peak_memory_mb: Peak memory usage in megabytes during the run.
        query_latency_ms: Average latency per query in milliseconds.
        repetition_id: Unique identifier for this repetition of the benchmark configuration.
        query_count: Total number of queries executed.
        insert_time_ms: Total time taken to insert all elements (optional).
        false_positive_rate: Actual measured false positive rate (optional).
    """
    dataset_size: int
    fpr_target: float
    implementation_type: str
    peak_memory_mb: float
    query_latency_ms: float
    repetition_id: int
    query_count: int
    insert_time_ms: Optional[float] = None
    false_positive_rate: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert the dataclass instance to a dictionary for serialization."""
        return {
            "dataset_size": self.dataset_size,
            "fpr_target": self.fpr_target,
            "implementation_type": self.implementation_type,
            "peak_memory_mb": self.peak_memory_mb,
            "query_latency_ms": self.query_latency_ms,
            "repetition_id": self.repetition_id,
            "query_count": self.query_count,
            "insert_time_ms": self.insert_time_ms,
            "false_positive_rate": self.false_positive_rate
        }

def measure_memory(func: Callable[[], Any]) -> float:
    """
    Measure peak memory usage of a function in MB.
    
    Args:
        func: Function to measure memory usage for. Must be callable with no arguments.
    
    Returns:
        Peak memory usage in megabytes.
    
    Raises:
        RuntimeError: If tracemalloc fails to start or stop.
    """
    tracemalloc.start()
    try:
        func()
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)  # Convert bytes to MB
    finally:
        tracemalloc.stop()

def measure_latency(func: Callable[[], Any], iterations: int = 100) -> float:
    """
    Measure average latency of a function in milliseconds.
    
    Args:
        func: Function to measure latency for. Must be callable with no arguments.
        iterations: Number of iterations to average over.
    
    Returns:
        Average latency in milliseconds.
    """
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()
    
    total_time_ms = (end - start) * 1000
    return total_time_ms / iterations