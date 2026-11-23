"""
Memory Profiling Utilities for llmXive DanceOPD Extension.

Provides functions to monitor and report memory usage during data streaming
operations to ensure peak memory stays below 6GB.
"""
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import tracemalloc

def get_memory_usage_mb() -> float:
    """
    Get current memory usage in megabytes.
    
    Returns:
        Current memory usage in MB
    """
    try:
        # Try to get memory from /proc on Linux
        if sys.platform.startswith("linux"):
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        # VmRSS is in kB
                        return float(line.split()[1]) / 1024.0
        
        # Fallback to tracemalloc if available
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            return current / 1024.0 / 1024.0
        
        return 0.0
        
    except Exception:
        return 0.0

def profile_function(
    func: Callable,
    *args,
    max_memory_mb: float = 6000.0,
    interval_seconds: float = 1.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Profile a function's memory usage.
    
    Args:
        func: Function to profile
        *args: Positional arguments for the function
        max_memory_mb: Maximum allowed memory in MB (default: 6000.0)
        interval_seconds: Memory check interval in seconds
        **kwargs: Keyword arguments for the function
        
    Returns:
        Dictionary with profiling results
    """
    results = {
        "start_memory_mb": 0.0,
        "peak_memory_mb": 0.0,
        "end_memory_mb": 0.0,
        "exceeded_max": False,
        "memory_samples": [],
        "duration_seconds": 0.0
    }
    
    tracemalloc.start()
    
    results["start_memory_mb"] = get_memory_usage_mb()
    start_time = time.time()
    
    try:
        # Start memory monitoring thread
        def monitor_memory():
            while True:
                current_mem = get_memory_usage_mb()
                results["memory_samples"].append({
                    "time": time.time() - start_time,
                    "memory_mb": current_mem
                })
                
                if current_mem > results["peak_memory_mb"]:
                    results["peak_memory_mb"] = current_mem
                
                if current_mem > max_memory_mb:
                    results["exceeded_max"] = True
                
                time.sleep(interval_seconds)
        
        import threading
        monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        monitor_thread.start()
        
        # Execute the function
        result = func(*args, **kwargs)
        
        # Wait for thread to finish (with timeout)
        monitor_thread.join(timeout=5.0)
        
        results["end_memory_mb"] = get_memory_usage_mb()
        results["duration_seconds"] = time.time() - start_time
        
    except Exception as e:
        results["error"] = str(e)
        results["exceeded_max"] = True
        
    finally:
        tracemalloc.stop()
    
    return results

def save_memory_profile(
    results: Dict[str, Any],
    output_path: Path
):
    """
    Save memory profiling results to a JSON file.
    
    Args:
        results: Profiling results dictionary
        output_path: Path to output JSON file
    """
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

def main():
    """Example usage of memory profiler."""
    print("Memory Profiler Utility")
    print(f"Current memory usage: {get_memory_usage_mb():.2f} MB")
    
    # Example: profile a simple function
    def sample_function():
        time.sleep(2)
        data = [i for i in range(1000000)]
        time.sleep(1)
        return len(data)
    
    profile_results = profile_function(
        sample_function,
        max_memory_mb=6000.0,
        interval_seconds=0.5
    )
    
    print(f"Sample function results:")
    print(f"  Start memory: {profile_results['start_memory_mb']:.2f} MB")
    print(f"  Peak memory: {profile_results['peak_memory_mb']:.2f} MB")
    print(f"  End memory: {profile_results['end_memory_mb']:.2f} MB")
    print(f"  Duration: {profile_results['duration_seconds']:.2f} seconds")
    print(f"  Exceeded max: {profile_results['exceeded_max']}")

if __name__ == "__main__":
    main()