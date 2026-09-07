"""
model_report.py

Generates the final model report (data/results/model_report.json) containing:
- Mean out-of-fold MAE, Pearson r, R²
- Empirical p-value from permutation testing
- Null distribution statistics (mean, std, min, max)
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np

from utils import read_json, write_json, get_logger, ensure_file_directory
from config import ensure_directories

# Ensure logger is configured
logger = get_logger(__name__)


def load_existing_results(results_dir: Path) -> Dict[str, Any]:
    """
    Load results from previous modeling steps.
    Expects:
      - data/results/model_metrics.json (from modeling.py)
      - data/results/null_distribution.json (from modeling.py)
    """
    metrics_path = results_dir / "model_metrics.json"
    null_path = results_dir / "null_distribution.json"

    if not metrics_path.exists():
        raise FileNotFoundError(f"Required file missing: {metrics_path}")
    if not null_path.exists():
        raise FileNotFoundError(f"Required file missing: {null_path}")

    metrics = read_json(metrics_path)
    null_dist = read_json(null_path)

    return {
        "metrics": metrics,
        "null_distribution": null_dist
    }


def compute_null_distribution_stats(null_values: list) -> Dict[str, float]:
    """
    Compute summary statistics for the null distribution.
    """
    arr = np.array(null_values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "count": int(len(arr))
    }


def calculate_empirical_p_value(null_values: list, observed_mae: float) -> float:
    """
    Calculate empirical p-value as the proportion of null MAEs <= observed MAE.
    Standard convention: p = (count(null <= observed) + 1) / (N + 1)
    to avoid zero p-values and ensure valid inference.
    """
    if not null_values:
        raise ValueError("Null distribution values cannot be empty")

    null_arr = np.array(null_values)
    # Count how many null MAEs are less than or equal to observed
    count_le = np.sum(null_arr <= observed_mae)
    n = len(null_arr)

    # Empirical p-value calculation (standard convention)
    p_value = (count_le + 1) / (n + 1)
    return float(p_value)


def generate_model_report(results_dir: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate the final model report combining modeling metrics and null distribution stats.

    Output structure:
    {
      "mean_mae": float,
      "mean_r": float,
      "mean_r2": float,
      "p_value": float,
      "null_distribution_stats": { ... },
      "observed_mae": float,
      "permutation_count": int
    }
    """
    if output_path is None:
        output_path = results_dir / "model_report.json"

    ensure_file_directory(output_path)

    # Load existing results
    try:
        data = load_existing_results(results_dir)
    except FileNotFoundError as e:
        logger.error(f"Failed to load results: {e}")
        raise

    metrics = data["metrics"]
    null_data = data["null_distribution"]

    observed_mae = metrics.get("mean_mae")
    observed_r = metrics.get("mean_r")
    observed_r2 = metrics.get("mean_r2")

    if observed_mae is None:
        raise ValueError("Observed MAE not found in model_metrics.json")

    null_values = null_data.get("mae_values", [])
    if not null_values:
        raise ValueError("Null distribution values are empty in null_distribution.json")

    # Compute stats
    null_stats = compute_null_distribution_stats(null_values)
    p_value = calculate_empirical_p_value(null_values, observed_mae)

    report = {
        "mean_mae": float(observed_mae),
        "mean_r": float(observed_r) if observed_r is not None else None,
        "mean_r2": float(observed_r2) if observed_r2 is not None else None,
        "p_value": p_value,
        "null_distribution_stats": null_stats,
        "observed_mae": float(observed_mae),
        "permutation_count": len(null_values)
    }

    # Write report
    write_json(output_path, report)
    logger.info(f"Model report generated: {output_path}")

    return report


def main():
    """
    Entry point for generating the model report.
    """
    # Ensure directories exist
    ensure_directories()

    # Define paths
    project_root = Path(__file__).parent.parent
    results_dir = project_root / "data" / "results"

    if not results_dir.exists():
        logger.error(f"Results directory does not exist: {results_dir}")
        return

    try:
        report = generate_model_report(results_dir)
        logger.info("Model report generation completed successfully.")
        logger.info(f"Report summary: MAE={report['mean_mae']:.4f}, p-value={report['p_value']:.4f}")
    except Exception as e:
        logger.error(f"Failed to generate model report: {e}")
        raise


if __name__ == "__main__":
    main()
