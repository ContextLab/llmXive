import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from utils import read_json, write_json, get_logger
from config import ensure_directories

def load_existing_results(base_path: Path) -> Dict[str, Any]:
    """
    Load results from null distribution and delta_r2 analysis.
    
    Args:
        base_path: Path to the results directory.
        
    Returns:
        Dictionary containing null distribution stats and delta_r2 results.
    """
    results = {}
    
    null_path = base_path / "null_distribution.json"
    if null_path.exists():
        results["null_distribution"] = read_json(null_path)
    else:
        logging.warning(f"Null distribution file not found at {null_path}")
        results["null_distribution"] = None
        
    delta_r2_path = base_path / "delta_r2.json"
    if delta_r2_path.exists():
        results["delta_r2"] = read_json(delta_r2_path)
    else:
        logging.warning(f"Delta R² file not found at {delta_r2_path}")
        results["delta_r2"] = None
        
    return results

def compute_null_distribution_stats(null_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute statistics from the null distribution data.
    
    Args:
        null_data: Dictionary containing null distribution MAE values.
        
    Returns:
        Dictionary with computed statistics.
    """
    if null_data is None or "mae_values" not in null_data:
        return {
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "count": 0
        }
        
    mae_values = np.array(null_data["mae_values"])
    return {
        "mean": float(np.mean(mae_values)),
        "std": float(np.std(mae_values)),
        "min": float(np.min(mae_values)),
        "max": float(np.max(mae_values)),
        "count": len(mae_values)
    }

def calculate_empirical_p_value(null_data: Optional[Dict[str, Any]], observed_mae: float) -> float:
    """
    Calculate the empirical p-value using the formula:
    p = (count(null_mae <= observed_mae) + 1) / (N + 1)
    
    Args:
        null_data: Dictionary containing null distribution MAE values.
        observed_mae: The observed MAE from the real model.
        
    Returns:
        Empirical p-value.
    """
    if null_data is None or "mae_values" not in null_data:
        logging.warning("Null distribution data is missing, returning p-value of 1.0")
        return 1.0
        
    mae_values = np.array(null_data["mae_values"])
    count = np.sum(mae_values <= observed_mae)
    n = len(mae_values)
    return float((count + 1) / (n + 1))

def generate_model_report(
    base_path: Path,
    output_path: Path,
    observed_metrics: Dict[str, float]
) -> Dict[str, Any]:
    """
    Generate the complete model report JSON file.
    
    Args:
        base_path: Path to the results directory.
        output_path: Path where the model report will be saved.
        observed_metrics: Dictionary containing observed model metrics
                         (mean_mae, mean_r, mean_r2, observed_mae).
                         
    Returns:
        The generated model report dictionary.
    """
    logger = get_logger(__name__)
    logger.info(f"Generating model report from {base_path}")
    
    # Load existing results from previous tasks
    existing_results = load_existing_results(base_path)
    
    # Compute null distribution statistics
    null_stats = compute_null_distribution_stats(existing_results.get("null_distribution"))
    
    # Calculate empirical p-value
    observed_mae = observed_metrics.get("observed_mae", 0.0)
    p_value = calculate_empirical_p_value(
        existing_results.get("null_distribution"),
        observed_mae
    )
    
    # Extract delta_r2 stats if available
    delta_r2_stats = {}
    if existing_results.get("delta_r2"):
        delta_r2_data = existing_results["delta_r2"]
        delta_r2_stats = {
            "delta_r2": delta_r2_data.get("delta_r2", 0.0),
            "status": delta_r2_data.get("status", "unknown"),
            "full_model_r2": delta_r2_data.get("full_model_r2", 0.0),
            "reduced_model_r2": delta_r2_data.get("reduced_model_r2", 0.0)
        }
    
    # Construct the model report
    model_report = {
        "mean_mae": observed_metrics.get("mean_mae", 0.0),
        "mean_r": observed_metrics.get("mean_r", 0.0),
        "mean_r2": observed_metrics.get("mean_r2", 0.0),
        "p_value": p_value,
        "null_distribution_stats": null_stats,
        "observed_mae": observed_mae,
        "permutation_count": existing_results.get("null_distribution", {}).get("count", 0),
        "reduced_model_stats": delta_r2_stats
    }
    
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    # Write the report to file
    write_json(output_path, model_report)
    logger.info(f"Model report saved to {output_path}")
    
    return model_report

def main():
    """
    Main entry point for generating the model report.
    Reads results from previous tasks and generates model_report.json.
    """
    logger = get_logger(__name__)
    logger.info("Starting model report generation")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    results_dir = project_root / "data" / "results"
    output_file = results_dir / "model_report.json"
    
    # Ensure directories exist
    ensure_directories([results_dir])
    
    # Observed metrics from the primary ridge regression (T019)
    # These would typically be computed and passed from the modeling module
    # For now, we load them from a temporary file or compute them
    # In a real pipeline, these would come from the output of run_modeling.py
    
    # Load observed metrics from a temporary file if available
    observed_metrics_path = results_dir / "observed_metrics.json"
    if observed_metrics_path.exists():
        observed_metrics = read_json(observed_metrics_path)
    else:
        # Default values - in a real pipeline, these should be populated
        # by the modeling module after running the ridge regression
        logger.warning("No observed metrics found. Using placeholder values.")
        observed_metrics = {
            "mean_mae": 0.0,
            "mean_r": 0.0,
            "mean_r2": 0.0,
            "observed_mae": 0.0
        }
    
    # Generate the model report
    model_report = generate_model_report(
        base_path=results_dir,
        output_path=output_file,
        observed_metrics=observed_metrics
    )
    
    logger.info("Model report generation completed")
    return model_report

if __name__ == "__main__":
    main()
