"""
Scaling Analysis Module.

Implements power-law fitting for metric trends vs. agent count.
Note: Fitting a power law to only 3 points (N=3,5,7) is statistically
weak. This module includes a warning note in the generated report.
"""
from __future__ import annotations

import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b"""
    return a * np.power(x, b)

def fit_power_law(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float]:
    """
    Fit a power law y = a * x^b using log-log linear regression.
    
    Returns (a, b).
    """
    if len(x) < 2:
        raise ValueError("Need at least 2 points to fit power law")
        
    # Log transform
    log_x = np.log(x)
    log_y = np.log(y)
    
    # Linear regression
    coeffs = np.polyfit(log_x, log_y, 1)
    b = coeffs[0]
    a = np.exp(coeffs[1])
    
    return a, b

def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    confidence: float = 0.95
) -> Dict[str, Any]:
    """
    Fit power law and return parameters with confidence intervals.
    
    WARNING: With only 3 data points, confidence intervals are extremely wide
    and should be interpreted with caution.
    """
    if len(x) < 3:
        warnings.warn(
            "Fitting power law to fewer than 3 points. "
            "Results are statistically unreliable."
        )
    
    a, b = fit_power_law(x, y)
    
    # Estimate uncertainty (simplified)
    # In a real analysis, we would use bootstrapping or MCMC
    n = len(x)
    if n > 2:
        # Approximate standard error of slope
        log_x = np.log(x)
        log_y = np.log(y)
        residuals = log_y - (b * log_x + np.log(a))
        mse = np.sum(residuals**2) / (n - 2)
        se_b = np.sqrt(mse / np.sum((log_x - np.mean(log_x))**2))
        
        # 95% CI for b
        ci_b = 1.96 * se_b
    else:
        ci_b = float('inf')
        
    return {
        "a": a,
        "b": b,
        "ci_b": ci_b,
        "n_points": n,
        "warning": "Low data points (N=3) limit power-law reliability."
    }

def load_scaling_data(path: pathlib.Path) -> pd.DataFrame:
    """Load scaling data from CSV."""
    return pd.read_csv(path)

def generate_scaling_plot(
    df: pd.DataFrame,
    output_path: pathlib.Path,
    metric: str = "specialization_index"
) -> None:
    """
    Generate a scaling plot with fitted power-law curve.
    
    Includes an explicit note about the limitation of 3 data points.
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for CI
    import matplotlib.pyplot as plt

    # Aggregate by agent count
    grouped = df.groupby("agent_count")[metric].mean().reset_index()
    x = grouped["agent_count"].values.astype(float)
    y = grouped[metric].values.astype(float)

    # Fit power law
    try:
        fit_result = fit_power_law_with_ci(x, y)
        a, b = fit_result["a"], fit_result["b"]
        warning_msg = fit_result.get("warning", "")
    except Exception as e:
        a, b = 1.0, 0.0
        warning_msg = f"Fit failed: {e}"

    # Create plot
    plt.figure(figsize=(10, 6))
    
    # Plot data points
    plt.scatter(x, y, s=100, color='blue', label='Observed Mean', zorder=5)
    
    # Plot fitted curve
    x_fit = np.linspace(min(x), max(x), 100)
    y_fit = power_law(x_fit, a, b)
    plt.plot(x_fit, y_fit, 'r--', label=f'Power Law Fit (y = {a:.3f} * x^{b:.3f})')
    
    plt.xlabel("Number of Agents (N)")
    plt.ylabel(metric.replace('_', ' ').title())
    plt.title(f"Scaling of {metric.replace('_', ' ').title()} vs. Agent Count")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Add warning note
    note_text = (
        "NOTE: Scaling plot includes an explicit note that "
        "3 data points limit power-law reliability."
    )
    plt.text(
        0.02, 0.02, note_text,
        transform=plt.gca().transAxes,
        fontsize=9,
        verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    print(f"Scaling plot saved to {output_path}")
    print(f"Power law exponent (b): {b:.4f}")
    if warning_msg:
        print(f"WARNING: {warning_msg}")