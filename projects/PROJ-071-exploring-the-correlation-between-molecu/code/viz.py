"""Visualization module for molecular complexity and degradation analysis.

Generates diagnostic plots including scatter plots with regression lines
and residual diagnostic plots (histogram, QQ-plot, residuals vs fitted).
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
from matplotlib.ticker import FuncFormatter

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Output directory for figures
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"


def get_data_path() -> Path:
    """Return the data directory path."""
    return PROJECT_ROOT / "data"


def check_gate_status() -> Tuple[bool, str]:
    """Check if the data availability gate passed.

    Returns:
        Tuple of (passed, reason)
    """
    gate_file = get_data_path() / "gate_status.json"
    if not gate_file.exists():
        return False, "Gate status file not found"

    try:
        with open(gate_file, "r") as f:
            status = json.load(f)

        if status.get("status") == "PASS":
            return True, "Gate passed"
        else:
            return False, status.get("reason", "Unknown reason")
    except Exception as e:
        logger.error(f"Error reading gate status: {e}")
        return False, str(e)


def check_statistical_gate() -> Tuple[bool, str]:
    """Check if the statistical gate passed.

    Returns:
        Tuple of (passed, reason)
    """
    gate_file = get_data_path() / "stat_gate_status.json"
    if not gate_file.exists():
        return False, "Statistical gate status file not found"

    try:
        with open(gate_file, "r") as f:
            status = json.load(f)

        if status.get("status") == "PASS":
            return True, "Statistical gate passed"
        else:
            return False, status.get("reason", "Unknown reason")
    except Exception as e:
        logger.error(f"Error reading statistical gate status: {e}")
        return False, str(e)


def load_analysis_results() -> Optional[Dict[str, Any]]:
    """Load analysis results from JSON file.

    Returns:
        Dictionary containing analysis results or None if not found.
    """
    results_file = get_data_path() / "processed" / "analysis_results.json"
    if not results_file.exists():
        logger.warning(f"Analysis results file not found: {results_file}")
        return None

    try:
        with open(results_file, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading analysis results: {e}")
        return None


def load_residuals_data() -> Optional[pd.DataFrame]:
    """Load residuals data for diagnostic plots.

    Returns:
        DataFrame with residuals or None if not found.
    """
    # Try to load from analysis results first
    results = load_analysis_results()
    if results and results.get("status") == "PASS":
        # Check if residuals are embedded in results
        if "residuals" in results:
            return pd.DataFrame(results["residuals"])

    # Try to load from a separate file
    residuals_file = get_data_path() / "processed" / "residuals.csv"
    if residuals_file.exists():
        try:
            return pd.read_csv(residuals_file)
        except Exception as e:
            logger.error(f"Error loading residuals file: {e}")

    return None


def plot_scatter_with_regression(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    output_path: Path,
) -> None:
    """Generate a scatter plot with regression line.

    Args:
        x: Independent variable values
        y: Dependent variable values
        x_label: Label for x-axis
        y_label: Label for y-axis
        title: Plot title
        output_path: Path to save the figure
    """
    plt.style.use("seaborn-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter plot
    ax.scatter(x, y, alpha=0.6, edgecolors="w", linewidth=0.5)

    # Fit regression line
    if len(x) > 1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        x_line = np.linspace(min(x), max(x), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, "r-", linewidth=2, label=f"y = {slope:.4f}x + {intercept:.4f}\nR² = {r_value**2:.4f}")
        ax.legend()

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved scatter plot to {output_path}")


def generate_placeholder_plot(output_path: Path, title: str) -> None:
    """Generate a placeholder plot when data is unavailable.

    Args:
        output_path: Path to save the figure
        title: Plot title
    """
    plt.style.use("seaborn-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.text(
        0.5, 0.5,
        f"No Data Available\n\n{title}",
        ha="center",
        va="center",
        fontsize=14,
        transform=ax.transAxes,
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved placeholder plot to {output_path}")


def generate_correlation_scatter_plots(results: Dict[str, Any]) -> None:
    """Generate scatter plots for top correlated features.

    Args:
        results: Analysis results dictionary
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Extract data
    df = results.get("data")
    if df is None:
        logger.warning("No data found in analysis results")
        return

    # Define feature pairs to plot
    feature_pairs = [
        ("tpsa", "half_life", "TPSA vs Half-life"),
        ("rotatable_bonds", "half_life", "Rotatable Bonds vs Half-life"),
        ("mw", "half_life", "Molecular Weight vs Half-life"),
        ("aromatic_rings", "half_life", "Aromatic Rings vs Half-life"),
    ]

    for x_col, y_col, title in feature_pairs:
        if x_col in df.columns and y_col in df.columns:
            x_data = df[x_col].dropna()
            y_data = df[y_col].loc[x_data.index].dropna()

            if len(x_data) > 1:
                output_path = OUTPUT_DIR / f"scatter_{x_col}_vs_{y_col}.png"
                plot_scatter_with_regression(
                    x_data.values,
                    y_data.values,
                    x_col,
                    y_col,
                    title,
                    output_path,
                )
            else:
                generate_placeholder_plot(
                    OUTPUT_DIR / f"scatter_{x_col}_vs_{y_col}.png",
                    f"Not enough data for {title}",
                )


def plot_residual_histogram(residuals: np.ndarray, output_path: Path) -> None:
    """Plot histogram of residuals.

    Args:
        residuals: Array of residual values
        output_path: Path to save the figure
    """
    plt.style.use("seaborn-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(residuals, bins=30, alpha=0.7, edgecolor="black")
    ax.axvline(x=0, color="red", linestyle="--", linewidth=2, label="Zero")

    # Add normal distribution curve
    if len(residuals) > 1:
        mu, sigma = np.mean(residuals), np.std(residuals)
        x = np.linspace(mu - 3 * sigma, mu + 3 * sigma, 100)
        y = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
        ax.plot(x, y * len(residuals) * (x[1] - x[0]), "r-", linewidth=2, label="Normal Fit")

    ax.set_xlabel("Residuals")
    ax.set_ylabel("Frequency")
    ax.set_title("Histogram of Residuals")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved residual histogram to {output_path}")


def plot_qq_plot(residuals: np.ndarray, output_path: Path) -> None:
    """Plot QQ-plot of residuals.

    Args:
        residuals: Array of residual values
        output_path: Path to save the figure
    """
    plt.style.use("seaborn-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    if len(residuals) > 1:
        stats.probplot(residuals, dist="norm", plot=ax)
        ax.set_title("QQ-Plot of Residuals")
    else:
        ax.text(
            0.5, 0.5,
            "Not enough data for QQ-plot",
            ha="center",
            va="center",
            fontsize=14,
            transform=ax.transAxes,
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved QQ-plot to {output_path}")


def plot_residuals_vs_fitted(
    fitted: np.ndarray,
    residuals: np.ndarray,
    output_path: Path,
) -> None:
    """Plot residuals vs fitted values.

    Args:
        fitted: Array of fitted values
        residuals: Array of residual values
        output_path: Path to save the figure
    """
    plt.style.use("seaborn-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.scatter(fitted, residuals, alpha=0.6, edgecolors="w", linewidth=0.5)
    ax.axhline(y=0, color="red", linestyle="--", linewidth=2)

    # Add smooth trend line
    if len(fitted) > 1:
        sorted_idx = np.argsort(fitted)
        fitted_sorted = fitted[sorted_idx]
        residuals_sorted = residuals[sorted_idx]

        # Simple moving average for trend
        window = min(10, len(fitted) // 5)
        if window > 1:
            trend = np.convolve(residuals_sorted, np.ones(window) / window, mode="valid")
            fitted_trend = fitted_sorted[window // 2 : -(window // 2)]
            ax.plot(fitted_trend, trend, "b-", linewidth=2, label="Trend")
            ax.legend()

    ax.set_xlabel("Fitted Values")
    ax.set_ylabel("Residuals")
    ax.set_title("Residuals vs Fitted Values")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved residuals vs fitted plot to {output_path}")


def generate_residual_diagnostic_plots() -> None:
    """Generate all residual diagnostic plots.

    Reads analysis results and generates:
    - residuals.png (histogram)
    - qq_plot.png (QQ-plot)
    - residuals_vs_fitted.png
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load analysis results
    results = load_analysis_results()
    if not results or results.get("status") != "PASS":
        logger.warning("Analysis results not available or gate failed. Skipping residual plots.")
        # Generate placeholder plots
        generate_placeholder_plot(OUTPUT_DIR / "residuals.png", "Residual Analysis")
        generate_placeholder_plot(OUTPUT_DIR / "qq_plot.png", "QQ-Plot")
        generate_placeholder_plot(OUTPUT_DIR / "residuals_vs_fitted.png", "Residuals vs Fitted")
        return

    # Extract residuals data
    residuals_data = load_residuals_data()
    if residuals_data is None or len(residuals_data) == 0:
        logger.warning("No residuals data found. Generating placeholder plots.")
        generate_placeholder_plot(OUTPUT_DIR / "residuals.png", "Residual Analysis")
        generate_placeholder_plot(OUTPUT_DIR / "qq_plot.png", "QQ-Plot")
        generate_placeholder_plot(OUTPUT_DIR / "residuals_vs_fitted.png", "Residuals vs Fitted")
        return

    # Check for required columns
    if "residuals" in residuals_data.columns:
        residuals = residuals_data["residuals"].dropna().values
    elif "residual" in residuals_data.columns:
        residuals = residuals_data["residual"].dropna().values
    else:
        logger.warning("No 'residuals' column found in data. Generating placeholder plots.")
        generate_placeholder_plot(OUTPUT_DIR / "residuals.png", "Residual Analysis")
        generate_placeholder_plot(OUTPUT_DIR / "qq_plot.png", "QQ-Plot")
        generate_placeholder_plot(OUTPUT_DIR / "residuals_vs_fitted.png", "Residuals vs Fitted")
        return

    if len(residuals) < 2:
        logger.warning("Not enough residuals data. Generating placeholder plots.")
        generate_placeholder_plot(OUTPUT_DIR / "residuals.png", "Residual Analysis")
        generate_placeholder_plot(OUTPUT_DIR / "qq_plot.png", "QQ-Plot")
        generate_placeholder_plot(OUTPUT_DIR / "residuals_vs_fitted.png", "Residuals vs Fitted")
        return

    # Generate plots
    plot_residual_histogram(residuals, OUTPUT_DIR / "residuals.png")
    plot_qq_plot(residuals, OUTPUT_DIR / "qq_plot.png")

    # For residuals vs fitted, try to get fitted values
    if "fitted" in residuals_data.columns:
        fitted = residuals_data["fitted"].dropna().values
        # Align with residuals
        valid_idx = residuals_data["fitted"].notna() & residuals_data["residuals"].notna()
        if valid_idx.sum() >= 2:
            plot_residuals_vs_fitted(
                residuals_data.loc[valid_idx, "fitted"].values,
                residuals_data.loc[valid_idx, "residuals"].values,
                OUTPUT_DIR / "residuals_vs_fitted.png",
            )
        else:
            generate_placeholder_plot(OUTPUT_DIR / "residuals_vs_fitted.png", "Residuals vs Fitted")
    else:
        generate_placeholder_plot(OUTPUT_DIR / "residuals_vs_fitted.png", "Residuals vs Fitted")


def main() -> None:
    """Main entry point for visualization module.

    Reads analysis results and generates residual diagnostic plots
    if the gate status is PASS.
    """
    logger.info("Starting visualization module (T033)")

    # Check gate status
    gate_passed, reason = check_gate_status()
    if not gate_passed:
        logger.warning(f"Gate failed: {reason}. Skipping plot generation.")
        # Still generate placeholder plots for documentation
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        generate_placeholder_plot(OUTPUT_DIR / "residuals.png", "Residual Analysis")
        generate_placeholder_plot(OUTPUT_DIR / "qq_plot.png", "QQ-Plot")
        return

    # Check statistical gate
    stat_gate_passed, stat_reason = check_statistical_gate()
    if not stat_gate_passed:
        logger.warning(f"Statistical gate failed: {stat_reason}. Skipping plot generation.")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        generate_placeholder_plot(OUTPUT_DIR / "residuals.png", "Residual Analysis")
        generate_placeholder_plot(OUTPUT_DIR / "qq_plot.png", "QQ-Plot")
        return

    # Load analysis results
    results = load_analysis_results()
    if not results or results.get("status") != "PASS":
        logger.warning("Analysis results not available or status not PASS. Skipping plot generation.")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        generate_placeholder_plot(OUTPUT_DIR / "residuals.png", "Residual Analysis")
        generate_placeholder_plot(OUTPUT_DIR / "qq_plot.png", "QQ-Plot")
        return

    # Generate residual diagnostic plots
    generate_residual_diagnostic_plots()

    # Generate correlation scatter plots if data is available
    if "data" in results:
        generate_correlation_scatter_plots(results)

    logger.info("Visualization module completed successfully")


if __name__ == "__main__":
    main()