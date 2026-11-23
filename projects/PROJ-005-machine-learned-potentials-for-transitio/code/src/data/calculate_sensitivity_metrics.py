"""
Task T017b: Calculate and store sensitivity metrics.

Input: code/data/results/cutoff_sensitivity_raw.json (from T017a)
Logic: Compute variance of metrics (avg_degree, edge_count, density) across cutoffs.
Output: code/data/results/cutoff_sensitivity.json
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from src.utils.logging import get_logger
from src.utils.config import get_project_root

logger = get_logger(__name__)

def load_raw_sensitivity_results(input_path: Path) -> List[Dict[str, Any]]:
    """Load the raw sensitivity analysis results from T017a."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of results, got {type(data)}")
    
    return data

def calculate_variance_metrics(raw_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute variance of metrics across cutoffs.
    
    Metrics to analyze:
    - samples_processed
    - total_edges
    - graph_density
    - avg_edge_feature_cv
    
    Returns a summary dictionary with variance and coefficient of variation.
    """
    if not raw_results:
        raise ValueError("Raw results list is empty")

    # Filter out entries with "no_data" status if any
    valid_results = [r for r in raw_results if r.get("status") != "no_data"]
    
    if not valid_results:
        logger.warning("No valid data found in raw results. All entries marked as 'no_data'.")
        # Return a structure indicating no data was available for variance calculation
        return {
            "status": "no_data",
            "message": "No valid data available for variance calculation",
            "metrics": {}
        }

    cutoffs = [r["cutoff"] for r in valid_results]
    samples_processed = [r["samples_processed"] for r in valid_results]
    total_edges = [r["total_edges"] for r in valid_results]
    graph_density = [r["graph_density"] for r in valid_results]
    avg_edge_feature_cv = [r["avg_edge_feature_cv"] for r in valid_results]

    # Calculate variance for each metric
    metrics_variance = {
        "samples_processed": float(np.var(samples_processed, ddof=1)) if len(samples_processed) > 1 else 0.0,
        "total_edges": float(np.var(total_edges, ddof=1)) if len(total_edges) > 1 else 0.0,
        "graph_density": float(np.var(graph_density, ddof=1)) if len(graph_density) > 1 else 0.0,
        "avg_edge_feature_cv": float(np.var(avg_edge_feature_cv, ddof=1)) if len(avg_edge_feature_cv) > 1 else 0.0,
    }

    # Calculate coefficient of variation (CV = std / mean) for normalized comparison
    metrics_cv = {}
    for name, values in [
        ("samples_processed", samples_processed),
        ("total_edges", total_edges),
        ("graph_density", graph_density),
        ("avg_edge_feature_cv", avg_edge_feature_cv)
    ]:
        mean_val = np.mean(values)
        std_val = np.std(values, ddof=1) if len(values) > 1 else 0.0
        if mean_val != 0:
            metrics_cv[name] = float(std_val / abs(mean_val))
        else:
            metrics_cv[name] = 0.0 if std_val == 0 else float('inf')

    # Overall stability score (lower is better) - average of normalized variances
    # Using mean of CVs as a stability indicator
    stability_score = float(np.mean([v for v in metrics_cv.values() if v != float('inf')]))

    return {
        "cutoffs_tested": cutoffs,
        "num_valid_samples": len(valid_results),
        "metrics": {
            "variance": metrics_variance,
            "coefficient_of_variation": metrics_cv
        },
        "stability_score": stability_score,
        "status": "computed"
    }

def save_sensitivity_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """Save the calculated sensitivity metrics to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Sensitivity metrics saved to {output_path}")

def run_sensitivity_metric_calculation(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point for T017b.
    
    Args:
        input_path: Path to cutoff_sensitivity_raw.json (default: derived from project root)
        output_path: Path to save cutoff_sensitivity.json (default: derived from project root)
        
    Returns:
        The calculated metrics dictionary
    """
    project_root = get_project_root()
    
    if input_path is None:
        input_path = project_root / "data" / "results" / "cutoff_sensitivity_raw.json"
    
    if output_path is None:
        output_path = project_root / "data" / "results" / "cutoff_sensitivity.json"

    logger.info(f"Loading raw sensitivity results from {input_path}")
    raw_results = load_raw_sensitivity_results(input_path)
    
    logger.info("Calculating variance metrics across cutoffs")
    metrics = calculate_variance_metrics(raw_results)
    
    logger.info(f"Saving sensitivity metrics to {output_path}")
    save_sensitivity_metrics(metrics, output_path)
    
    return metrics

def main():
    """CLI entry point."""
    try:
        metrics = run_sensitivity_metric_calculation()
        logger.info(f"Task T017b completed successfully. Stability score: {metrics.get('stability_score', 'N/A')}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during sensitivity metric calculation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
