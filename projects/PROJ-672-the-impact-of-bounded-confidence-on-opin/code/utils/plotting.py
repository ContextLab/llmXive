"""
Plotting utilities for the bounded confidence opinion dynamics project.

This module provides functions to generate:
1. Log-log convergence plots (Convergence Time vs. Epsilon)
2. Regression scatter plots (Scaling Exponent gamma vs. Structural Metrics)
3. Critical threshold detection visualizations
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Ensure non-interactive backend for server-side generation
matplotlib.use('Agg')

def plot_convergence_loglog(
    data: List[Dict],
    output_path: str,
    title: str = "Convergence Time vs. Confidence Threshold (Log-Log)",
    xlabel: str = r"$\epsilon$ (Confidence Threshold)",
    ylabel: str = "Convergence Time (Iterations)"
) -> str:
    """
    Generate a log-log plot of convergence time vs. epsilon.
    
    Args:
        data: List of dictionaries containing 'epsilon' and 'convergence_time' keys.
        output_path: Path to save the plot (e.g., 'figures/convergence_loglog.png').
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        
    Returns:
        The absolute path to the saved figure.
    """
    if not data:
        raise ValueError("Data list is empty. Cannot generate plot.")

    epsilons = []
    times = []
    
    for entry in data:
        eps = entry.get('epsilon')
        t = entry.get('convergence_time')
        if eps is not None and t is not None and t > 0:
            epsilons.append(eps)
            times.append(t)

    if not epsilons:
        raise ValueError("No valid data points found for plotting.")

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sort by epsilon for consistent line plotting if desired, 
    # but scatter is often better for raw simulation results
    # Here we use scatter to show distribution, then optionally a trend line
    ax.scatter(epsilons, times, alpha=0.6, color='blue', label='Simulation Data')
    
    # Log-log scale
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", ls="--", alpha=0.5)
    
    # Add a trend line for visual reference if enough points
    if len(epsilons) > 1:
        # Fit a line in log-log space: log(y) = m * log(x) + c
        # This corresponds to a power law y = A * x^m
        log_eps = np.log(epsilons)
        log_times = np.log(times)
        coeffs = np.polyfit(log_eps, log_times, 1)
        fit_fn = np.poly1d(coeffs)
        
        # Generate smooth line for plotting
        x_fit = np.linspace(min(epsilons), max(epsilons), 100)
        y_fit = np.exp(fit_fn(np.log(x_fit)))
        
        ax.plot(x_fit, y_fit, 'r-', linewidth=2, label='Power Law Fit')
        ax.legend()

    plt.tight_layout()
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    return os.path.abspath(output_path)


def plot_regression_scatter(
    x_values: List[Union[int, float]],
    y_values: List[Union[int, float]],
    output_path: str,
    x_label: str = "Metric",
    y_label: str = r"$\gamma$ (Scaling Exponent)",
    title: str = "Regression Analysis: Structural Metric vs. Scaling Exponent",
    regression_line: bool = True
) -> str:
    """
    Generate a scatter plot with optional linear regression line.
    
    Args:
        x_values: List of x-axis values (e.g., Assortativity, Path Length).
        y_values: List of y-axis values (e.g., gamma scaling exponents).
        output_path: Path to save the plot.
        x_label: X-axis label.
        y_label: Y-axis label.
        title: Plot title.
        regression_line: If True, fit and plot a linear regression line.
        
    Returns:
        The absolute path to the saved figure.
    """
    if len(x_values) != len(y_values):
        raise ValueError("x_values and y_values must have the same length.")
    if len(x_values) == 0:
        raise ValueError("Data lists are empty.")

    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.scatter(x_values, y_values, alpha=0.7, color='darkgreen', edgecolors='k', label='Data Points')
    
    if regression_line and len(x_values) >= 2:
        x_arr = np.array(x_values)
        y_arr = np.array(y_values)
        
        # Linear regression
        slope, intercept = np.polyfit(x_arr, y_arr, 1)
        x_fit = np.linspace(min(x_arr), max(x_arr), 100)
        y_fit = slope * x_fit + intercept
        
        ax.plot(x_fit, y_fit, 'r--', linewidth=2, label=f'Linear Fit (slope={slope:.3f})')
        
        # Calculate R^2
        y_pred = slope * x_arr + intercept
        ss_res = np.sum((y_arr - y_pred) ** 2)
        ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        ax.text(0.05, 0.95, f'$R^2 = {r_squared:.3f}$', transform=ax.transAxes,
                fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.legend()

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    return os.path.abspath(output_path)


def plot_critical_threshold_detection(
    convergence_trace: List[float],
    epsilon: float,
    output_path: str,
    threshold: float = 1e-4,
    title: str = "Critical Threshold Detection",
    x_label: str = "Iteration",
    y_label: str = "Max Opinion Change"
) -> str:
    """
    Plot the convergence trace to identify the critical threshold point.
    
    Args:
        convergence_trace: List of max opinion changes per iteration.
        epsilon: The confidence threshold used for this run.
        output_path: Path to save the plot.
        threshold: The convergence threshold (horizontal line).
        title: Plot title.
        x_label: X-axis label.
        y_label: Y-axis label.
        
    Returns:
        The absolute path to the saved figure.
    """
    if not convergence_trace:
        raise ValueError("Convergence trace is empty.")

    fig, ax = plt.subplots(figsize=(10, 6))
    
    iterations = range(1, len(convergence_trace) + 1)
    ax.semilogy(iterations, convergence_trace, 'b-', linewidth=1.5, label='Max Change')
    
    # Horizontal threshold line
    ax.axhline(y=threshold, color='r', linestyle='--', label=f'Convergence Threshold ({threshold})')
    
    # Mark the point where it crosses
    converged_idx = None
    for i, val in enumerate(convergence_trace):
        if val < threshold:
            converged_idx = i + 1
            break
    
    if converged_idx:
        ax.axvline(x=converged_idx, color='g', linestyle=':', label=f'Converged at Iter {converged_idx}')
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(f"{title} (ε = {epsilon:.2f})")
    ax.legend()
    ax.grid(True, which="both", ls="-", alpha=0.4)
    
    plt.tight_layout()
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    return os.path.abspath(output_path)


def main():
    """
    Main function to demonstrate plotting capabilities with synthetic data.
    This is for testing the module functionality.
    """
    # Create output directory
    output_dir = Path("data/processed/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Demo 1: Convergence Log-Log Plot
    print("Generating convergence log-log plot...")
    demo_data = [
        {"epsilon": 0.05, "convergence_time": 1500},
        {"epsilon": 0.10, "convergence_time": 800},
        {"epsilon": 0.15, "convergence_time": 450},
        {"epsilon": 0.20, "convergence_time": 200},
        {"epsilon": 0.25, "convergence_time": 120},
        {"epsilon": 0.30, "convergence_time": 85},
        {"epsilon": 0.35, "convergence_time": 60},
        {"epsilon": 0.40, "convergence_time": 45},
        {"epsilon": 0.45, "convergence_time": 35},
    ]
    plot_convergence_loglog(
        demo_data, 
        str(output_dir / "convergence_loglog_demo.png"),
        title="Demo: Convergence Time vs. Epsilon"
    )
    print(f"Saved: {output_dir / 'convergence_loglog_demo.png'}")
    
    # Demo 2: Regression Scatter Plot
    print("Generating regression scatter plot...")
    x_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    y_data = [2.1, 2.5, 2.9, 3.4, 3.8, 4.2, 4.7, 5.0]
    plot_regression_scatter(
        x_data,
        y_data,
        str(output_dir / "regression_scatter_demo.png"),
        x_label="Assortativity Coefficient",
        y_label=r"$\gamma$ (Scaling Exponent)",
        title="Demo: Assortativity vs. Scaling Exponent"
    )
    print(f"Saved: {output_dir / 'regression_scatter_demo.png'}")
    
    # Demo 3: Critical Threshold Detection
    print("Generating critical threshold detection plot...")
    trace = [1.0, 0.8, 0.5, 0.3, 0.1, 0.05, 0.02, 0.008, 0.003, 0.001, 0.0005, 0.0001, 0.00005]
    plot_critical_threshold_detection(
        trace,
        0.25,
        str(output_dir / "threshold_detection_demo.png"),
        threshold=1e-4,
        title="Demo: Convergence Trace"
    )
    print(f"Saved: {output_dir / 'threshold_detection_demo.png'}")
    
    print("All demo plots generated successfully.")


if __name__ == "__main__":
    main()