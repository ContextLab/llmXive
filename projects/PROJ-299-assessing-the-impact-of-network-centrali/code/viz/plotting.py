"""
Visualization Helpers

Creates scatter plots and heatmaps.
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
from code.utils.logging_config import setup_logging, get_logger

def generate_plots():
    """
    Generate visualization plots.
    """
    logger = get_logger("viz")
    logger.info("Generating Plots")

    output_dir = project_root / "outputs" / "viz"
    output_dir.mkdir(parents=True, exist_ok=True)

    results_path = project_root / "data" / "analysis" / "regression_results.csv"
    if not results_path.exists():
        logger.warning("Regression results not found. Skipping plots.")
        return 0

    df = pd.read_csv(results_path)

    # Scatter plot (example)
    if not df.empty:
        plt.figure(figsize=(8, 6))
        plt.scatter(df.index, df["beta"] if "beta" in df.columns else range(len(df)))
        plt.title("Regression Coefficients")
        plt.xlabel("Model Index")
        plt.ylabel("Beta")
        plt.savefig(output_dir / "scatter_coefficients.png")
        plt.close()

    logger.info(f"Plots saved to {output_dir}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Generate Plots")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)

    return generate_plots()

if __name__ == "__main__":
    sys.exit(main())
