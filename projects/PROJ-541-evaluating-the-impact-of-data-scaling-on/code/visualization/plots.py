"""Visualization module for the llmXive data scaling impact study."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

logger = logging.getLogger(__name__)

# Ensure the plot output directory exists
FIGURES_DIR = Path("results/figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def calculate_confidence_interval(
    successes: int, total: int, alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate the Clopper-Pearson (exact) confidence interval for a binomial proportion.

    Args:
        successes: Number of successes (e.g., rejections of null hypothesis).
        total: Total number of trials (iterations).
        alpha: Significance level for the confidence interval (default 0.05).

    Returns:
        A tuple (lower_bound, upper_bound) for the confidence interval.
    """
    if total == 0:
        return 0.0, 0.0

    # Use scipy.stats.beta for the exact Clopper-Pearson interval
    # Lower bound: Beta(alpha/2, successes, total - successes + 1)
    # Upper bound: Beta(1 - alpha/2, successes + 1, total - successes)
    # Note: scipy.stats.beta.ppf(q, a, b)
    # For successes=0, lower is 0. For successes=total, upper is 1.

    if successes == 0:
        lower = 0.0
    else:
        lower = stats.beta.ppf(alpha / 2, successes, total - successes + 1)

    if successes == total:
        upper = 1.0
    else:
        upper = stats.beta.ppf(1 - alpha / 2, successes + 1, total - successes)

    return float(lower), float(upper)


def generate_error_rate_plot(
    df: Optional[pd.DataFrame] = None,
    output_path: Optional[str] = None,
    alpha_threshold: float = 0.05,
) -> None:
    """
    Generate a plot of empirical error rates with confidence intervals.

    This function expects a DataFrame with the following columns:
    - scaling_method: The scaling method used (string).
    - error_rate: The empirical error rate (float).
    - ci_lower: Lower bound of the confidence interval (float).
    - ci_upper: Upper bound of the confidence interval (float).
    - test_type: The statistical test used (optional, for grouping).
    - config_id: The configuration ID (optional, for grouping).

    If `df` is None, it attempts to load from the default path:
    'results/aggregate_metrics.csv'.

    Args:
        df: DataFrame containing the aggregate metrics.
        output_path: Path to save the plot. Defaults to 'results/figures/error_rate_plot.png'.
        alpha_threshold: The horizontal reference line threshold (default 0.05).
    """
    if df is None:
        input_path = Path("results/aggregate_metrics.csv")
        if not input_path.exists():
            raise FileNotFoundError(
                f"Input file not found: {input_path}. "
                "Please ensure T029 has run and produced 'results/aggregate_metrics.csv'."
            )
        df = pd.read_csv(input_path)

    required_cols = ["scaling_method", "error_rate", "ci_lower", "ci_upper"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"DataFrame missing required columns: {missing_cols}. "
            f"Required: {required_cols}"
        )

    # Set style
    sns.set_theme(style="whitegrid", context="talk")

    # Create the plot
    plt.figure(figsize=(12, 8))

    # Use seaborn pointplot or stripplot with error bars
    # Since we have pre-calculated CI bounds, we can use errorbar capability in newer seaborn
    # or manually plot errorbars.
    # To ensure compatibility and explicit control, we'll use plt.errorbar or a custom approach
    # if seaborn's pointplot doesn't accept pre-calculated CIs directly in older versions.
    # However, seaborn.pointplot with 'ci' argument expects raw data or a function.
    # Given the input is already aggregated with CIs, let's use a barplot with errorbars
    # or scatter with errorbars.

    # Sort by scaling_method for consistent plotting
    df = df.sort_values(by="scaling_method")

    # Plot using errorbar
    x_positions = range(len(df))
    x_labels = [f"{row['scaling_method']}" for _, row in df.iterrows()]

    # If there are multiple tests/configs per scaling method, we might need to group.
    # Assuming the input is already grouped or we plot all points.
    # If we want to group by scaling_method, we need to aggregate or use a loop.
    # Let's assume the input DataFrame is one row per (scaling_method, test_type, config_id)
    # and we want to plot them all.

    # To make it readable, let's group by scaling_method on the x-axis
    unique_methods = df["scaling_method"].unique()
    unique_methods = sorted(unique_methods)

    # Create a mapping for x-axis positions
    method_to_x = {m: i for i, m in enumerate(unique_methods)}

    # Prepare data for plotting
    plot_data = []
    for _, row in df.iterrows():
        plot_data.append({
            "x": method_to_x[row["scaling_method"]],
            "y": row["error_rate"],
            "yerr": [[row["error_rate"] - row["ci_lower"]], [row["ci_upper"] - row["error_rate"]]],
            "label": f"{row.get('test_type', 'test')} - {row.get('config_id', 'config')}"
        })

    # Plot
    for item in plot_data:
        plt.errorbar(
            item["x"],
            item["y"],
            yerr=item["yerr"],
            fmt="o",
            capsize=5,
            label=item["label"],
            markersize=8,
            linestyle="None"
        )

    # Set x-axis ticks and labels
    plt.xticks(range(len(unique_methods)), unique_methods)
    plt.xlabel("Scaling Method")
    plt.ylabel("Empirical Error Rate")
    plt.title("Empirical Error Rate with 95% Confidence Intervals (Clopper-Pearson)")

    # Add horizontal reference line
    plt.axhline(
        y=alpha_threshold,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Significance Threshold ($\\alpha$ = {alpha_threshold})"
    )
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

    # Save the plot
    if output_path is None:
        output_path = "results/figures/error_rate_plot.png"

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.info(f"Error rate plot saved to {output_path}")


def generate_sensitivity_plot(
    df: Optional[pd.DataFrame] = None,
    output_path: Optional[str] = None,
) -> None:
    """
    Generate a plot showing error rates across different alpha thresholds.

    Args:
        df: DataFrame from sensitivity analysis (results/sensitivity_analysis.csv).
            Expected columns: alpha, scaling_method, error_rate, power.
        output_path: Path to save the plot.
    """
    if df is None:
        input_path = Path("results/sensitivity_analysis.csv")
        if not input_path.exists():
            logger.warning(f"Sensitivity analysis file not found: {input_path}. Skipping plot.")
            return
        df = pd.read_csv(input_path)

    if "alpha" not in df.columns or "error_rate" not in df.columns:
        raise ValueError("Sensitivity plot requires 'alpha' and 'error_rate' columns.")

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))

    # Plot error rate vs alpha for each scaling method
    sns.lineplot(
        data=df,
        x="alpha",
        y="error_rate",
        hue="scaling_method",
        marker="o",
        err_style="band"
    )

    plt.xlabel("Alpha Threshold")
    plt.ylabel("Empirical Error Rate")
    plt.title("Sensitivity of Error Rate to Alpha Threshold")
    plt.legend(title="Scaling Method")

    if output_path is None:
        output_path = "results/figures/sensitivity_plot.png"

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Sensitivity plot saved to {output_path}")