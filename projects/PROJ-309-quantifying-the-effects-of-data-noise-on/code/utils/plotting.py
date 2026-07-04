import os
from typing import Any, Dict, List, Optional, Tuple, Union
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes

# Configure plot style for scientific publication
def set_plot_style():
    """Set a consistent, publication-ready plot style."""
    mpl.rcParams['font.family'] = 'serif'
    mpl.rcParams['font.serif'] = ['Times New Roman']
    mpl.rcParams['font.size'] = 12
    mpl.rcParams['axes.labelsize'] = 12
    mpl.rcParams['axes.titlesize'] = 14
    mpl.rcParams['legend.fontsize'] = 10
    mpl.rcParams['figure.figsize'] = (10, 6)
    mpl.rcParams['figure.dpi'] = 150
    mpl.rcParams['savefig.dpi'] = 300
    mpl.rcParams['savefig.bbox'] = 'tight'
    mpl.rcParams['axes.grid'] = True
    mpl.rcParams['grid.alpha'] = 0.3
    mpl.rcParams['grid.linestyle'] = '--'

def plot_error_vs_snr(
    snr_levels: List[float],
    errors: Dict[str, List[float]],
    metric_names: List[str],
    output_path: str
) -> None:
    """
    Plot error vs SNR for multiple metrics.

    Args:
        snr_levels: List of SNR values in dB.
        errors: Dictionary mapping metric name to list of errors.
        metric_names: List of metric names to plot.
        output_path: Path to save the figure.
    """
    set_plot_style()
    fig, ax = plt.subplots()

    colors = ['tab:blue', 'tab:orange', 'tab:green']
    markers = ['o', 's', '^']

    for i, metric in enumerate(metric_names):
        if metric in errors:
            ax.plot(
                snr_levels,
                errors[metric],
                marker=markers[i % len(markers)],
                color=colors[i % len(colors)],
                label=metric.replace('_', ' ').title(),
                linewidth=2,
                markersize=8
            )

    ax.set_xlabel('SNR (dB)')
    ax.set_ylabel('Relative Error (%)')
    ax.set_title('Metric Error vs Signal-to-Noise Ratio')
    ax.legend(loc='best')
    ax.set_xlim(min(snr_levels) - 1, max(snr_levels) + 1)
    ax.set_ylim(0, max(max(errors[m]) for m in errors if errors[m]) * 1.1 if errors else 100)

    save_figure(fig, output_path)
    plt.close(fig)

def plot_threshold_marker(
    snr_levels: List[float],
    fnn_errors: List[float],
    threshold_value: float,
    critical_snr: float,
    output_path: str
) -> None:
    """
    Plot FNN error with critical threshold marker.

    Args:
        snr_levels: List of SNR values.
        fnn_errors: List of FNN error values.
        threshold_value: The error threshold defining criticality (e.g., 50%).
        critical_snr: The SNR at which the threshold is crossed.
        output_path: Path to save the figure.
    """
    set_plot_style()
    fig, ax = plt.subplots()

    ax.plot(snr_levels, fnn_errors, marker='o', color='tab:red', label='FNN Error', linewidth=2)
    ax.axhline(y=threshold_value, color='gray', linestyle='--', label=f'Threshold ({threshold_value}%)')
    ax.axvline(x=critical_snr, color='green', linestyle=':', label=f'Critical SNR ({critical_snr:.1f} dB)')

    ax.set_xlabel('SNR (dB)')
    ax.set_ylabel('FNN Error (%)')
    ax.set_title('Critical Threshold Identification')
    ax.legend(loc='best')

    save_figure(fig, output_path)
    plt.close(fig)

def plot_metric_convergence(
    snr_levels: List[float],
    metric_values: Dict[str, List[float]],
    ground_truth: Dict[str, float],
    output_path: str
) -> None:
    """
    Plot metric values vs SNR with ground truth reference.

    Args:
        snr_levels: List of SNR values.
        metric_values: Dictionary mapping metric name to list of values.
        ground_truth: Dictionary mapping metric name to ground truth value.
        output_path: Path to save the figure.
    """
    set_plot_style()
    fig, axes = plt.subplots(1, len(metric_values), figsize=(15, 5))
    if len(metric_values) == 1:
        axes = [axes]

    colors = ['tab:blue', 'tab:orange', 'tab:green']

    for i, metric in enumerate(metric_values):
        ax = axes[i]
        ax.plot(snr_levels, metric_values[metric], marker='o', color=colors[i % len(colors)], label='Computed')
        if metric in ground_truth:
            ax.axhline(y=ground_truth[metric], color='gray', linestyle='--', label=f'Ground Truth ({ground_truth[metric]:.4f})')
        
        ax.set_xlabel('SNR (dB)')
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.set_title(metric.replace('_', ' ').title())
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

    save_figure(fig, output_path)
    plt.close(fig)

def save_figure(fig: plt.Figure, output_path: str) -> None:
    """
    Save a matplotlib figure to disk.

    Args:
        fig: The figure to save.
        output_path: The path to save the file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
