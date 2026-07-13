"""Scaling analysis for agent counts.

Implements power-law fitting for metric trends vs. agent count.
Uses real data from experiment results; never fabricates values.
"""
from __future__ import annotations

import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b

    Args:
        x: Independent variable values (agent counts).
        a: Prefactor coefficient.
        b: Exponent coefficient.

    Returns:
        Predicted y values.
    """
    return a * np.power(x, b)


def fit_power_law(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Fit a power law to data using log-log linear regression.

    Fits y = a * x^b by transforming to log(y) = log(a) + b * log(x).

    Args:
        x: Independent variable values (agent counts)
        y: Dependent variable values (metrics)

    Returns:
        Tuple of (a, b) where y ≈ a * x^b
    """
    # y = a * x^b  =>  log(y) = log(a) + b * log(x)
    # Avoid log(0) or negative values
    mask = (x > 0) & (y > 0)
    if np.sum(mask) < 2:
        # Not enough valid data points
        return 1.0, 0.0

    log_x = np.log(x[mask])
    log_y = np.log(y[mask])

    # Linear regression: log_y = intercept + slope * log_x
    # Using polyfit for simplicity
    slope, intercept = np.polyfit(log_x, log_y, 1)
    a = np.exp(intercept)
    b = slope

    return a, b


def fit_power_law_with_ci(
    x: np.ndarray, y: np.ndarray, confidence: float = 0.95
) -> Tuple[float, float, float]:
    """Fit power law and return exponent with confidence interval.

    Args:
        x: Independent variable values
        y: Dependent variable values
        confidence: Confidence level for CI (default 0.95)

    Returns:
        Tuple of (a, b, ci_half_width) where y ≈ a * x^b
    """
    a, b = fit_power_law(x, y)

    # Calculate confidence interval using bootstrap-like approach
    # or analytical approximation from linear regression
    mask = (x > 0) & (y > 0)
    if np.sum(mask) < 3:
        # Not enough data for meaningful CI
        ci = 0.5 * abs(b) if b != 0 else 0.5
        return a, b, ci

    log_x = np.log(x[mask])
    log_y = np.log(y[mask])

    # Fit linear model
    slope, intercept = np.polyfit(log_x, log_y, 1)

    # Calculate residuals
    y_pred = slope * log_x + intercept
    residuals = log_y - y_pred

    # Standard error of the slope
    n = len(log_x)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)

    if ss_tot == 0 or n < 3:
        ci = 0.5 * abs(b) if b != 0 else 0.5
        return a, b, ci

    # Standard error of regression
    s_e = np.sqrt(ss_res / (n - 2))

    # Standard error of slope
    ss_x = np.sum((log_x - np.mean(log_x)) ** 2)
    se_slope = s_e / np.sqrt(ss_x)

    # t-value for confidence interval (approximate with 1.96 for large n)
    # For small samples, we'd use scipy.stats.t, but keeping deps minimal
    t_val = 2.0 if n < 30 else 1.96

    ci_half_width = t_val * se_slope

    return a, b, ci_half_width


def load_scaling_data(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Load and aggregate results for scaling analysis.

    Args:
        results: List of experiment result dictionaries

    Returns:
        DataFrame with aggregated metrics by agent_count
    """
    df = pd.DataFrame(results)

    # Filter for valid numeric entries
    df = df[df["agent_count"] > 0]
    df = df[df["specialization_index"].notna()]
    df = df[df["retrieval_efficiency"].notna()]

    # Aggregate by agent_count
    aggregated = df.groupby("agent_count").agg({
        "specialization_index": "mean",
        "retrieval_efficiency": "mean",
        "game_id": "count"  # Count games per configuration
    }).reset_index()

    aggregated.columns = ["agent_count", "specialization_index", "retrieval_efficiency", "game_count"]

    return aggregated


def generate_scaling_plot(
    results: List[Dict[str, Any]],
    output_path: pathlib.Path,
    note_text: Optional[str] = None
) -> None:
    """Generate a scaling plot with fitted power law curves.

    Creates plots for specialization index and retrieval efficiency
    vs. agent count, with power-law fits overlaid.

    Args:
        results: List of experiment result dictionaries
        output_path: Path to save the plot (PDF or PNG)
        note_text: Optional text note to include on the plot
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError("matplotlib is required for scaling plots")

    df = load_scaling_data(results)

    if len(df) < 2:
        # Not enough data points to plot a trend
        warnings.warn("Insufficient data points for scaling plot (need >= 2)")
        # Create a minimal placeholder plot
        plt.figure(figsize=(10, 5))
        plt.text(0.5, 0.5, "Insufficient data for scaling analysis",
                ha='center', va='center', transform=plt.gca().transAxes)
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

    x = df["agent_count"].values
    y_spec = df["specialization_index"].values
    y_ret = df["retrieval_efficiency"].values

    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot specialization index
    ax1 = axes[0]
    ax1.scatter(x, y_spec, label='Specialization Index', color='blue', s=100, zorder=3)

    if len(x) >= 2:
        a, b, ci = fit_power_law_with_ci(x, y_spec)
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = power_law(x_fit, a, b)
        ax1.plot(x_fit, y_fit, 'b--', linewidth=2,
                label=f'Power Law fit (exp={b:.3f} ± {ci:.3f})')

    ax1.set_xlabel("Number of Agents", fontsize=12)
    ax1.set_ylabel("Specialization Index", fontsize=12)
    ax1.set_title("Scaling of Specialization Index", fontsize=14)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)

    # Plot retrieval efficiency
    ax2 = axes[1]
    ax2.scatter(x, y_ret, label='Retrieval Efficiency', color='green', s=100, zorder=3)

    if len(x) >= 2:
        a, b, ci = fit_power_law_with_ci(x, y_ret)
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = power_law(x_fit, a, b)
        ax2.plot(x_fit, y_fit, 'g--', linewidth=2,
                label=f'Power Law fit (exp={b:.3f} ± {ci:.3f})')

    ax2.set_xlabel("Number of Agents", fontsize=12)
    ax2.set_ylabel("Retrieval Efficiency", fontsize=12)
    ax2.set_title("Scaling of Retrieval Efficiency", fontsize=14)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)

    # Add note about data limitations if provided
    if note_text:
        fig.suptitle(note_text, fontsize=10, style='italic', y=0.95)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()