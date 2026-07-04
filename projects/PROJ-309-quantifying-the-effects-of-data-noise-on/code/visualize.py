import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Iterable
import numpy as np

# Import from existing project modules
from utils.io import export_csv, write_json_artifact
from utils.plotting import set_plot_style, plot_error_vs_snr, plot_threshold_marker, save_figure
from config import get_snr_levels

def generate_error_vs_snr_plot(
    data: List[Dict[str, Any]],
    output_path: str,
    title: str = "Metric Error vs. SNR",
    marker_threshold: float = 50.0
) -> str:
    """
    Generate a line plot of metric error (%) vs. SNR (dB) for all metrics.
    
    This function plots the error rates for Correlation Dimension, Lyapunov Exponent,
    and FNN against SNR levels. It also marks the critical threshold where FNN
    error exceeds the specified percentage (default 50%).
    
    Args:
        data: List of dictionaries containing SNR, metric_name, error_percent.
        output_path: Path to save the generated figure (e.g., 'data/results/error_vs_snr.png').
        title: Title for the plot.
        marker_threshold: The error percentage threshold to mark on the FNN curve.
    
    Returns:
        The path to the saved figure.
    """
    # Group data by metric
    metrics_data = {}
    fnn_snr_points = []
    
    for row in data:
        metric_name = row.get('metric_name')
        snr = float(row.get('SNR_dB', 0))
        error = float(row.get('error_percent', 0))
        noise_type = row.get('noise_type', 'Gaussian')
        
        key = f"{metric_name}_{noise_type}"
        if key not in metrics_data:
            metrics_data[key] = {'snr': [], 'error': [], 'noise_type': noise_type}
        
        metrics_data[key]['snr'].append(snr)
        metrics_data[key]['error'].append(error)
        
        # Collect FNN points for threshold detection
        if 'FNN' in metric_name:
            fnn_snr_points.append((snr, error))
    
    # Sort data by SNR for plotting
    for key in metrics_data:
        sorted_pairs = sorted(zip(metrics_data[key]['snr'], metrics_data[key]['error']))
        metrics_data[key]['snr'] = [p[0] for p in sorted_pairs]
        metrics_data[key]['error'] = [p[1] for p in sorted_pairs]
    
    # Determine critical threshold SNR for FNN
    critical_snr = None
    if fnn_snr_points:
        fnn_snr_points.sort(key=lambda x: x[0])
        for snr, error in fnn_snr_points:
            if error >= marker_threshold:
                critical_snr = snr
                break
    
    # Set plot style
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot each metric
    for key, values in metrics_data.items():
        label = key.replace('_', ' (') + ')'
        ax.plot(values['snr'], values['error'], marker='o', label=label, linewidth=2)
    
    # Mark critical threshold
    if critical_snr is not None:
        ax.axvline(x=critical_snr, color='red', linestyle='--', 
                   label=f'Critical Threshold (FNN > {marker_threshold}%)', alpha=0.7)
        ax.plot(critical_snr, marker_threshold, 'r*', markersize=20, label='50% FNN Point')
    else:
        # If no threshold reached, mark the max FNN point
        if fnn_snr_points:
            max_snr, max_error = max(fnn_snr_points, key=lambda x: x[1])
            ax.plot(max_snr, max_error, 'r*', markersize=20, label='Max FNN Point')

    ax.set_xlabel('SNR (dB)', fontsize=12)
    ax.set_ylabel('Error (%)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_xlim(left=min(get_snr_levels()) - 2)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_figure(fig, output_path)
    plt.close(fig)
    
    return output_path

def create_final_results_bundle(
    csv_path: str,
    plot_path: str,
    report_path: str,
    data: List[Dict[str, Any]],
    critical_snr: Optional[float] = None
) -> str:
    """
    Create a bundle of final results including CSV, plot, and a JSON report.
    
    Args:
        csv_path: Path to the metrics summary CSV.
        plot_path: Path to the generated error vs SNR plot.
        report_path: Path to save the JSON report.
        data: The raw data used for the plot.
        critical_snr: The identified critical SNR threshold.
    
    Returns:
        Path to the saved JSON report.
    """
    report = {
        "status": "completed",
        "artifacts": {
            "csv": csv_path,
            "plot": plot_path
        },
        "summary": {
            "total_records": len(data),
            "critical_threshold_snr_db": critical_snr,
            "description": "Error vs SNR analysis with critical threshold marker"
        }
    }
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    write_json_artifact(report, report_path)
    return report_path

def export_metric_results_to_csv(
    data: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Export metric results to a CSV file.
    
    Args:
        data: List of dictionaries with metric results.
        output_path: Path to save the CSV file.
    
    Returns:
        Path to the saved CSV file.
    """
    if not data:
        raise ValueError("No data provided for CSV export")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    export_csv(data, output_path)
    return output_path

def generate_metric_convergence_plot(
    data: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Generate a plot showing metric convergence over SNR levels.
    
    Args:
        data: List of dictionaries with metric results.
        output_path: Path to save the figure.
    
    Returns:
        Path to the saved figure.
    """
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Group by metric
    metrics = {}
    for row in data:
        metric = row['metric_name']
        snr = float(row['SNR_dB'])
        value = float(row.get('computed_value', 0))
        
        if metric not in metrics:
            metrics[metric] = {'snr': [], 'value': []}
        metrics[metric]['snr'].append(snr)
        metrics[metric]['value'].append(value)
    
    for metric, values in metrics.items():
        sorted_pairs = sorted(zip(values['snr'], values['value']))
        snrs = [p[0] for p in sorted_pairs]
        vals = [p[1] for p in sorted_pairs]
        ax.plot(snrs, vals, marker='o', label=metric)
    
    ax.set_xlabel('SNR (dB)')
    ax.set_ylabel('Metric Value')
    ax.set_title('Metric Convergence vs SNR')
    ax.legend()
    ax.grid(True, linestyle=':', alpha=0.6)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_figure(fig, output_path)
    plt.close(fig)
    return output_path

def get_visualization_functions() -> List[str]:
    """Return list of available visualization functions."""
    return [
        "export_metric_results_to_csv",
        "generate_error_vs_snr_plot",
        "generate_metric_convergence_plot",
        "create_final_results_bundle"
    ]