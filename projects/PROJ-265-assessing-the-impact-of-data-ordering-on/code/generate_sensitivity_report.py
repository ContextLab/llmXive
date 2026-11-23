import os
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from config import get_results_dir

def load_metrics_csv(csv_path: str) -> pd.DataFrame:
    """Load the coverage metrics CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    return pd.read_csv(csv_path)

def aggregate_by_n(df: pd.DataFrame) -> Dict[int, Dict[str, float]]:
    """Aggregate coverage drop magnitude by sample size N."""
    result = {}
    for n in df["n"].unique():
        subset = df[df["n"] == n]
        avg_drop = subset["diff"].mean()
        result[n] = {
            "avg_drop": avg_drop,
            "min_phi": subset["phi"].min(),
            "max_phi": subset["phi"].max(),
            "count": len(subset),
        }
    return result

def generate_plots(df: pd.DataFrame, output_dir: str):
    """Generate sensitivity plots (placeholder for actual plotting)."""
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)

    # Plot 1: Coverage vs Phi for different N
    plt.figure(figsize=(10, 6))
    for n in df["n"].unique():
        subset = df[df["n"] == n]
        plt.plot(subset["phi"], subset["ordered_cov"], label=f"N={n}")

    plt.xlabel("Phi (Autocorrelation)")
    plt.ylabel("Ordered Coverage")
    plt.title("Coverage vs Autocorrelation by Sample Size")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "coverage_vs_phi.png"))
    plt.close()

    # Plot 2: Coverage Drop vs Phi
    plt.figure(figsize=(10, 6))
    for n in df["n"].unique():
        subset = df[df["n"] == n]
        plt.plot(subset["phi"], subset["diff"], label=f"N={n}")

    plt.xlabel("Phi (Autocorrelation)")
    plt.ylabel("Coverage Drop (Ordered - Shuffled)")
    plt.title("Coverage Drop vs Autocorrelation by Sample Size")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "coverage_drop_vs_phi.png"))
    plt.close()

    logging.info("Plots generated.")

def generate_markdown_report(df: pd.DataFrame, output_path: str):
    """Generate the sensitivity analysis markdown report."""
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        "## Overview",
        "This report analyzes the sensitivity of the coverage drop to sample size (N) and autocorrelation (Phi).",
        "",
        "## Sensitivity by N",
        "",
    ]

    aggregated = aggregate_by_n(df)
    for n, stats in sorted(aggregated.items()):
        report_lines.append(f"### N = {n}")
        report_lines.append(f"- **Average Coverage Drop**: {stats['avg_drop']:.4f}")
        report_lines.append(f"- **Phi Range**: {stats['min_phi']:.1f} to {stats['max_phi']:.1f}")
        report_lines.append(f"- **Number of Configurations**: {stats['count']}")
        report_lines.append("")

    report_lines.append("## Plots")
    report_lines.append("See figures in `results/figures/` for visualizations.")
    report_lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(report_lines))

    logging.info(f"Sensitivity report written to {output_path}")

def main():
    results_dir = get_results_dir()
    csv_path = os.path.join(results_dir, "coverage_metrics.csv")
    report_path = os.path.join(results_dir, "sensitivity_analysis.md")
    figures_dir = os.path.join(results_dir, "figures")

    logging.basicConfig(level=logging.INFO)

    try:
        df = load_metrics_csv(csv_path)
        generate_plots(df, figures_dir)
        generate_markdown_report(df, report_path)
        logging.info("Sensitivity analysis complete.")
    except FileNotFoundError as e:
        logging.error(str(e))
        logging.error("Run 'python code/generate_metrics_csv.py' first.")

if __name__ == "__main__":
    main()
