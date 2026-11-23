import time
import json
import sys
import argparse
import torch
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from src.data.loader import load_config

def evaluate_latency_pass_fail(average_latency_ms: float, threshold_ms: Optional[float]) -> Dict[str, Any]:
    """
    Evaluate whether the average latency meets the threshold.
    
    Args:
        average_latency_ms: Average latency in milliseconds.
        threshold_ms: Threshold latency in milliseconds (can be None if deferred).
        
    Returns:
        Dictionary with status ("MEASURED" or "PASS"/"FAIL"), average_ms, and threshold_ms.
    """
    if threshold_ms is None:
        status = "MEASURED"
    else:
        status = "PASS" if average_latency_ms <= threshold_ms else "FAIL"
    
    return {
        "status": status,
        "average_ms": average_latency_ms,
        "threshold_ms": threshold_ms
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

def run_pipeline(output_path: str, threshold_ms: Optional[float] = None) -> None:
    """
    Run a latency benchmark pipeline.
    
    This function simulates a real inference scenario by creating a dummy model
    and measuring the time it takes to perform a forward pass.
    
    Args:
        output_path: Path to save the latency report JSON.
        threshold_ms: Optional threshold for pass/fail evaluation.
    """
    # Create a dummy model to measure realistic inference time on CPU
    # Using a small transformer-like operation to simulate inference
    dummy_input = torch.randn(1, 3, 224, 224)
    dummy_weight = torch.randn(64, 3, 3, 3)
    
    def dummy_inference():
        # Simulate a forward pass operation
        _ = torch.nn.functional.conv2d(dummy_input, dummy_weight)
        # Add a small sleep to simulate processing overhead if needed, 
        # but we rely on actual computation time here.
    
    print(f"Running latency benchmark with {5} measurement runs...")
    
    metrics = measure_inference_latency(
        func=dummy_inference,
        warmup_runs=1,
        measurement_runs=5
    )
    
    avg_latency = metrics["average_latency_ms"]
    
    # Evaluate against threshold
    evaluation = evaluate_latency_pass_fail(avg_latency, threshold_ms)
    
    # Construct final report
    report = {
        "average_ms": avg_latency,
        "status": evaluation["status"],
        "threshold_ms": threshold_ms,
        "breakdown": {
            "min_ms": metrics["min_latency_ms"],
            "max_ms": metrics["max_latency_ms"],
            "samples_ms": metrics["samples"]
        }
    }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write report to disk
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Latency report written to: {output_path}")
    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"Status: {evaluation['status']}")

def main():
    """
    Main entry point for the latency metrics tool.
    """
    parser = argparse.ArgumentParser(description="Latency Metrics Tool")
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=None, 
        help="Latency threshold in milliseconds (optional, defaults to None/deferred)"
    )
    parser.add_argument(
        "--window", 
        type=int, 
        default=10, 
        help="Window size for moving average (not used in main pipeline yet)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/latency_verification_report.json",
        help="Output path for the latency report"
    )
    args = parser.parse_args()
    
    run_pipeline(args.output, args.threshold)

if __name__ == "__main__":
    main()