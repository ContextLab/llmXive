"""
Sensitivity Report Generator for GWR Bandwidth Sweep (Task T035).

This module generates a Markdown sensitivity report visualizing the stability
of R² across different GWR bandwidths, as required by SC-004.

It reads the bandwidth sweep results produced by T034 (run_gwr_bandwidth_sweep)
and generates a report at `data/results/sensitivity_report.md`.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np

from utils.logging import get_main_logger

# Ensure output directory exists
RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

logger = get_main_logger(__name__)


def load_bandwidth_sweep_results(sweep_file: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load the GWR bandwidth sweep results from JSON.
    
    Args:
        sweep_file: Path to the sweep results JSON. Defaults to 
                    `data/results/gwr_bandwidth_sweep.json`.
    
    Returns:
        List of dictionaries containing bandwidth, R2, and other metrics.
    """
    if sweep_file is None:
        sweep_file = RESULTS_DIR / "gwr_bandwidth_sweep.json"
    
    if not sweep_file.exists():
        raise FileNotFoundError(
            f"Sweep results file not found at {sweep_file}. "
            "Please ensure T034 (run_gwr_bandwidth_sweep) has been executed."
        )
    
    with open(sweep_file, "r") as f:
        data = json.load(f)
    
    return data.get("sweep_results", [])


def calculate_stability_metrics(sweep_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate stability metrics from the sweep results.
    
    Args:
        sweep_results: List of sweep result dictionaries.
    
    Returns:
        Dictionary with mean R2, std R2, min R2, max R2, and range.
    """
    if not sweep_results:
        return {
            "mean_r2": 0.0,
            "std_r2": 0.0,
            "min_r2": 0.0,
            "max_r2": 0.0,
            "range_r2": 0.0
        }
    
    r2_values = [res.get("r2", 0.0) for res in sweep_results]
    r2_array = np.array(r2_values)
    
    return {
        "mean_r2": float(np.mean(r2_array)),
        "std_r2": float(np.std(r2_array)),
        "min_r2": float(np.min(r2_array)),
        "max_r2": float(np.max(r2_array)),
        "range_r2": float(np.max(r2_array) - np.min(r2_array))
    }


def generate_report_content(
    sweep_results: List[Dict[str, Any]],
    stability_metrics: Dict[str, float]
) -> str:
    """
    Generate the Markdown content for the sensitivity report.
    
    Args:
        sweep_results: List of sweep result dictionaries.
        stability_metrics: Dictionary of calculated stability metrics.
    
    Returns:
        Markdown string content for the report.
    """
    report_lines = [
        "# GWR Bandwidth Sensitivity Report",
        "",
        "## Overview",
        "",
        "This report analyzes the stability of the Geographically Weighted Regression (GWR) "
        "model performance across different bandwidth values. Stability is measured by the "
        "standard deviation of R² scores.",
        "",
        "## Data Source",
        "",
        f"Results loaded from: `data/results/gwr_bandwidth_sweep.json`",
        "",
        "## Stability Metrics",
        "",
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| Mean R² | {stability_metrics['mean_r2']:.4f} |",
        f"| Std Dev R² | {stability_metrics['std_r2']:.4f} |",
        f"| Min R² | {stability_metrics['min_r2']:.4f} |",
        f"| Max R² | {stability_metrics['max_r2']:.4f} |",
        f"| R² Range | {stability_metrics['range_r2']:.4f} |",
        "",
        "## Interpretation",
        "",
        "A lower standard deviation in R² across bandwidths indicates a stable model "
        "that is less sensitive to the specific choice of bandwidth. A high standard "
        "deviation suggests the model performance is highly dependent on the bandwidth "
        "selection.",
        "",
        "## Detailed Results",
        "",
        "| Bandwidth | R² | RMSE | MAE |",
        "| :--- | :--- | :--- | :--- |",
    ]
    
    for res in sweep_results:
        bw = res.get("bandwidth", "N/A")
        r2 = res.get("r2", 0.0)
        rmse = res.get("rmse", 0.0)
        mae = res.get("mae", 0.0)
        report_lines.append(f"| {bw} | {r2:.4f} | {rmse:.4f} | {mae:.4f} |")
    
    report_lines.extend([
        "",
        "## Conclusion",
        "",
        "Based on the standard deviation of R² across the tested bandwidths, the model "
        f"{'shows stable performance' if stability_metrics['std_r2'] < 0.05 else 'exhibits sensitivity to bandwidth choice'}. "
        "The optimal bandwidth should be selected based on the specific bandwidth that maximizes "
        "R² while maintaining model interpretability and avoiding overfitting.",
        "",
        "---",
        f"*Report generated automatically by `code/sensitivity_report.py`.*"
    ])
    
    return "\n".join(report_lines)


def main():
    """
    Main entry point to generate the sensitivity report.
    """
    logger.info("Starting GWR Bandwidth Sensitivity Report generation (Task T035).")
    
    try:
        # Load sweep results
        logger.info(f"Loading bandwidth sweep results from {RESULTS_DIR / 'gwr_bandwidth_sweep.json'}")
        sweep_results = load_bandwidth_sweep_results()
        
        if not sweep_results:
            logger.warning("No sweep results found. Generating report with empty data.")
        
        # Calculate stability metrics
        stability_metrics = calculate_stability_metrics(sweep_results)
        logger.info(f"Stability metrics calculated: Std Dev R² = {stability_metrics['std_r2']:.4f}")
        
        # Generate report content
        report_content = generate_report_content(sweep_results, stability_metrics)
        
        # Write report to file
        output_path = RESULTS_DIR / "sensitivity_report.md"
        with open(output_path, "w") as f:
            f.write(report_content)
        
        logger.info(f"Sensitivity report successfully written to {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error generating sensitivity report: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())