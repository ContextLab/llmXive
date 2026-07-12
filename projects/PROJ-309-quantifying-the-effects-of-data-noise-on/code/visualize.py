import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Iterable

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# Apply a consistent scientific style
mpl.rcParams['figure.figsize'] = (10, 6)
mpl.rcParams['font.size'] = 10
mpl.rcParams['axes.grid'] = True
mpl.rcParams['axes.axisbelow'] = True
mpl.rcParams['grid.linestyle'] = '--'
mpl.rcParams['grid.alpha'] = 0.5

def set_plot_style(style: str = 'seaborn-v0_8-whitegrid'):
    """
    Apply a consistent matplotlib style to all plots.
    
    Args:
        style: Matplotlib style string.
    """
    try:
        plt.style.use(style)
    except Exception:
        # Fallback if specific seaborn version not available
        plt.style.use('seaborn-whitegrid')

def save_figure(fig: plt.Figure, path: Union[str, Path], dpi: int = 300):
    """
    Save a matplotlib figure to disk.
    
    Args:
        fig: The figure to save.
        path: Output file path.
        dpi: Resolution for the saved figure.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)

def plot_error_vs_snr(
    data: List[Dict[str, Any]],
    metric_name: str,
    output_path: Union[str, Path],
    title: Optional[str] = None,
    critical_threshold: Optional[float] = None
) -> plt.Figure:
    """
    Plot error percentage vs SNR for a specific metric.
    
    Args:
        data: List of dictionaries containing SNR, error, and noise_type keys.
        metric_name: Name of the metric to plot (used for filtering and labeling).
        output_path: Path to save the figure.
        title: Optional custom title.
        critical_threshold: Optional SNR value to mark as a vertical line.
    
    Returns:
        The matplotlib Figure object.
    """
    set_plot_style()
    fig, ax = plt.subplots()
    
    # Filter data for the specific metric
    metric_data = [d for d in data if d.get('metric_name') == metric_name]
    
    if not metric_data:
        raise ValueError(f"No data found for metric: {metric_name}")
    
    # Group by noise type for distinct lines
    noise_types = sorted(list(set(d.get('noise_type', 'unknown') for d in metric_data)))
    colors = plt.cm.tab10(np.linspace(0, 1, len(noise_types)))
    
    for i, noise_type in enumerate(noise_types):
        subset = [d for d in metric_data if d.get('noise_type') == noise_type]
        # Sort by SNR for plotting
        subset.sort(key=lambda x: float(x.get('snr_db', 0)))
        
        snrs = [float(d['snr_db']) for d in subset]
        errors = [float(d.get('error_percent', 0)) for d in subset]
        
        ax.plot(snrs, errors, marker='o', label=noise_type, color=colors[i], linewidth=2)
    
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel(f"Error (%) - {metric_name}")
    if title:
        ax.set_title(title)
    else:
        ax.set_title(f"{metric_name} Error vs SNR")
    
    ax.legend(loc='best')
    
    # Mark critical threshold if provided
    if critical_threshold is not None:
        ax.axvline(x=critical_threshold, color='red', linestyle='--', 
                   label=f"Critical Threshold ({critical_threshold} dB)")
        ax.text(critical_threshold + 1, ax.get_ylim()[1] * 0.9, 
                "Critical", color='red', fontsize=10, rotation=90)
    
    # Invert x-axis if standard convention (low SNR on right) or keep standard
    # Standard scientific convention: Low SNR (bad) on left, High SNR (good) on right
    # But often noise plots show degradation as noise increases (SNR decreases).
    # We will keep standard ascending SNR.
    
    save_figure(fig, output_path)
    return fig

def plot_metric_convergence(
    data: List[Dict[str, Any]],
    metric_name: str,
    output_path: Union[str, Path],
    ground_truth: Optional[float] = None
) -> plt.Figure:
    """
    Plot the computed metric value vs SNR to show convergence to ground truth.
    
    Args:
        data: List of dictionaries containing SNR, computed_value, and noise_type.
        metric_name: Name of the metric.
        output_path: Path to save the figure.
        ground_truth: Optional ground truth value to plot as a horizontal line.
    
    Returns:
        The matplotlib Figure object.
    """
    set_plot_style()
    fig, ax = plt.subplots()
    
    metric_data = [d for d in data if d.get('metric_name') == metric_name]
    if not metric_data:
        raise ValueError(f"No data found for metric: {metric_name}")
    
    noise_types = sorted(list(set(d.get('noise_type', 'unknown') for d in metric_data)))
    colors = plt.cm.tab10(np.linspace(0, 1, len(noise_types)))
    
    for i, noise_type in enumerate(noise_types):
        subset = [d for d in metric_data if d.get('noise_type') == noise_type]
        subset.sort(key=lambda x: float(x.get('snr_db', 0)))
        
        snrs = [float(d['snr_db']) for d in subset]
        values = [float(d.get('computed_value', 0)) for d in subset]
        
        ax.plot(snrs, values, marker='s', label=noise_type, color=colors[i], linewidth=2)
    
    if ground_truth is not None:
        ax.axhline(y=ground_truth, color='black', linestyle='-', 
                   label=f"Ground Truth ({ground_truth:.4f})", linewidth=2)
    
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel(f"Computed Value - {metric_name}")
    ax.set_title(f"{metric_name} Convergence vs SNR")
    ax.legend(loc='best')
    
    save_figure(fig, output_path)
    return fig

def plot_threshold_marker(
    data: List[Dict[str, Any]],
    threshold_snr: float,
    output_path: Union[str, Path],
    metric_name: str = "FNN"
) -> plt.Figure:
    """
    Plot a specific visualization highlighting the critical threshold for FNN.
    
    Args:
        data: List of data dictionaries.
        threshold_snr: The SNR value identified as critical.
        output_path: Path to save the figure.
        metric_name: The metric being analyzed (default FNN).
    
    Returns:
        The matplotlib Figure object.
    """
    # Reuse error_vs_snr logic but focus on the threshold annotation
    fig = plot_error_vs_snr(data, metric_name, output_path, 
                            title=f"Critical Threshold Identification: {metric_name}",
                            critical_threshold=threshold_snr)
    return fig

def export_metric_results_to_csv(
    results: List[Dict[str, Any]],
    output_path: Union[str, Path],
    columns: Optional[List[str]] = None
) -> Path:
    """
    Export metric results to a CSV file.
    
    Args:
        results: List of dictionaries containing result data.
        output_path: Path to the output CSV file.
        columns: Optional list of columns to include. Defaults to all keys found.
    
    Returns:
        The path to the created CSV file.
    """
    if not results:
        raise ValueError("No results to export.")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine columns if not provided
    if columns is None:
        columns = list(results[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)
    
    return output_path

def generate_error_vs_snr_plot(
    input_data_path: Union[str, Path],
    output_plot_path: Union[str, Path],
    metrics: List[str] = None,
    critical_thresholds: Dict[str, float] = None
) -> List[Path]:
    """
    Main entry point to generate error vs SNR plots for multiple metrics.
    Reads from a summary CSV and generates individual plots.
    
    Args:
        input_data_path: Path to the input CSV (e.g., metrics_summary.csv).
        output_plot_path: Directory to save plots.
        metrics: List of metric names to plot. Defaults to common metrics.
        critical_thresholds: Dict mapping metric name to critical SNR threshold.
    
    Returns:
        List of paths to generated plot files.
    """
    metrics = metrics or ["Correlation Dimension", "Lyapunov Exponent", "FNN"]
    critical_thresholds = critical_thresholds or {}
    
    # Load data
    input_path = Path(input_data_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    output_dir = Path(output_plot_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for metric in metrics:
        # Determine threshold for this metric
        threshold = critical_thresholds.get(metric)
        
        # Construct output filename
        safe_metric_name = metric.replace(" ", "_").replace("/", "_")
        plot_file = output_dir / f"error_vs_snr_{safe_metric_name}.png"
        
        try:
            plot_error_vs_snr(
                data=data,
                metric_name=metric,
                output_path=plot_file,
                title=f"{metric} Error vs SNR",
                critical_threshold=threshold
            )
            generated_files.append(plot_file)
        except Exception as e:
            # Log but continue if a specific metric fails (e.g., no data)
            import logging
            logging.warning(f"Failed to generate plot for {metric}: {e}")
    
    return generated_files

def generate_metric_convergence_plots(
    input_data_path: Union[str, Path],
    output_plot_path: Union[str, Path],
    ground_truths: Dict[str, float],
    metrics: List[str] = None
) -> List[Path]:
    """
    Generate convergence plots for metrics against ground truth.
    
    Args:
        input_data_path: Path to input CSV.
        output_plot_path: Directory for output plots.
        ground_truths: Dict mapping metric name to ground truth value.
        metrics: List of metrics to plot.
    
    Returns:
        List of paths to generated plots.
    """
    metrics = metrics or list(ground_truths.keys())
    output_dir = Path(output_plot_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    data = []
    with open(Path(input_data_path), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    generated_files = []
    for metric in metrics:
        if metric not in ground_truths:
            continue
        
        safe_name = metric.replace(" ", "_").replace("/", "_")
        plot_file = output_dir / f"convergence_{safe_name}.png"
        
        try:
            plot_metric_convergence(
                data=data,
                metric_name=metric,
                output_path=plot_file,
                ground_truth=ground_truths[metric]
            )
            generated_files.append(plot_file)
        except Exception as e:
            import logging
            logging.warning(f"Failed to generate convergence plot for {metric}: {e}")
    
    return generated_files

def create_final_results_bundle(
    csv_path: Union[str, Path],
    plots_dir: Union[str, Path],
    output_bundle_dir: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Assemble the final results bundle (CSV, plots, metadata).
    
    Args:
        csv_path: Path to the summary CSV.
        plots_dir: Directory containing generated plots.
        output_bundle_dir: Destination directory for the bundle.
        metadata: Optional metadata dict to include in a JSON sidecar.
    
    Returns:
        Path to the output bundle directory.
    """
    bundle_path = Path(output_bundle_dir)
    bundle_path.mkdir(parents=True, exist_ok=True)
    
    # Copy CSV
    src_csv = Path(csv_path)
    if src_csv.exists():
        dest_csv = bundle_path / src_csv.name
        dest_csv.write_bytes(src_csv.read_bytes())
    
    # Copy plots
    src_plots = Path(plots_dir)
    if src_plots.exists():
        for plot_file in src_plots.glob("*.png"):
            dest_plot = bundle_path / plot_file.name
            dest_plot.write_bytes(plot_file.read_bytes())
    
    # Write metadata
    if metadata:
        meta_path = bundle_path / "metadata.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    return bundle_path

def get_visualization_functions() -> Dict[str, callable]:
    """
    Returns a dictionary of public visualization functions for external use.
    """
    return {
        'plot_error_vs_snr': plot_error_vs_snr,
        'plot_metric_convergence': plot_metric_convergence,
        'export_metric_results_to_csv': export_metric_results_to_csv,
        'generate_error_vs_snr_plot': generate_error_vs_snr_plot,
        'generate_metric_convergence_plots': generate_metric_convergence_plots,
        'create_final_results_bundle': create_final_results_bundle,
        'save_figure': save_figure
    }