import os
import json
import time
import logging
import traceback
import resource
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import numpy as np

# Importing from sibling modules based on API surface
# Note: inference and retrieval modules are assumed to exist based on task list
# We will import the necessary types if they are defined there, or define local ones if needed.
# Based on API surface, we have `from inference import ...` but we don't see the content.
# We assume `generate_answer` returns a string or a dict with 'answer' key.
# We assume `run_inference_pipeline` returns a list of results.

# Local imports for data handling
import config

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

@dataclass
class ResourceMetrics:
    """Dataclass to hold resource usage metrics."""
    peak_ram_mb: float
    cpu_time_seconds: float
    wall_time_seconds: float
    strategy: str
    sample_count: int

def get_resource_usage() -> Dict[str, float]:
    """
    Get current resource usage (RAM, CPU time).
    Returns a dictionary with 'peak_ram_mb', 'cpu_time_seconds'.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in kilobytes on Linux/macOS
    peak_ram_kb = usage.ru_maxrss
    peak_ram_mb = peak_ram_kb / 1024.0
    cpu_time = usage.ru_utime + usage.ru_stime
    return {
        "peak_ram_mb": peak_ram_mb,
        "cpu_time_seconds": cpu_time
    }

def record_strategy_execution(strategy_name: str, start_time: float, end_time: float, sample_count: int) -> ResourceMetrics:
    """
    Record execution metrics for a specific strategy.
    """
    current_usage = get_resource_usage()
    return ResourceMetrics(
        peak_ram_mb=current_usage["peak_ram_mb"],
        cpu_time_seconds=current_usage["cpu_time_seconds"],
        wall_time_seconds=end_time - start_time,
        strategy=strategy_name,
        sample_count=sample_count
    )

def save_metrics_to_disk(metrics: ResourceMetrics, output_path: str) -> None:
    """
    Save metrics to a JSON file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    metrics_dict = asdict(metrics)
    with open(output_path, 'w') as f:
        json.dump(metrics_dict, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def load_metrics_from_disk(input_path: str) -> ResourceMetrics:
    """
    Load metrics from a JSON file.
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
    return ResourceMetrics(**data)

def calculate_accuracy(predictions: List[str], ground_truth: List[str]) -> Dict[str, Any]:
    """
    Calculate accuracy metrics between predictions and ground truth.
    
    Args:
        predictions: List of predicted answers (strings).
        ground_truth: List of ground truth answers (strings).
        
    Returns:
        Dictionary containing:
            - exact_match_ratio: float
            - total_samples: int
            - matches: int
            - mismatches: int
    """
    if len(predictions) != len(ground_truth):
        raise ValueError(f"Length mismatch: predictions ({len(predictions)}) vs ground_truth ({len(ground_truth)})")
    
    if len(predictions) == 0:
        return {
            "exact_match_ratio": 0.0,
            "total_samples": 0,
            "matches": 0,
            "mismatches": 0,
            "accuracy": 0.0
        }

    matches = 0
    mismatches = 0
    
    # Normalize strings for comparison (strip whitespace, lowercase)
    # This is a simple normalization; real evaluation might use more complex NLP metrics
    for pred, gt in zip(predictions, ground_truth):
        if isinstance(pred, dict):
            pred = pred.get('answer', str(pred))
        if isinstance(gt, dict):
            gt = gt.get('answer', str(gt))
        
        pred_clean = str(pred).strip().lower()
        gt_clean = str(gt).strip().lower()
        
        if pred_clean == gt_clean:
            matches += 1
        else:
            mismatches += 1
    
    accuracy = matches / len(predictions)
    
    return {
        "exact_match_ratio": accuracy,
        "total_samples": len(predictions),
        "matches": matches,
        "mismatches": mismatches,
        "accuracy": accuracy
    }

def run_evaluation_pipeline(
    predictions_coarse: List[str],
    predictions_medium: List[str],
    predictions_fine: List[str],
    ground_truth: List[str],
    output_dir: str = "data/processed/metrics"
) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline comparing Coarse, Medium, and Fine strategies.
    
    Args:
        predictions_coarse: List of answers from Coarse store retrieval.
        predictions_medium: List of answers from Medium store retrieval.
        predictions_fine: List of answers from Fine store retrieval.
        ground_truth: List of ground truth answers.
        output_dir: Directory to save results.
        
    Returns:
        Dictionary containing evaluation results for all strategies.
    """
    logger.info("Starting evaluation pipeline...")
    
    results = {}
    
    # Calculate accuracy for each strategy
    logger.info("Calculating accuracy for Coarse strategy...")
    results['coarse'] = calculate_accuracy(predictions_coarse, ground_truth)
    
    logger.info("Calculating accuracy for Medium strategy...")
    results['medium'] = calculate_accuracy(predictions_medium, ground_truth)
    
    logger.info("Calculating accuracy for Fine strategy...")
    results['fine'] = calculate_accuracy(predictions_fine, ground_truth)
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    output_path = os.path.join(output_dir, "accuracy_results.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_path}")
    
    # Summary logging
    logger.info(f"Coarse Accuracy: {results['coarse']['accuracy']:.4f}")
    logger.info(f"Medium Accuracy: {results['medium']['accuracy']:.4f}")
    logger.info(f"Fine Accuracy: {results['fine']['accuracy']:.4f}")
    
    return results

def main():
    """
    Main entry point for evaluation.
    This is a placeholder for CLI execution.
    In a real scenario, this would load predictions and ground truth from files.
    """
    logger.info("Evaluation module loaded. Use run_evaluation_pipeline() to evaluate results.")
    
    # Example usage (commented out as it requires real data)
    # predictions = ["answer1", "answer2", "answer3"]
    # ground_truth = ["answer1", "answer2", "answer3"]
    # results = calculate_accuracy(predictions, ground_truth)
    # print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()