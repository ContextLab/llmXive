"""
Profiling utilities for the pipeline.

Provides functions to measure execution time and memory usage.
"""
import os
import time
import resource
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any

class PipelineProfiler:
    """Profiler class to track pipeline execution metrics."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory: int = 0
        self.stages: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def start(self):
        """Start the profiler."""
        self.start_time = time.time()
        # Reset peak memory tracking
        resource.setrlimit(resource.RLIMIT_AS, resource.getrlimit(resource.RLIMIT_AS))
    
    def stop(self):
        """Stop the profiler and record final metrics."""
        self.end_time = time.time()
        # Get peak memory usage
        usage = resource.getrusage(resource.RUSAGE_SELF)
        self.peak_memory = usage.ru_maxrss  # in KB on Linux/macOS
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get the collected metrics."""
        return {
            "total_execution_time": (self.end_time - self.start_time) if self.end_time and self.start_time else 0,
            "peak_memory_kb": self.peak_memory,
            "stages": self.stages
        }
    
    def record_stage(self, stage_name: str, duration: float, memory_kb: int):
        """Record metrics for a specific stage."""
        with self._lock:
            self.stages[stage_name] = {
                "duration_seconds": duration,
                "peak_memory_kb": memory_kb
            }

@contextmanager
def profile_stage(profiler: PipelineProfiler, stage_name: str):
    """Context manager to profile a specific stage."""
    start = time.time()
    profiler.start()
    try:
        yield
    finally:
        end = time.time()
        duration = end - start
        usage = resource.getrusage(resource.RUSAGE_SELF)
        memory_kb = usage.ru_maxrss
        profiler.record_stage(stage_name, duration, memory_kb)

def get_resource_limits():
    """Get current resource limits."""
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    return {
        "memory_soft_limit_kb": soft,
        "memory_hard_limit_kb": hard
    }

def main():
    """Main entry point for profiler (demo)."""
    print("Pipeline Profiler Module")
    print("Usage: from profiler import PipelineProfiler, profile_stage, get_resource_limits")
    print("Example:")
    print("  profiler = PipelineProfiler()")
    print("  profiler.start()")
    print("  # ... run pipeline stages ...")
    print("  profiler.stop()")
    print("  metrics = profiler.get_metrics()")

if __name__ == "__main__":
    main()
