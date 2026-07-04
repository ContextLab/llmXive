"""
Visualization module for plotting error vs SNR and critical thresholds.
"""
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
import csv
from pathlib import Path
import json

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

from utils.plotting import (
    set_plot_style,
    plot_error_vs_snr,
    plot_threshold_marker,
    plot_metric_convergence,
    save_figure
)
from utils.io import export_csv, write_json_artifact

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def export_metric_results_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export metric results to a CSV file.

    Args:
        results: List of dictionaries containing metric results.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.warning("No results to export.")
        return

    # Flatten the results for CSV export
    rows = []
    for res in results:
        row = {
            'snr_db': res.get('snr_db'),
            'noise_type': res.get('noise_type'),
            'metric_name': res.get('metric_name'),
            'computed_value': res.get('computed_value'),
            'ground_truth_value': res.get('ground_truth_value'),
            'error_percent': res.get('error_percent')
        }
        rows.append(row)

    export_csv(rows, output_path)
    logger.info(f"Exported {len(rows)} rows to {output_path}")


def generate_error_vs_snr_plot(
    results: List[Dict[str, Any]],
    output_path: str,
    threshold_snr: Optional[float] = None,
    threshold_metric: str = 'FNN',
    threshold_error: float = 50.0
) -> None:
    """
    Generate a line plot of error vs SNR with an optional critical threshold marker.

    Args:
        results: List of dictionaries containing metric results.
        output_path: Path to save the plot.
        threshold_snr: Optional SNR value to mark as critical threshold.
        threshold_metric: The metric to use for threshold detection (default 'FNN').
        threshold_error: The error percentage considered critical (default 50%).
    """
    if not results:
        logger.error("No results provided for plotting.")
        raise ValueError("Results list cannot be empty.")

    set_plot_style()

    # Group results by metric and noise type
    metrics = {}
    for res in results:
        metric_name = res['metric_name']
        noise_type = res['noise_type']
        key = (metric_name, noise_type)
        if key not in metrics:
            metrics[key] = {'snr': [], 'error': []}
        metrics[key]['snr'].append(res['snr_db'])
        metrics[key]['error'].append(res['error_percent'])

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = plt.cm.tab10(np.linspace(0, 1, len(metrics)))
    color_idx = 0

    critical_point = None

    for (metric_name, noise_type), data in metrics.items():
        snr_vals = sorted(data['snr'])
        error_vals = [data['error'][data['snr'].index(s)] for s in snr_vals]

        label = f"{metric_name} ({noise_type})"
        ax.plot(snr_vals, error_vals, marker='o', label=label, color=colors[color_idx])
        color_idx += 1

        # Check for critical threshold if this is the FNN metric
        if metric_name == threshold_metric and threshold_snr is None:
            for s, e in zip(snr_vals, error_vals):
                if e >= threshold_error:
                    critical_point = (s, e)
                    break

    ax.set_xlabel('SNR (dB)')
    ax.set_ylabel('Error (%)')
    ax.set_title('Metric Error vs SNR')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)

    # Plot critical threshold marker if identified
    if threshold_snr is not None:
        # Use provided threshold
        ax.axvline(x=threshold_snr, color='r', linestyle='--', linewidth=2, label=f'Critical Threshold ({threshold_snr} dB)')
        # Find the point on the FNN curve closest to this threshold
        if (threshold_metric, 'Gaussian') in metrics:
            snr_vals = metrics[(threshold_metric, 'Gaussian')]['snr']
            error_vals = metrics[(threshold_metric, 'Gaussian')]['error']
            if threshold_snr in snr_vals:
                idx = snr_vals.index(threshold_snr)
                ax.plot(threshold_snr, error_vals[idx], 'ro', markersize=10, label='Critical Point')
    elif critical_point:
        # Use detected threshold
        ax.axvline(x=critical_point[0], color='r', linestyle='--', linewidth=2, label=f'Critical Threshold ({critical_point[0]} dB)')
        ax.plot(critical_point[0], critical_point[1], 'ro', markersize=10, label='Critical Point')

    plt.tight_layout()
    save_figure(fig, output_path)
    plt.close()
    logger.info(f"Saved error vs SNR plot to {output_path}")


def generate_critical_threshold_report(
    results: List[Dict[str, Any]],
    output_path: str,
    threshold_metric: str = 'FNN',
    threshold_error: float = 50.0
) -> Dict[str, Any]:
    """
    Identify and report the critical SNR threshold where a metric exceeds a certain error.

    Args:
        results: List of dictionaries containing metric results.
        output_path: Path to save the JSON report.
        threshold_metric: The metric to analyze for the threshold.
        threshold_error: The error percentage threshold.

    Returns:
        Dictionary containing the report data.
    """
    # Filter for the specific metric
    fnn_results = [r for r in results if r['metric_name'] == threshold_metric]

    if not fnn_results:
        logger.warning(f"No results found for metric {threshold_metric}.")
        report = {
            'metric': threshold_metric,
            'threshold_error_percent': threshold_error,
            'critical_snr_db': None,
            'critical_error_percent': None,
            'message': f"No data found for {threshold_metric}."
        }
        write_json_artifact(report, output_path)
        return report

    # Group by noise type and find the first SNR where error >= threshold
    critical_data = {}
    for noise_type in set(r['noise_type'] for r in fnn_results):
        type_results = [r for r in fnn_results if r['noise_type'] == noise_type]
        type_results.sort(key=lambda x: x['snr_db'])

        critical_snr = None
        critical_error = None

        for res in type_results:
            if res['error_percent'] >= threshold_error:
                critical_snr = res['snr_db']
                critical_error = res['error_percent']
                break

        critical_data[noise_type] = {
            'critical_snr_db': critical_snr,
            'critical_error_percent': critical_error
        }

    # Determine overall critical SNR (lowest among noise types)
    valid_snr = [v['critical_snr_db'] for v in critical_data.values() if v['critical_snr_db'] is not None]
    overall_critical_snr = min(valid_snr) if valid_snr else None

    report = {
        'metric': threshold_metric,
        'threshold_error_percent': threshold_error,
        'critical_snr_db': overall_critical_snr,
        'by_noise_type': critical_data,
        'message': f"Critical threshold identified at {overall_critical_snr} dB for {threshold_metric} error >= {threshold_error}%." if overall_critical_snr is not None else "No critical threshold identified."
    }

    write_json_artifact(report, output_path)
    logger.info(f"Saved critical threshold report to {output_path}")
    return report


def run_visualization_pipeline(
    metrics_csv_path: str,
    output_dir: str,
    plot_filename: str = 'error_vs_snr.png',
    report_filename: str = 'critical_threshold_report.json'
) -> None:
    """
    Run the full visualization pipeline: load metrics, generate plots, and reports.

    Args:
        metrics_csv_path: Path to the CSV file containing metric results.
        output_dir: Directory to save outputs.
        plot_filename: Filename for the error vs SNR plot.
        report_filename: Filename for the critical threshold report.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load metrics from CSV
    logger.info(f"Loading metrics from {metrics_csv_path}")
    if not os.path.exists(metrics_csv_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_csv_path}")

    results = []
    with open(metrics_csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'snr_db': float(row['snr_db']),
                'noise_type': row['noise_type'],
                'metric_name': row['metric_name'],
                'computed_value': float(row['computed_value']),
                'ground_truth_value': float(row['ground_truth_value']),
                'error_percent': float(row['error_percent'])
            })

    # Generate plot
    plot_path = output_dir / plot_filename
    generate_error_vs_snr_plot(results, str(plot_path))

    # Generate report
    report_path = output_dir / report_filename
    generate_critical_threshold_report(results, str(report_path))

    logger.info("Visualization pipeline completed successfully.")