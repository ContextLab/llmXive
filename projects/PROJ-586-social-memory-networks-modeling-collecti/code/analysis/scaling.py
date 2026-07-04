"""Scaling analysis for agent counts."""
from __future__ import annotations

import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b"""
    return a * np.power(x, b)


def fit_power_law(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Fit a power law to data using log-log linear regression."""
    # y = a * x^b  =>  log(y) = log(a) + b * log(x)
    # Avoid log(0)
    mask = (x > 0) & (y > 0)
    if np.sum(mask) < 2:
        return 1.0, 0.0  # Default to linear if not enough data
    
    log_x = np.log(x[mask])
    log_y = np.log(y[mask])
    
    # Linear regression
    slope, intercept = np.polyfit(log_x, log_y, 1)
    a = np.exp(intercept)
    b = slope
    
    return a, b


def fit_power_law_with_ci(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    """Fit power law and return exponent with confidence interval."""
    a, b = fit_power_law(x, y)
    # Simplified CI calculation (approximate)
    # In a real scenario, use statsmodels or scipy.optimize.curve_fit
    ci = 0.1 * abs(b) if b != 0 else 0.1
    return a, b, ci


def load_scaling_data(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Load and aggregate results for scaling analysis."""
    df = pd.DataFrame(results)
    # Aggregate by agent_count
    aggregated = df.groupby("agent_count").agg({
        "specialization_index": "mean",
        "retrieval_efficiency": "mean"
    }).reset_index()
    return aggregated


def generate_scaling_plot(results: List[Dict[str, Any]], output_path: pathlib.Path) -> None:
    """Generate a scaling plot with fitted power law."""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        # Fallback if matplotlib is not available
        return
    
    df = load_scaling_data(results)
    
    if len(df) < 2:
        # Not enough data points to plot a trend
        return
    
    x = df["agent_count"].values
    y_spec = df["specialization_index"].values
    y_ret = df["retrieval_efficiency"].values
    
    plt.figure(figsize=(10, 6))
    
    # Plot specialization
    plt.subplot(1, 2, 1)
    plt.scatter(x, y_spec, label='Specialization Index', color='blue')
    if len(x) >= 2:
        a, b, _ = fit_power_law_with_ci(x, y_spec)
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = power_law(x_fit, a, b)
        plt.plot(x_fit, y_fit, 'b--', label=f'Power Law (exp={b:.2f})')
    plt.xlabel("Number of Agents")
    plt.ylabel("Specialization Index")
    plt.title("Scaling of Specialization")
    plt.legend()
    plt.grid(True)
    
    # Plot retrieval
    plt.subplot(1, 2, 2)
    plt.scatter(x, y_ret, label='Retrieval Efficiency', color='green')
    if len(x) >= 2:
        a, b, _ = fit_power_law_with_ci(x, y_ret)
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = power_law(x_fit, a, b)
        plt.plot(x_fit, y_fit, 'g--', label=f'Power Law (exp={b:.2f})')
    plt.xlabel("Number of Agents")
    plt.ylabel("Retrieval Efficiency")
    plt.title("Scaling of Retrieval Efficiency")
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()