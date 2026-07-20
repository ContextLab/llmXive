import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from config import AnalysisConfig, ensure_dirs
from utils.logger import setup_logging

def setup_logging():
    """Configure logging for report generation."""
    return setup_logging("generate_reports", log_level=logging.INFO)

def load_shap_rankings(shap_rankings_path: Path) -> list:
    """Load SHAP rankings from a JSON file."""
    if not shap_rankings_path.exists():
        raise FileNotFoundError(f"SHAP rankings file not found: {shap_rankings_path}")
    
    with open(shap_rankings_path, 'r') as f:
        data = json.load(f)
    
    # Expected format: {"rankings": [{"feature_id": int, "mean_abs_shap": float, ...}, ...]}
    if "rankings" not in data:
        raise ValueError("Invalid SHAP rankings format: missing 'rankings' key")
    
    return data["rankings"]

def load_sensitivity_results(sensitivity_path: Path) -> list:
    """Load sensitivity analysis results from a CSV file."""
    if not sensitivity_path.exists():
        raise FileNotFoundError(f"Sensitivity results file not found: {sensitivity_path}")
    
    results = []
    with open(sensitivity_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "cutoff": float(row["cutoff"]),
                "r2": float(row["r2"]),
                "mae": float(row["mae"])
            })
    
    return results

def load_perturbation_results(perturbation_path: Path) -> list:
    """Load perturbation study results from a CSV file."""
    if not perturbation_path.exists():
        raise FileNotFoundError(f"Perturbation results file not found: {perturbation_path}")
    
    results = []
    with open(perturbation_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "feature_id": int(row["feature_id"]),
                "original_r2": float(row["original_r2"]),
                "perturbed_r2": float(row["perturbed_r2"]),
                "delta": float(row["delta"])
            })
    
    return results

def generate_feature_importance_plot(shap_rankings: list, output_path: Path):
    """Generate a bar plot of feature importance based on SHAP values."""
    if not shap_rankings:
        raise ValueError("No SHAP rankings provided for plotting")
    
    # Sort by mean absolute SHAP value (descending)
    sorted_rankings = sorted(shap_rankings, key=lambda x: x["mean_abs_shap"], reverse=True)
    
    # Take top 15 features for readability
    top_n = min(15, len(sorted_rankings))
    top_features = sorted_rankings[:top_n]
    
    labels = [f"Feature {f['feature_id']}" for f in top_features]
    values = [f["mean_abs_shap"] for f in top_features]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(labels, values, color='steelblue')
    ax.set_xlabel('Mean Absolute SHAP Value')
    ax.set_title('Top Feature Importance (SHAP)')
    ax.invert_yaxis()  # Highest importance at top
    
    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax.text(val + 0.01, bar.get_y() + bar.get_height()/2, 
               f'{val:.3f}', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Feature importance plot saved to {output_path}")

def generate_sensitivity_report(sensitivity_results: list, output_path: Path):
    """Generate a CSV report of sensitivity analysis results."""
    if not sensitivity_results:
        raise ValueError("No sensitivity results provided for report")
    
    # Sort by cutoff
    sorted_results = sorted(sensitivity_results, key=lambda x: x["cutoff"])
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["cutoff", "r2", "mae"])
        writer.writeheader()
        writer.writerows(sorted_results)
    
    logging.info(f"Sensitivity report saved to {output_path}")

def generate_perturbation_report(perturbation_results: list, output_path: Path):
    """Generate a CSV report of perturbation study results."""
    if not perturbation_results:
        raise ValueError("No perturbation results provided for report")
    
    # Sort by delta (descending) to show most impactful features first
    sorted_results = sorted(perturbation_results, key=lambda x: abs(x["delta"]), reverse=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["feature_id", "original_r2", "perturbed_r2", "delta"])
        writer.writeheader()
        writer.writerows(sorted_results)
    
    logging.info(f"Perturbation report saved to {output_path}")

def main():
    """Main entry point for generating analysis reports."""
    parser = argparse.ArgumentParser(description="Generate analysis reports from intermediate results")
    parser.add_argument("--shap-rankings", type=str, required=True,
                      help="Path to SHAP rankings JSON file")
    parser.add_argument("--sensitivity-results", type=str, required=True,
                      help="Path to sensitivity results CSV file")
    parser.add_argument("--perturbation-results", type=str, required=True,
                      help="Path to perturbation results CSV file")
    parser.add_argument("--output-dir", type=str, default="artifacts",
                      help="Directory to save output reports")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    ensure_dirs([output_dir])
    
    # Load inputs
    logger.info("Loading input data...")
    shap_rankings = load_shap_rankings(Path(args.shap_rankings))
    sensitivity_results = load_sensitivity_results(Path(args.sensitivity_results))
    perturbation_results = load_perturbation_results(Path(args.perturbation_results))
    
    # Generate outputs
    logger.info("Generating feature importance plot...")
    feature_importance_path = output_dir / "feature_importance.png"
    generate_feature_importance_plot(shap_rankings, feature_importance_path)
    
    logger.info("Generating sensitivity report...")
    sensitivity_path = output_dir / "sensitivity_report.csv"
    generate_sensitivity_report(sensitivity_results, sensitivity_path)
    
    logger.info("Generating perturbation report...")
    perturbation_path = output_dir / "perturbation_results.csv"
    generate_perturbation_report(perturbation_results, perturbation_path)
    
    logger.info("All reports generated successfully.")

if __name__ == "__main__":
    main()