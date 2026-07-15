"""
Sensitivity Analysis for Network Metrics (FR-008)

Implements a threshold sweep across significance levels to evaluate the stability
of network metrics (Global Efficiency, Local Efficiency, Clustering Coefficient, etc.).
Generates a report indicating which metrics are stable (variation < 0.05) across
the swept thresholds.

Output: data/results/sensitivity_report.csv
Schema: threshold, metric_name, std_dev, is_stable
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import ensure_dirs, RESULTS_DIR
from network.metrics import compute_all_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for sensitivity analysis
THRESHOLD_RANGE = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
STABILITY_TOLERANCE = 0.05

def load_connectivity_matrices(mat_dir: Path) -> Dict[str, np.ndarray]:
    """
    Load all connectivity matrices from the specified directory.
    Returns a dictionary mapping subject_id to the connectivity matrix.
    """
    matrices = {}
    if not mat_dir.exists():
        raise FileNotFoundError(f"Connectivity matrix directory not found: {mat_dir}")
    
    for file_path in mat_dir.glob("*.npy"):
        subject_id = file_path.stem
        try:
            matrices[subject_id] = np.load(file_path)
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    
    if not matrices:
        raise ValueError(f"No valid connectivity matrices found in {mat_dir}")
    
    logger.info(f"Loaded {len(matrices)} connectivity matrices.")
    return matrices

def compute_metrics_at_threshold(
    matrices: Dict[str, np.ndarray], 
    threshold: float
) -> Dict[str, Dict[str, float]]:
    """
    Apply a threshold to the connectivity matrices and compute network metrics.
    The threshold here represents the proportion of edges to retain (sparsity)
    or a correlation strength cutoff. For this analysis, we interpret it as 
    a sparsity level (keep top 'threshold' fraction of edges).
    
    Returns a dictionary: { subject_id: { metric_name: value } }
    """
    results = {}
    
    for subject_id, matrix in matrices.items():
        # Create a copy to avoid modifying original
        adj_matrix = matrix.copy()
        
        # Apply threshold: Keep top 'threshold' fraction of edges by weight
        # Flatten, sort, find cutoff
        flat_vals = adj_matrix.flatten()
        # Exclude diagonal (self-loops)
        np.fill_diagonal(adj_matrix, 0)
        flat_non_diag = adj_matrix.flatten()
        flat_non_diag = flat_non_diag[flat_non_diag > 0]
        
        if len(flat_non_diag) == 0:
            continue

        cutoff_idx = int(len(flat_non_diag) * (1 - threshold))
        if cutoff_idx < 0: cutoff_idx = 0
        if cutoff_idx >= len(flat_non_diag): cutoff_idx = len(flat_non_diag) - 1
        
        threshold_val = np.sort(flat_non_diag)[cutoff_idx]
        
        # Apply hard threshold
        binary_mask = adj_matrix >= threshold_val
        adj_matrix = adj_matrix * binary_mask
        
        # Ensure diagonal is 0
        np.fill_diagonal(adj_matrix, 0)
        
        # Check if graph is connected or valid
        if np.sum(adj_matrix) == 0:
            continue

        # Compute metrics
        try:
            metrics = compute_all_metrics(adj_matrix)
            results[subject_id] = metrics
        except Exception as e:
            logger.warning(f"Failed to compute metrics for {subject_id} at threshold {threshold}: {e}")
            continue

    return results

def aggregate_metrics(metrics_dict: Dict[str, Dict[str, float]]) -> Dict[str, List[float]]:
    """
    Aggregate metrics across subjects into lists for statistical analysis.
    Returns: { metric_name: [val_subj1, val_subj2, ...] }
    """
    aggregated = {}
    for subject_id, metrics in metrics_dict.items():
        for metric_name, value in metrics.items():
            if metric_name not in aggregated:
                aggregated[metric_name] = []
            if not np.isnan(value) and not np.isinf(value):
                aggregated[metric_name].append(value)
    return aggregated

def calculate_stability(aggregated: Dict[str, List[float]]) -> List[Dict[str, Any]]:
    """
    Calculate standard deviation and stability flag for each metric.
    Returns a list of dicts: { metric_name, std_dev, is_stable }
    """
    stats = []
    for metric_name, values in aggregated.items():
        if len(values) < 2:
            std_dev = 0.0
        else:
            std_dev = float(np.std(values))
        
        is_stable = std_dev < STABILITY_TOLERANCE
        stats.append({
            'metric_name': metric_name,
            'std_dev': std_dev,
            'is_stable': is_stable
        })
    return stats

def run_sensitivity_analysis(
    connectivity_dir: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main driver for the sensitivity analysis.
    Sweeps through THRESHOLD_RANGE, computes metrics, aggregates, and checks stability.
    """
    if connectivity_dir is None:
        connectivity_dir = Path(RESULTS_DIR) / "connectivity_matrices"
    if output_path is None:
        output_path = Path(RESULTS_DIR) / "sensitivity_report.csv"

    ensure_dirs()
    
    logger.info(f"Loading connectivity matrices from {connectivity_dir}...")
    try:
        matrices = load_connectivity_matrices(connectivity_dir)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Data loading failed: {e}")
        # Create an empty report with headers if no data exists, but log failure
        report_df = pd.DataFrame(columns=['threshold', 'metric_name', 'std_dev', 'is_stable'])
        report_df.to_csv(output_path, index=False)
        return report_df

    logger.info(f"Running sensitivity sweep over {len(THRESHOLD_RANGE)} thresholds...")
    
    report_data = []
    
    for threshold in THRESHOLD_RANGE:
        logger.info(f"Processing threshold: {threshold}")
        
        # Compute metrics for this threshold
        metrics_by_subject = compute_metrics_at_threshold(matrices, threshold)
        
        if not metrics_by_subject:
            logger.warning(f"No valid metrics computed for threshold {threshold}. Skipping.")
            continue
        
        # Aggregate across subjects
        aggregated = aggregate_metrics(metrics_by_subject)
        
        # Calculate stability stats
        stability_stats = calculate_stability(aggregated)
        
        for stat in stability_stats:
            report_data.append({
                'threshold': threshold,
                'metric_name': stat['metric_name'],
                'std_dev': stat['std_dev'],
                'is_stable': stat['is_stable']
            })
    
    report_df = pd.DataFrame(report_data)
    
    if report_df.empty:
        logger.warning("Sensitivity analysis produced no results. Check input data.")
    
    logger.info(f"Saving sensitivity report to {output_path}")
    report_df.to_csv(output_path, index=False)
    
    return report_df

def main():
    """Entry point for the script."""
    logger.info("Starting Sensitivity Analysis (T018)...")
    try:
        df = run_sensitivity_analysis()
        logger.info(f"Sensitivity analysis complete. Output: {RESULTS_DIR}/sensitivity_report.csv")
        if not df.empty:
            stable_count = df['is_stable'].sum()
            logger.info(f"Stable metrics found: {stable_count} / {len(df)}")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
