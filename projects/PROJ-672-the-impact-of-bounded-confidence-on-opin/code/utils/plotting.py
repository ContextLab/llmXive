"""
Plotting utilities for the bounded confidence opinion dynamics project.
"""
import os
from pathlib import Path
from typing import Dict, List, Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Ensure non-interactive backend
matplotlib.use('Agg')

def plot_convergence_loglog(
    data: List[Dict],
    output_path: str,
    title: str = "Convergence Time vs. Confidence Threshold (Log-Log)",
    xlabel: str = r"$\epsilon$ (Confidence Threshold)",
    ylabel: str = "Convergence Time (Iterations)"
) -> str:
    if not data:
        raise ValueError("Data list is empty.")

    epsilons = [e['epsilon'] for e in data if e.get('epsilon') is not None and e.get('convergence_time', 0) > 0]
    times = [e['convergence_time'] for e in data if e.get('epsilon') is not None and e.get('convergence_time', 0) > 0]

    if not epsilons:
        raise ValueError("No valid data points found.")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(epsilons, times, alpha=0.6, color='blue', label='Simulation Data')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", ls="--", alpha=0.5)
    
    if len(epsilons) > 1:
        log_eps = np.log(epsilons)
        log_times = np.log(times)
        coeffs = np.polyfit(log_eps, log_times, 1)
        fit_fn = np.poly1d(coeffs)
        x_fit = np.linspace(min(epsilons), max(epsilons), 100)
        y_fit = np.exp(fit_fn(np.log(x_fit)))
        ax.plot(x_fit, y_fit, 'r-', linewidth=2, label='Power Law Fit')
        ax.legend()

    plt.tight_layout()
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
    title: str = "Regression Analysis",
    regression_line: bool = True
) -> str:
    if len(x_values) != len(y_values) or not x_values:
        raise ValueError("Invalid data lengths.")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(x_values, y_values, alpha=0.7, color='darkgreen', edgecolors='k', label='Data Points')
    
    if regression_line and len(x_values) >= 2:
        x_arr, y_arr = np.array(x_values), np.array(y_values)
        slope, intercept = np.polyfit(x_arr, y_arr, 1)
        x_fit = np.linspace(min(x_arr), max(x_arr), 100)
        y_fit = slope * x_fit + intercept
        ax.plot(x_fit, y_fit, 'r--', linewidth=2, label=f'Linear Fit (slope={slope:.3f})')
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
    if not convergence_trace:
        raise ValueError("Trace is empty.")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogy(range(1, len(convergence_trace) + 1), convergence_trace, 'b-', linewidth=1.5, label='Max Change')
    ax.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold ({threshold})')
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
    output_dir = Path("data/processed/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_convergence_loglog([{"epsilon": 0.1, "convergence_time": 100}], str(output_dir / "test_loglog.png"))
    plot_regression_scatter([1, 2], [1, 2], str(output_dir / "test_reg.png"))
    plot_critical_threshold_detection([0.1, 0.01, 0.0001], 0.2, str(output_dir / "test_trace.png"))

if __name__ == "__main__":
    main()
