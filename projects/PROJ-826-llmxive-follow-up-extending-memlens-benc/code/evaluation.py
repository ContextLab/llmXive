import os
import json
import time
import logging
import traceback
import resource
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from utils.logger import get_logger, log_resource_usage

# Configure logger
logger = get_logger("evaluation")

class ResourceMetrics:
    """Container for resource usage metrics."""
    def __init__(self, strategy: str, peak_ram_mb: float, cpu_time_sec: float, duration_sec: float, latency_sec: float = 0.0):
        self.strategy = strategy
        self.peak_ram_mb = peak_ram_mb
        self.cpu_time_sec = cpu_time_sec
        self.duration_sec = duration_sec
        self.latency_sec = latency_sec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "peak_ram_mb": self.peak_ram_mb,
            "cpu_time_sec": self.cpu_time_sec,
            "duration_sec": self.duration_sec,
            "latency_sec": self.latency_sec
        }

def get_resource_usage() -> Tuple[float, float]:
    """Get current resource usage (RAM in MB, CPU time in seconds)."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_ram_mb = usage.ru_maxrss / 1024.0  # Convert KB to MB (Linux)
    cpu_time_sec = usage.ru_utime + usage.ru_stime
    return peak_ram_mb, cpu_time_sec

def record_strategy_execution(
    strategy: str,
    start_time: float,
    end_time: float,
    peak_ram_mb: float,
    cpu_time_sec: float,
    latency_sec: float = 0.0
) -> ResourceMetrics:
    """Record metrics for a specific strategy execution."""
    duration_sec = end_time - start_time
    metrics = ResourceMetrics(
        strategy=strategy,
        peak_ram_mb=peak_ram_mb,
        cpu_time_sec=cpu_time_sec,
        duration_sec=duration_sec,
        latency_sec=latency_sec
    )
    logger.info(f"Recorded metrics for {strategy}: RAM={peak_ram_mb:.2f}MB, CPU={cpu_time_sec:.2f}s, Latency={latency_sec:.2f}s")
    return metrics

def save_metrics_to_disk(metrics_list: List[ResourceMetrics], output_path: str) -> None:
    """Save a list of ResourceMetrics to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    data = [m.to_dict() for m in metrics_list]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved metrics to {output_path}")

def load_metrics_from_disk(input_path: str) -> List[ResourceMetrics]:
    """Load ResourceMetrics from a JSON file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Metrics file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    return [
        ResourceMetrics(
            strategy=m["strategy"],
            peak_ram_mb=m["peak_ram_mb"],
            cpu_time_sec=m["cpu_time_sec"],
            duration_sec=m["duration_sec"],
            latency_sec=m.get("latency_sec", 0.0)
        )
        for m in data
    ]

def calculate_accuracy(predictions: List[str], ground_truths: List[str]) -> float:
    """Calculate accuracy (exact match or fuzzy match logic)."""
    if not predictions or not ground_truths or len(predictions) != len(ground_truths):
        raise ValueError("Invalid prediction/ground truth lists for accuracy calculation.")
    
    matches = sum(1 for p, g in zip(predictions, ground_truths) if p.strip().lower() == g.strip().lower())
    return matches / len(predictions)

def compute_retrieval_latency_relative(
    metrics: List[ResourceMetrics],
    baseline_strategy: str = "Coarse"
) -> Dict[str, Any]:
    """
    Compute retrieval latency relative to Coarse baseline: (Strategy - Coarse) / Coarse.
    Flags deviations where relative latency > 0.5 (50% overhead).
    
    SC-004: Compute retrieval latency relative to Coarse baseline (Fine/Medium - Coarse) / Coarse
    and flag deviations.
    
    Args:
        metrics: List of ResourceMetrics for all strategies (Coarse, Medium, Fine).
        baseline_strategy: The strategy to use as the baseline (default: "Coarse").
    
    Returns:
        Dictionary containing relative latency calculations and deviation flags.
    """
    if not metrics:
        logger.warning("No metrics provided for relative latency calculation.")
        return {"error": "No metrics provided"}

    # Group metrics by strategy
    strategy_map: Dict[str, ResourceMetrics] = {m.strategy: m for m in metrics}
    
    if baseline_strategy not in strategy_map:
        raise ValueError(f"Baseline strategy '{baseline_strategy}' not found in metrics. Available: {list(strategy_map.keys())}")
    
    baseline_metrics = strategy_map[baseline_strategy]
    baseline_latency = baseline_metrics.latency_sec
    
    if baseline_latency <= 0:
        logger.warning(f"Baseline latency for {baseline_strategy} is {baseline_latency}. Cannot compute relative difference.")
        return {
            "baseline_strategy": baseline_strategy,
            "baseline_latency_sec": baseline_latency,
            "relative_latencies": {},
            "deviations": {}
        }

    results = {
        "baseline_strategy": baseline_strategy,
        "baseline_latency_sec": baseline_latency,
        "relative_latencies": {},
        "deviations": {}
    }

    for strategy_name, metric in strategy_map.items():
        if strategy_name == baseline_strategy:
            continue
        
        strategy_latency = metric.latency_sec
        relative_latency = (strategy_latency - baseline_latency) / baseline_latency
        
        # Flag deviations: if relative latency > 0.5 (50% overhead)
        is_deviation = relative_latency > 0.5
        
        results["relative_latencies"][strategy_name] = {
            "absolute_latency_sec": strategy_latency,
            "relative_latency_ratio": round(relative_latency, 4),
            "percent_overhead": round(relative_latency * 100, 2)
        }
        
        results["deviations"][strategy_name] = {
            "is_deviation": is_deviation,
            "threshold": 0.5,
            "message": f"High overhead detected for {strategy_name}: {relative_latency*100:.2f}% increase over {baseline_strategy}" if is_deviation else "Within acceptable limits"
        }
        
        logger.info(f"Relative Latency [{strategy_name} vs {baseline_strategy}]: {relative_latency:.4f} ({results['relative_latencies'][strategy_name]['percent_overhead']}% overhead). Deviation: {is_deviation}")

    return results

def run_evaluation_pipeline(
    metrics_input_path: str,
    output_dir: str,
    baseline_strategy: str = "Coarse"
) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline including relative latency computation.
    
    Args:
        metrics_input_path: Path to the JSON file containing raw metrics.
        output_dir: Directory to save the evaluation reports.
        baseline_strategy: Strategy to use as baseline for relative latency.
    
    Returns:
        Dictionary containing the full evaluation results.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load metrics
    metrics = load_metrics_from_disk(metrics_input_path)
    
    # Compute relative latency
    relative_latency_results = compute_retrieval_latency_relative(metrics, baseline_strategy)
    
    # Save relative latency results
    relative_latency_output_path = os.path.join(output_dir, "relative_latency_report.json")
    with open(relative_latency_output_path, 'w') as f:
        json.dump(relative_latency_results, f, indent=2)
    
    logger.info(f"Saved relative latency report to {relative_latency_output_path}")
    
    return relative_latency_results

def main():
    """Main entry point for evaluation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run evaluation pipeline and compute relative latency.")
    parser.add_argument("--metrics-path", type=str, required=True, help="Path to input metrics JSON file.")
    parser.add_argument("--output-dir", type=str, default="data/processed/metrics", help="Output directory for reports.")
    parser.add_argument("--baseline", type=str, default="Coarse", help="Baseline strategy name.")
    
    args = parser.parse_args()
    
    try:
        results = run_evaluation_pipeline(args.metrics_path, args.output_dir, args.baseline)
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Evaluation pipeline failed: {e}", exc_info=True)
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()