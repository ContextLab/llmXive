"""
Scaling Analysis Module.

Implements power-law fitting for metric trends vs. agent count.
Note: Fitting a power law to only 3 points (N=3,5,7) is statistically
weak. This module includes a warning note in the generated report.

This module is designed to be tolerant of various input shapes and 
does not raise errors on missing or malformed data, instead returning
safe defaults or warnings.
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
    
    If data is insufficient or invalid, returns (1.0, 0.0) and logs a warning.
    """
    if len(x) < 2 or len(y) < 2:
        warnings.warn("Need at least 2 points to fit power law. Returning default.")
        return 1.0, 0.0
        
    # Ensure no zeros or negatives in log transform
    x_clean = x[x > 0]
    y_clean = y[y > 0]
    
    if len(x_clean) < 2:
        warnings.warn("Insufficient positive data points for log transform. Returning default.")
        return 1.0, 0.0

    # Log transform
    log_x = np.log(x_clean)
    log_y = np.log(y_clean)
    
    # Linear regression
    try:
        coeffs = np.polyfit(log_x, log_y, 1)
        b = coeffs[0]
        a = np.exp(coeffs[1])
    except (np.linalg.LinAlgError, ValueError) as e:
        warnings.warn(f"Regression failed: {e}. Returning default.")
        return 1.0, 0.0
    
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
    
    Returns a dictionary with 'a', 'b', 'ci_b', 'n_points', and 'warning'.
    """
    if len(x) < 3:
        warnings.warn(
            "Fitting power law to fewer than 3 points. "
            "Results are statistically unreliable."
        )
    
    a, b = fit_power_law(x, y)
    
    # If we got the default fallback, return early with appropriate warning
    if a == 1.0 and b == 0.0:
        return {
            "a": a,
            "b": b,
            "ci_b": float('inf'),
            "n_points": len(x),
            "warning": "Fit failed or insufficient data. Results are unreliable."
        }
    
    # Estimate uncertainty (simplified)
    # In a real analysis, we would use bootstrapping or MCMC
    n = len(x)
    x_clean = x[x > 0]
    y_clean = y[y > 0]
    
    if n > 2:
        # Approximate standard error of slope
        log_x = np.log(x_clean)
        log_y = np.log(y_clean)
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
    if not path.exists():
        warnings.warn(f"Scaling data file not found: {path}. Returning empty DataFrame.")
        return pd.DataFrame(columns=["agent_count", "specialization_index", "retrieval_efficiency"])
    return pd.read_csv(path)

def generate_scaling_plot(
    df: pd.DataFrame,
    output_path: pathlib.Path,
    metric: str = "specialization_index"
) -> None:
    """
    Generate a scaling plot with fitted power-law curve.
    
    Includes an explicit note about the limitation of 3 data points.
    The plot is saved to the specified output path.
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for CI
    import matplotlib.pyplot as plt

    if df.empty:
        warnings.warn("No data to plot. Creating an empty plot with warning.")
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No data available", ha='center', va='center', transform=plt.gca().transAxes)
        plt.title(f"Scaling of {metric.replace('_', ' ').title()} vs. Agent Count (No Data)")
        plt.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

    # Aggregate by agent count
    if metric not in df.columns:
        warnings.warn(f"Metric '{metric}' not found in DataFrame. Available: {list(df.columns)}")
        metric = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    grouped = df.groupby("agent_count")[metric].mean().reset_index()
    
    if grouped.empty:
        warnings.warn("No grouped data available after aggregation.")
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No grouped data available", ha='center', va='center', transform=plt.gca().transAxes)
        plt.title(f"Scaling of {metric.replace('_', ' ').title()} vs. Agent Count (No Data)")
        plt.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

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
    if len(x) > 0:
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    print(f"Scaling plot saved to {output_path}")
    print(f"Power law exponent (b): {b:.4f}")
    if warning_msg:
        print(f"WARNING: {warning_msg}")