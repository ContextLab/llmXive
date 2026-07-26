import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import from existing API surface
from network.connectivity import load_epochs_from_file, select_channels, calculate_coherence_matrix, save_connectivity_matrix
from network.metrics import compute_all_metrics, process_subject_metrics
from config import ensure_dirs, get_config_summary

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define density thresholds for sensitivity analysis
# Low: 10%, Medium: 20%, High: 30% of maximum possible edges
DENSITY_THRESHOLDS = [0.10, 0.20, 0.30]

def load_connectivity_matrices(processed_dir: Path) -> Dict[str, np.ndarray]:
    """
    Load all connectivity matrices from the processed directory.
    Returns a dict mapping participant_id to connectivity matrix (numpy array).
    """
    matrices = {}
    if not processed_dir.exists():
        raise FileNotFoundError(f"Processed directory not found: {processed_dir}")
    
    for file_path in processed_dir.glob("*.npy"):
        # Expecting filename format: participant_id_connectivity.npy
        participant_id = file_path.stem.replace('_connectivity', '')
        try:
            matrices[participant_id] = np.load(file_path)
            logger.info(f"Loaded connectivity matrix for {participant_id}: shape {matrices[participant_id].shape}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
    
    if not matrices:
        raise ValueError(f"No connectivity matrices found in {processed_dir}")
    
    return matrices

def threshold_connectivity_matrix(matrix: np.ndarray, density: float) -> np.ndarray:
    """
    Apply a density threshold to the connectivity matrix.
    Keeps only the top 'density' fraction of edges (by absolute value) for each node,
    ensuring a sparse graph with the specified density.
    """
    if density <= 0 or density > 1:
        raise ValueError(f"Density must be between 0 and 1, got {density}")
    
    n_nodes = matrix.shape[0]
    # Create a copy to avoid modifying the original
    thresholded = np.zeros_like(matrix)
    
    # For each node, keep the top 'density' fraction of connections
    # We consider the upper triangle for undirected graphs, but apply to both for symmetry
    for i in range(n_nodes):
        # Get connections for node i (excluding self)
        row = matrix[i, :]
        # Exclude self-connection
        connections = row.copy()
        connections[i] = 0
        
        # Determine number of edges to keep
        n_edges = int(np.ceil(density * (n_nodes - 1)))
        
        if n_edges == 0:
            continue
        
        # Get indices of top n_edges connections
        top_indices = np.argsort(np.abs(connections))[-n_edges:]
        
        # Set those connections in the thresholded matrix
        thresholded[i, top_indices] = matrix[i, top_indices]
    
    # Ensure symmetry for undirected graph
    thresholded = (thresholded + thresholded.T) / 2.0
    
    return thresholded

def compute_metrics_at_threshold(matrix: np.ndarray, density: float) -> Dict[str, float]:
    """
    Compute network metrics for a connectivity matrix at a given density threshold.
    """
    thresholded_matrix = threshold_connectivity_matrix(matrix, density)
    
    # Compute metrics using the existing function
    # Note: process_subject_metrics expects a matrix and returns a dict of metrics
    metrics = process_subject_metrics(thresholded_matrix)
    
    return metrics

def aggregate_metrics(all_metrics: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Aggregate metrics across all subjects into a DataFrame.
    """
    rows = []
    for subject_id, metrics in all_metrics.items():
        row = {'subject_id': subject_id}
        row.update(metrics)
        rows.append(row)
    
    return pd.DataFrame(rows)

def calculate_stability(metrics_df: pd.DataFrame, metric_name: str) -> Tuple[float, bool]:
    """
    Calculate the standard deviation of a metric across density thresholds.
    Returns (std_dev, is_stable) where is_stable is True if std_dev < 0.05.
    """
    if metric_name not in metrics_df.columns:
        logger.warning(f"Metric {metric_name} not found in DataFrame")
        return np.nan, False
    
    std_dev = metrics_df[metric_name].std()
    is_stable = std_dev < 0.05
    return std_dev, is_stable

def run_sensitivity_analysis(
    connectivity_dir: Path,
    output_dir: Path,
    metrics_of_interest: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Run sensitivity analysis for network density thresholds.
    
    Args:
        connectivity_dir: Directory containing connectivity matrices
        output_dir: Directory to save results
        metrics_of_interest: List of metrics to analyze (default: all available)
    
    Returns:
        DataFrame with sensitivity analysis results
    """
    # Load connectivity matrices
    logger.info("Loading connectivity matrices...")
    matrices = load_connectivity_matrices(connectivity_dir)
    
    if not matrices:
        raise ValueError("No connectivity matrices loaded")
    
    # Define metrics of interest if not provided
    if metrics_of_interest is None:
        # Get metrics from the first subject
        first_subject_metrics = compute_metrics_at_threshold(next(iter(matrices.values())), 0.20)
        metrics_of_interest = list(first_subject_metrics.keys())
    
    logger.info(f"Analyzing metrics: {metrics_of_interest}")
    
    # Store results
    all_results = []
    
    # For each subject
    for subject_id, matrix in matrices.items():
        logger.info(f"Processing subject: {subject_id}")
        
        subject_results = []
        
        # For each density threshold
        for density in DENSITY_THRESHOLDS:
            metrics = compute_metrics_at_threshold(matrix, density)
            
            # Filter to metrics of interest
            filtered_metrics = {k: v for k, v in metrics.items() if k in metrics_of_interest}
            
            subject_results.append({
                'subject_id': subject_id,
                'threshold': density,
                **filtered_metrics
            })
        
        all_results.extend(subject_results)
    
    # Create DataFrame
    results_df = pd.DataFrame(all_results)
    
    # Calculate stability for each metric
    stability_results = []
    for metric in metrics_of_interest:
        # Group by metric and calculate std across thresholds for each subject
        # We want to see how much the metric varies as we change density
        # For each subject, we have multiple rows (one per threshold)
        # We calculate the std dev of the metric across thresholds for each subject, then average
        
        # Pivot to have thresholds as columns
        pivot_df = results_df.pivot_table(
            index='subject_id', 
            columns='threshold', 
            values=metric, 
            aggfunc='first'
        )
        
        # Calculate std dev across thresholds for each subject
        subject_std = pivot_df.std(axis=1)
        
        # Average std dev across subjects
        avg_std = subject_std.mean()
        
        is_stable = avg_std < 0.05
        
        stability_results.append({
            'threshold': 'All',  # This is an aggregate across thresholds
            'metric_name': metric,
            'std_dev': avg_std,
            'is_stable': is_stable
        })
    
    # Also calculate per-threshold stability if needed, but the task asks for overall stability
    # Let's create the final report as specified in the task
    report_rows = []
    for metric in metrics_of_interest:
        # Calculate std dev of the metric across all subjects and thresholds
        metric_values = results_df[metric].values
        std_dev = np.std(metric_values)
        is_stable = std_dev < 0.05
        
        # We need to report for each threshold? The task says "threshold, metric_name, std_dev, is_stable"
        # Let's interpret this as: for each metric, report the stability across thresholds
        # Since we have multiple thresholds, we'll report one row per metric with aggregate stats
        # But the schema suggests one row per threshold-metric combination
        
        # Actually, re-reading the task: "threshold, metric_name, std_dev, is_stable"
        # This suggests we should have one row per threshold-metric pair
        # Let's calculate the std dev of the metric across subjects for each threshold
        
        for threshold in DENSITY_THRESHOLDS:
            threshold_data = results_df[results_df['threshold'] == threshold][metric]
            if len(threshold_data) > 0:
                std_dev = threshold_data.std()
                is_stable = std_dev < 0.05
                report_rows.append({
                    'threshold': threshold,
                    'metric_name': metric,
                    'std_dev': std_dev,
                    'is_stable': is_stable
                })
    
    report_df = pd.DataFrame(report_rows)
    
    # Save results
    ensure_dirs(output_dir)
    output_file = output_dir / "sensitivity_density_report.csv"
    report_df.to_csv(output_file, index=False)
    logger.info(f"Saved sensitivity analysis report to {output_file}")
    
    return report_df

def main():
    """Main entry point for sensitivity analysis."""
    config = get_config_summary()
    
    # Define paths
    connectivity_dir = Path(config['paths']['processed']) / "connectivity_matrices"
    output_dir = Path(config['paths']['results'])
    
    logger.info(f"Connectivity directory: {connectivity_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        # Run sensitivity analysis
        report_df = run_sensitivity_analysis(connectivity_dir, output_dir)
        
        # Print summary
        print("\nSensitivity Analysis Summary:")
        print("=" * 50)
        print(report_df.to_string(index=False))
        print("=" * 50)
        
        # Check overall stability
        stable_metrics = report_df[report_df['is_stable']]['metric_name'].unique()
        unstable_metrics = report_df[~report_df['is_stable']]['metric_name'].unique()
        
        print(f"\nStable metrics (std_dev < 0.05): {len(stable_metrics)}")
        if len(stable_metrics) > 0:
            print(f"  {', '.join(stable_metrics)}")
        
        print(f"\nUnstable metrics (std_dev >= 0.05): {len(unstable_metrics)}")
        if len(unstable_metrics) > 0:
            print(f"  {', '.join(unstable_metrics)}")
        
        logger.info("Sensitivity analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
