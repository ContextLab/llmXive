import time
import json
import sys
import argparse
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

def evaluate_latency_pass_fail(average_latency_ms: float, threshold_ms: float) -> Dict[str, Any]:
    """
    Evaluate whether the average latency meets the threshold.
    
    Args:
        average_latency_ms: Average latency in milliseconds.
        threshold_ms: Threshold latency in milliseconds.
        
    Returns:
        Dictionary with status ("PASS" or "FAIL") and average_ms.
    """
    status = "PASS" if average_latency_ms <= threshold_ms else "FAIL"
    return {
        "status": status,
        "average_ms": average_latency_ms
    }

def calculate_moving_average_latency(latency_samples: List[float], window_size: int = 10) -> float:
    """
    Calculate the moving average of latency samples.
    
    Args:
        latency_samples: List of latency measurements in milliseconds.
        window_size: Number of recent samples to include in the moving average.
        
    Returns:
        The moving average latency in milliseconds. Returns 0.0 if no samples.
    """
    if not latency_samples:
        return 0.0
    
    # Take the most recent 'window_size' samples
    recent_samples = latency_samples[-window_size:]
    
    if not recent_samples:
        return 0.0
        
    return sum(recent_samples) / len(recent_samples)

def measure_inference_latency(
    func: Callable[[], Any],
    warmup_runs: int = 1,
    measurement_runs: int = 5
) -> Dict[str, float]:
    """
    Measure inference latency of a function.
    
    Args:
        func: The function to measure.
        warmup_runs: Number of warmup runs before measurement.
        measurement_runs: Number of runs to measure.
        
    Returns:
        Dictionary with average_latency_ms, min_latency_ms, max_latency_ms, and samples.
    """
    # Warmup
    for _ in range(warmup_runs):
        func()
    
    # Measurement
    latencies = []
    for _ in range(measurement_runs):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)
    
    if not latencies:
        return {
            "average_latency_ms": 0.0,
            "min_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "samples": []
        }
    
    return {
        "average_latency_ms": sum(latencies) / len(latencies),
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
        "samples": latencies
    }

def main():
    """
    Main function to demonstrate latency measurement and moving average calculation.
    This script can be used to test the latency metrics module.
    """
    parser = argparse.ArgumentParser(description="Latency Metrics Tool")
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=50.0, 
        help="Latency threshold in milliseconds"
    )
    parser.add_argument(
        "--window", 
        type=int, 
        default=10, 
        help="Window size for moving average"
    )
    args = parser.parse_args()
    
    # Simulate some latency measurements
    simulated_latencies = [45.2, 48.7, 52.1, 46.3, 49.8, 51.2, 47.5, 50.0, 48.9, 49.5]
    
    print(f"Simulated latency samples: {simulated_latencies}")
    
    # Calculate moving average
    moving_avg = calculate_moving_average_latency(simulated_latencies, args.window)
    print(f"Moving average (window={args.window}): {moving_avg:.2f} ms")
    
    # Evaluate pass/fail
    result = evaluate_latency_pass_fail(moving_avg, args.threshold)
    print(f"Evaluation result: {json.dumps(result, indent=2)}")
    
    # Test with empty list
    empty_avg = calculate_moving_average_latency([])
    print(f"Moving average for empty list: {empty_avg:.2f} ms")

if __name__ == "__main__":
    main()