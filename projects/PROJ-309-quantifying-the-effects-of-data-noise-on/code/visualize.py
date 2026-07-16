import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Iterable
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from code.utils.io import export_csv
from code.utils.plotting import set_plot_style, plot_error_vs_snr, save_figure

def set_plot_style():
    """Apply consistent matplotlib style settings."""
    set_plot_style()

def export_metric_results_to_csv(
    results: List[Dict[str, Any]],
    output_path: str,
    fieldnames: Optional[List[str]] = None
) -> None:
    """
    Export metric results to a CSV file.

    Args:
        results: List of dictionaries containing metric results.
        output_path: Path to the output CSV file.
        fieldnames: Optional list of column names. If None, keys from the first
                    dictionary are used.
    """
    if not results:
        raise ValueError("No results to export")

    if fieldnames is None:
        # Ensure standard column order as per T034 spec
        standard_cols = [
            "SNR_dB", "noise_type", "metric_name",
            "computed_value", "ground_truth_value", "error_percent"
        ]
        # Filter to only available keys in the first result, preserving order
        available_keys = list(results[0].keys())
        fieldnames = [col for col in standard_cols if col in available_keys]
        # Append any remaining keys not in standard list
        fieldnames.extend([k for k in available_keys if k not in fieldnames])

    export_csv(results, output_path, fieldnames)

def generate_error_vs_snr_plot_from_files(
    input_csv_path: str,
    output_plot_path: str,
    critical_threshold_snr: Optional[float] = None
) -> None:
    """
    Generate an error vs SNR plot from a CSV file.

    Args:
        input_csv_path: Path to the input CSV file containing error data.
        output_plot_path: Path where the plot will be saved.
        critical_threshold_snr: Optional SNR value to mark as critical threshold.
    """
    data = []
    with open(input_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    if not data:
        raise ValueError("No data found in input CSV file")

    # Convert data to numpy arrays for plotting
    snr_levels = sorted(list(set(float(row['SNR_dB']) for row in data)))
    
    metrics = list(set(row['metric_name'] for row in data))
    
    plot_data = {}
    for metric in metrics:
        metric_data = []
        for snr in snr_levels:
            matching_rows = [r for r in data if float(r['SNR_dB']) == snr and r['metric_name'] == metric]
            if matching_rows:
                # Average error if multiple entries (e.g. different seeds)
                avg_error = np.mean([float(r['error_percent']) for r in matching_rows])
                metric_data.append(avg_error)
            else:
                metric_data.append(np.nan)
        plot_data[metric] = metric_data

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(metrics)))
    for idx, metric in enumerate(metrics):
        ax.plot(snr_levels, plot_data[metric], marker='o', label=metric, color=colors[idx])
    
    if critical_threshold_snr is not None:
        ax.axvline(x=critical_threshold_snr, color='red', linestyle='--', 
                   label=f'Critical Threshold ({critical_threshold_snr} dB)')
    
    ax.set_xlabel('SNR (dB)')
    ax.set_ylabel('Error (%)')
    ax.set_title('Metric Error vs Signal-to-Noise Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('linear')
    
    # Ensure output directory exists
    Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_error_vs_snr_plot(
    error_data: List[Dict[str, Any]],
    output_path: str,
    critical_threshold_snr: Optional[float] = None
) -> None:
    """
    Generate an error vs SNR plot from in-memory data.

    Args:
        error_data: List of dictionaries containing error data.
        output_path: Path where the plot will be saved.
        critical_threshold_snr: Optional SNR value to mark as critical threshold.
    """
    if not error_data:
        raise ValueError("No error data provided")

    snr_levels = sorted(list(set(float(row['SNR_dB']) for row in error_data)))
    metrics = list(set(row['metric_name'] for row in error_data))
    
    plot_data = {}
    for metric in metrics:
        metric_data = []
        for snr in snr_levels:
            matching_rows = [r for r in error_data if float(r['SNR_dB']) == snr and r['metric_name'] == metric]
            if matching_rows:
                avg_error = np.mean([float(r['error_percent']) for r in matching_rows])
                metric_data.append(avg_error)
            else:
                metric_data.append(np.nan)
        plot_data[metric] = metric_data

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, len(metrics)))
    for idx, metric in enumerate(metrics):
        ax.plot(snr_levels, plot_data[metric], marker='o', label=metric, color=colors[idx])
    
    if critical_threshold_snr is not None:
        ax.axvline(x=critical_threshold_snr, color='red', linestyle='--', 
                   label=f'Critical Threshold ({critical_threshold_snr} dB)')
    
    ax.set_xlabel('SNR (dB)')
    ax.set_ylabel('Error (%)')
    ax.set_title('Metric Error vs Signal-to-Noise Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_metric_convergence_plots(
    trajectory_data: Dict[str, Any],
    output_dir: str
) -> None:
    """
    Generate convergence plots for metric calculations.

    Args:
        trajectory_data: Dictionary containing trajectory and metric data.
        output_dir: Directory to save the plots.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    # Implementation would go here for specific convergence plots
    pass

def plot_threshold_marker(
    ax: plt.Axes,
    threshold_snr: float,
    label: str = "Critical Threshold"
) -> None:
    """
    Add a vertical marker for a critical threshold on an axis.

    Args:
        ax: Matplotlib axis to plot on.
        threshold_snr: SNR value for the threshold.
        label: Label for the threshold line.
    """
    ax.axvline(x=threshold_snr, color='red', linestyle='--', label=label)

def create_final_results_bundle(
    csv_path: str,
    plot_path: str,
    threshold_report_path: str,
    output_dir: str
) -> None:
    """
    Create a bundle of final results including CSV, plots, and reports.

    Args:
        csv_path: Path to the results CSV file.
        plot_path: Path to the results plot.
        threshold_report_path: Path to the critical threshold report JSON.
        output_dir: Directory to copy results to.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Copy files to output directory
    import shutil
    shutil.copy(csv_path, os.path.join(output_dir, os.path.basename(csv_path)))
    shutil.copy(plot_path, os.path.join(output_dir, os.path.basename(plot_path)))
    shutil.copy(threshold_report_path, os.path.join(output_dir, os.path.basename(threshold_report_path)))

def get_visualization_functions() -> List[str]:
    """Return list of available visualization function names."""
    return [
        "set_plot_style",
        "export_metric_results_to_csv",
        "generate_error_vs_snr_plot_from_files",
        "generate_error_vs_snr_plot",
        "generate_metric_convergence_plots",
        "plot_threshold_marker",
        "create_final_results_bundle"
    ]