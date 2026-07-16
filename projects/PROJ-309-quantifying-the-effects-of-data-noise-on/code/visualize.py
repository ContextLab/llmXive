"""
Visualization and export module for the noise effects analysis pipeline.
Implements FR-009 (Plotting) and FR-010 (CSV Export).
"""
import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Iterable
import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm as cm
from matplotlib.axes import Axes

# Configure matplotlib backend if not interactive
if not plt.isinteractive():
    mpl.use('Agg')

# Import from local utils
from utils.io import export_csv, write_json_artifact
from config import get_snr_levels, get_system_params, NoiseType

# --------------------------------------------------------------------------
# Style Configuration
# --------------------------------------------------------------------------

def set_plot_style() -> None:
    """
    Apply a consistent style to all plots.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.size'] = 12
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['savefig.bbox'] = 'tight'
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['legend.fontsize'] = 12

# --------------------------------------------------------------------------
# CSV Export Logic (FR-010)
# --------------------------------------------------------------------------

def export_metric_results_to_csv(
    results: List[Dict[str, Any]],
    output_path: str,
    fieldnames: Optional[List[str]] = None
) -> None:
    """
    Export metric results to a CSV file.

    Args:
        results: List of result dictionaries.
        output_path: Path to the output CSV file.
        fieldnames: Optional list of column names.
    """
    if fieldnames is None:
        # Standard order for consistency
        fieldnames = [
            "SNR_dB", "noise_type", "system_type", "metric_name",
            "computed_value", "ground_truth_value", "error_percent"
        ]
    export_csv(results, output_path, fieldnames)

def generate_error_vs_snr_plot_from_files(
    input_csv_path: str,
    output_plot_path: str,
    critical_threshold_snr: Optional[float] = None
) -> None:
    """
    Generate the Error-vs-SNR lookup table visualization from a CSV file.

    Args:
        input_csv_path: Path to the input CSV file containing error data.
        output_plot_path: Path to save the output plot.
        critical_threshold_snr: Optional SNR value to mark as a critical threshold.
    """
    set_plot_style()

    # Load data
    data = []
    with open(input_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    if not data:
        raise ValueError(f"No data found in {input_csv_path}")

    # Parse numeric fields
    snr_levels = sorted(list(set(float(row['SNR_dB']) for row in data)))
    metrics = sorted(list(set(row['metric_name'] for row in data)))
    noise_types = sorted(list(set(row['noise_type'] for row in data)))

    # Prepare plot
    fig, ax = plt.subplots(figsize=(12, 8))

    colors = plt.cm.tab10(np.linspace(0, 1, len(metrics)))
    markers = ['o', 's', '^', 'D', 'x']

    # Plot lines for each metric and noise type combination
    for i, metric in enumerate(metrics):
        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]

        for j, noise_type in enumerate(noise_types):
            snr_vals = []
            error_vals = []

            for row in data:
                if row['metric_name'] == metric and row['noise_type'] == noise_type:
                    snr_vals.append(float(row['SNR_dB']))
                    error_vals.append(float(row['error_percent']))

            if snr_vals:
                # Sort by SNR for plotting
                sorted_pairs = sorted(zip(snr_vals, error_vals))
                snr_sorted, err_sorted = zip(*sorted_pairs)
                label = f"{metric} ({noise_type})"
                ax.plot(snr_sorted, err_sorted, marker=marker, label=label,
                        color=color, linewidth=2, markersize=8)

    # Mark critical threshold if provided
    if critical_threshold_snr is not None:
        ax.axvline(x=critical_threshold_snr, color='red', linestyle='--',
                   linewidth=2, label=f'Critical Threshold ({critical_threshold_snr} dB)')
        ax.text(critical_threshold_snr, ax.get_ylim()[1] * 0.9,
                f'Critical: {critical_threshold_snr} dB',
                color='red', fontsize=12, ha='right', va='top')

    ax.set_xlabel("Signal-to-Noise Ratio (dB)")
    ax.set_ylabel("Error Percentage (%)")
    ax.set_title("Metric Error vs. Signal-to-Noise Ratio")
    ax.legend(loc='best')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_xscale('linear') # SNR levels are linear in dB

    # Ensure output directory exists
    Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_plot_path)
    plt.close(fig)

# --------------------------------------------------------------------------
# Plotting Logic (FR-009)
# --------------------------------------------------------------------------

def generate_error_vs_snr_plot(
    data: List[Dict[str, Any]],
    output_path: str,
    critical_threshold_snr: Optional[float] = None
) -> None:
    """
    Generate a plot of metric error vs SNR from in-memory data.

    Args:
        data: List of dictionaries containing SNR, metric, and error data.
        output_path: Path to save the plot.
        critical_threshold_snr: Optional SNR to mark as critical.
    """
    set_plot_style()

    # Group data
    metrics = sorted(list(set(d['metric_name'] for d in data)))
    noise_types = sorted(list(set(d['noise_type'] for d in data)))

    fig, ax = plt.subplots(figsize=(12, 8))

    colors = plt.cm.tab10(np.linspace(0, 1, len(metrics)))
    markers = ['o', 's', '^', 'D', 'x']

    for i, metric in enumerate(metrics):
        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]

        for j, noise_type in enumerate(noise_types):
            # Filter and sort
            subset = [d for d in data if d['metric_name'] == metric and d['noise_type'] == noise_type]
            if not subset:
                continue

            subset_sorted = sorted(subset, key=lambda x: float(x['SNR_dB']))
            snrs = [float(d['SNR_dB']) for d in subset_sorted]
            errors = [float(d['error_percent']) for d in subset_sorted]

            label = f"{metric} ({noise_type})"
            ax.plot(snrs, errors, marker=marker, label=label,
                    color=color, linewidth=2, markersize=8)

    if critical_threshold_snr is not None:
        ax.axvline(x=critical_threshold_snr, color='red', linestyle='--',
                   linewidth=2, label=f'Critical Threshold ({critical_threshold_snr} dB)')
        ax.text(critical_threshold_snr, ax.get_ylim()[1] * 0.9,
                f'Critical: {critical_threshold_snr} dB',
                color='red', fontsize=12, ha='right', va='top')

    ax.set_xlabel("Signal-to-Noise Ratio (dB)")
    ax.set_ylabel("Error Percentage (%)")
    ax.set_title("Metric Error vs. Signal-to-Noise Ratio")
    ax.legend(loc='best')
    ax.grid(True, linestyle='--', alpha=0.7)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close(fig)

def generate_metric_convergence_plots(
    data: List[Dict[str, Any]],
    output_dir: str
) -> None:
    """
    Generate individual convergence plots for each metric.

    Args:
        data: List of result dictionaries.
        output_dir: Directory to save plots.
    """
    set_plot_style()
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    metrics = sorted(list(set(d['metric_name'] for d in data)))

    for metric in metrics:
        subset = [d for d in data if d['metric_name'] == metric]
        if not subset:
            continue

        noise_types = sorted(list(set(d['noise_type'] for d in subset)))

        fig, ax = plt.subplots(figsize=(10, 6))

        for i, noise_type in enumerate(noise_types):
            snrs = []
            errors = []
            for d in subset:
                if d['noise_type'] == noise_type:
                    snrs.append(float(d['SNR_dB']))
                    errors.append(float(d['error_percent']))

            if snrs:
                snrs_sorted, errors_sorted = zip(*sorted(zip(snrs, errors)))
                ax.plot(snrs_sorted, errors_sorted, marker='o', label=noise_type, linewidth=2)

        ax.set_xlabel("SNR (dB)")
        ax.set_ylabel("Error (%)")
        ax.set_title(f"{metric} Error vs SNR")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.7)

        plot_path = Path(output_dir) / f"{metric.replace(' ', '_')}_convergence.png"
        plt.savefig(plot_path)
        plt.close(fig)

def plot_threshold_marker(
    snr_threshold: float,
    metric_name: str,
    output_path: str
) -> None:
    """
    Create a simple plot highlighting a critical threshold.

    Args:
        snr_threshold: The SNR value of the threshold.
        metric_name: Name of the metric associated with the threshold.
        output_path: Path to save the plot.
    """
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    # Mock data range for visualization context
    snrs = np.linspace(-10, 40, 50)
    # Simulate a degradation curve
    errors = 100 * np.exp(-0.1 * snrs)
    errors = errors + np.random.normal(0, 5, size=snrs.shape) # Add noise

    ax.plot(snrs, errors, label="Simulated Error Curve", color='blue', alpha=0.6)
    ax.axvline(x=snr_threshold, color='red', linestyle='--', linewidth=2,
               label=f'Critical Threshold ({snr_threshold} dB)')

    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("Error (%)")
    ax.set_title(f"Critical Threshold for {metric_name}")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close(fig)

# --------------------------------------------------------------------------
# Pipeline Orchestrator for Visualization
# --------------------------------------------------------------------------

def create_final_results_bundle(
    error_csv_path: str,
    output_dir: str,
    critical_threshold_report: Optional[Dict[str, Any]] = None
) -> None:
    """
    Orchestrates the creation of all final visualization artifacts.

    Args:
        error_csv_path: Path to the error_vs_snr.csv file.
        output_dir: Directory to save all results.
        critical_threshold_report: Optional dict with threshold details.
    """
    set_plot_style()
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 1. Generate main error plot
    main_plot_path = Path(output_dir) / "error_vs_snr.png"
    critical_snr = None
    if critical_threshold_report and 'threshold_snr' in critical_threshold_report:
        critical_snr = critical_threshold_report['threshold_snr']

    generate_error_vs_snr_plot_from_files(
        input_csv_path=error_csv_path,
        output_plot_path=str(main_plot_path),
        critical_threshold_snr=critical_snr
    )

    # 2. Generate individual metric plots
    # We need to load data to split by metric
    data = []
    with open(error_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    if data:
        metrics_dir = Path(output_dir) / "metric_convergence"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        generate_metric_convergence_plots(data, str(metrics_dir))

    # 3. Save final bundle metadata if threshold report exists
    if critical_threshold_report:
        bundle_meta = {
            "generated_at": str(Path(output_dir).absolute()),
            "input_csv": error_csv_path,
            "critical_threshold": critical_threshold_report
        }
        write_json_artifact(bundle_meta, str(Path(output_dir) / "bundle_metadata.json"))

def get_visualization_functions() -> List[str]:
    """
    Returns a list of public function names in this module.
    """
    return [
        "set_plot_style",
        "export_metric_results_to_csv",
        "generate_error_vs_snr_plot",
        "generate_metric_convergence_plots",
        "plot_threshold_marker",
        "generate_error_vs_snr_plot_from_files",
        "create_final_results_bundle"
    ]