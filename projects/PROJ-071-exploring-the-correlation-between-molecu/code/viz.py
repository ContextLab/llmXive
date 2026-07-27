"""Visualization module for molecular complexity and degradation analysis.

Generates scatter plots, residual diagnostics, and handles both successful
analysis and data insufficiency scenarios.
"""
import json
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import seaborn as sns

from scipy import stats

# Ensure output directory exists
OUTPUT_DIR = Path("data/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_data_path(filename: str) -> Path:
    """Get the full path for a data file."""
    return Path("data") / filename

def check_gate_status() -> Dict[str, Any]:
    """Read the gate status from the JSON file."""
    gate_path = Path("data/gate_status.json")
    if not gate_path.exists():
        return {"status": "FAIL", "reason": "Gate status file not found", "N": 0}
    with open(gate_path, "r") as f:
        return json.load(f)

def load_analysis_results() -> Optional[Dict[str, Any]]:
    """Load analysis results from JSON."""
    path = Path("data/processed/analysis_results.json")
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)

def load_residuals_data() -> Optional[pd.DataFrame]:
    """Load residuals data for plotting."""
    # Residuals are typically part of the analysis results or a separate file
    # For this implementation, we'll construct them from analysis_results if available
    results = load_analysis_results()
    if results and "residuals" in results:
        return pd.DataFrame(results["residuals"])
    return None

def plot_scatter_with_regression(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    output_path: Path,
    is_placeholder: bool = False
) -> None:
    """Create a scatter plot with a regression line."""
    plt.figure(figsize=(10, 8))

    if is_placeholder:
        # Generate synthetic data for placeholder
        np.random.seed(42)
        x = np.random.normal(0, 1, 50)
        y = 0.5 * x + np.random.normal(0, 0.2, 50)

    sns.scatterplot(x=x, y=y, alpha=0.7, edgecolor="k")

    if not is_placeholder:
        # Fit regression line
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        x_line = np.linspace(min(x), max(x), 100)
        y_line = slope * x_line + intercept
        plt.plot(x_line, y_line, 'r-', label=f'Regression (R²={r_value**2:.3f})')
        plt.text(0.05, 0.95, f'p-value: {p_value:.4f}', transform=plt.gca().transAxes)
    else:
        # Placeholder regression
        slope, intercept = 0.5, 0.0
        x_line = np.linspace(min(x), max(x), 100)
        y_line = slope * x_line + intercept
        plt.plot(x_line, y_line, 'r--', label='Placeholder Regression')

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)

    if is_placeholder:
        plt.figtext(0.5, 0.02, "Placeholder - Insufficient Data",
                    ha='center', fontsize=10, style='italic', bbox=dict(facecolor='yellow', alpha=0.2))

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def generate_correlation_scatter_plots(
    features: List[str],
    target: str,
    data: pd.DataFrame,
    is_placeholder: bool = False
) -> List[Path]:
    """Generate scatter plots for top correlated features."""
    output_paths = []
    for feature in features:
        if feature not in data.columns or target not in data.columns:
            continue

        x = data[feature].values
        y = data[target].values

        # Remove NaNs
        mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[mask]
        y_clean = y[mask]

        if len(x_clean) < 3:
            continue

        output_path = OUTPUT_DIR / f"scatter_{feature}_vs_{target}.png"
        plot_scatter_with_regression(
            x_clean, y_clean,
            feature, target,
            f"{feature} vs {target}",
            output_path,
            is_placeholder=is_placeholder
        )
        output_paths.append(output_path)

    return output_paths

def plot_residual_histogram(
    residuals: np.ndarray,
    output_path: Path,
    is_placeholder: bool = False
) -> None:
    """Plot histogram of residuals."""
    plt.figure(figsize=(10, 6))

    if is_placeholder:
        np.random.seed(42)
        residuals = np.random.normal(0, 1, 100)

    sns.histplot(residuals, kde=True, bins=20, color='skyblue', edgecolor='black')

    plt.axvline(x=0, color='r', linestyle='--', linewidth=2)
    plt.xlabel('Residuals')
    plt.ylabel('Frequency')
    plt.title('Distribution of Residuals')

    if is_placeholder:
        plt.figtext(0.5, 0.02, "Placeholder - Insufficient Data",
                    ha='center', fontsize=10, style='italic', bbox=dict(facecolor='yellow', alpha=0.2))

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def plot_qq_plot(
    residuals: np.ndarray,
    output_path: Path,
    is_placeholder: bool = False
) -> None:
    """Create a Q-Q plot of residuals."""
    plt.figure(figsize=(8, 8))

    if is_placeholder:
        np.random.seed(42)
        residuals = np.random.normal(0, 1, 100)

    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title('Q-Q Plot of Residuals')

    if is_placeholder:
        plt.figtext(0.5, 0.02, "Placeholder - Insufficient Data",
                    ha='center', fontsize=10, style='italic', bbox=dict(facecolor='yellow', alpha=0.2))

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def plot_residuals_vs_fitted(
    fitted: np.ndarray,
    residuals: np.ndarray,
    output_path: Path,
    is_placeholder: bool = False
) -> None:
    """Plot residuals vs fitted values."""
    plt.figure(figsize=(10, 6))

    if is_placeholder:
        np.random.seed(42)
        fitted = np.linspace(-2, 2, 100)
        residuals = np.random.normal(0, 0.5, 100)

    plt.scatter(fitted, residuals, alpha=0.7, edgecolor='k')
    plt.axhline(y=0, color='r', linestyle='--', linewidth=2)
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted Values')

    if is_placeholder:
        plt.figtext(0.5, 0.02, "Placeholder - Insufficient Data",
                    ha='center', fontsize=10, style='italic', bbox=dict(facecolor='yellow', alpha=0.2))

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def generate_residual_diagnostic_plots(
    residuals: Optional[np.ndarray] = None,
    fitted: Optional[np.ndarray] = None,
    is_placeholder: bool = False
) -> List[Path]:
    """Generate all residual diagnostic plots."""
    output_paths = []

    if is_placeholder or residuals is None:
        np.random.seed(42)
        residuals = np.random.normal(0, 1, 100)

    if fitted is None:
        fitted = np.linspace(-2, 2, len(residuals))

    # Histogram
    hist_path = OUTPUT_DIR / "residuals_histogram.png"
    plot_residual_histogram(residuals, hist_path, is_placeholder=is_placeholder)
    output_paths.append(hist_path)

    # Q-Q Plot
    qq_path = OUTPUT_DIR / "qq_plot.png"
    plot_qq_plot(residuals, qq_path, is_placeholder=is_placeholder)
    output_paths.append(qq_path)

    # Residuals vs Fitted
    fitted_path = OUTPUT_DIR / "residuals_vs_fitted.png"
    plot_residuals_vs_fitted(fitted, residuals, fitted_path, is_placeholder=is_placeholder)
    output_paths.append(fitted_path)

    return output_paths

def main() -> None:
    """Main entry point for visualization tasks."""
    gate_status = check_gate_status()
    is_gate_passed = gate_status.get("status") == "PASS" and gate_status.get("N", 0) >= 30

    if not is_gate_passed:
        print("Data Availability Gate failed. Generating placeholder diagnostic plots.")
        # Generate placeholder plots as required by T033b
        generate_residual_diagnostic_plots(is_placeholder=True)
        print("Placeholder diagnostic plots generated in data/outputs/")
        return

    # If gate passed, load real data and generate real plots
    # (This path is handled by T033, but we ensure it works here too)
    results = load_analysis_results()
    if not results:
        print("No analysis results found. Cannot generate real plots.")
        return

    residuals = np.array(results.get("residuals", []))
    fitted = np.array(results.get("fitted_values", []))

    if len(residuals) == 0:
        print("No residuals found in analysis results.")
        return

    generate_residual_diagnostic_plots(residuals, fitted, is_placeholder=False)
    print("Real diagnostic plots generated in data/outputs/")

if __name__ == "__main__":
    main()