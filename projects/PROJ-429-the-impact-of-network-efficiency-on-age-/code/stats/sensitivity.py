import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from network.metrics import compute_all_metrics
from network.connectivity import load_epochs_from_file
from config import ensure_dirs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thresholds for sensitivity analysis (significance levels or connection strength thresholds)
# We will sweep a range of thresholds to see how stable the metrics are
THRESHOLD_RANGE = np.linspace(0.1, 0.9, 9)  # 0.1 to 0.9 in steps of 0.1

def load_connectivity_matrices(epochs_dir: Path) -> Dict[str, Any]:
    """
    Load all connectivity matrices from the processed epochs directory.
    Returns a dictionary mapping subject_id to a list of connectivity matrices.
    """
    if not epochs_dir.exists():
        raise FileNotFoundError(f"Epochs directory not found: {epochs_dir}")

    matrices = {}
    for subject_dir in epochs_dir.iterdir():
        if subject_dir.is_dir():
            subject_id = subject_dir.name
            matrices[subject_id] = []
            for conn_file in subject_dir.glob("*.npz"):
                try:
                    data = np.load(conn_file)
                    # Assuming the connectivity matrix is stored under a key like 'connectivity'
                    if 'connectivity' in data:
                        matrices[subject_id].append(data['connectivity'])
                    elif 'matrix' in data:
                        matrices[subject_id].append(data['matrix'])
                    else:
                        logger.warning(f"Unknown format in {conn_file}, skipping")
                except Exception as e:
                    logger.error(f"Error loading {conn_file}: {e}")
    return matrices

def compute_metrics_at_threshold(
    connectivity_matrix: np.ndarray,
    threshold: float
) -> Dict[str, float]:
    """
    Apply a threshold to the connectivity matrix and compute graph metrics.
    Thresholding: keep edges where connectivity strength >= threshold.
    """
    # Create a binary adjacency matrix based on threshold
    adj_matrix = (connectivity_matrix >= threshold).astype(float)
    np.fill_diagonal(adj_matrix, 0)  # Ensure no self-loops

    # Compute metrics using the existing compute_all_metrics function
    # Note: compute_all_metrics expects a weighted or binary matrix
    metrics = compute_all_metrics(adj_matrix)
    return metrics

def aggregate_metrics(
    all_metrics: List[Dict[str, float]],
    metric_names: List[str]
) -> Dict[str, float]:
    """
    Aggregate metrics across multiple subjects/epochs by computing mean and std dev.
    """
    aggregated = {}
    for metric in metric_names:
        values = [m.get(metric, np.nan) for m in all_metrics if metric in m]
        if values:
            aggregated[metric] = {
                'mean': float(np.nanmean(values)),
                'std': float(np.nanstd(values))
            }
        else:
            aggregated[metric] = {'mean': np.nan, 'std': np.nan}
    return aggregated

def calculate_stability(
    aggregated_metrics: Dict[str, Dict[str, float]],
    threshold: float,
    stability_threshold: float = 0.05
) -> Dict[str, bool]:
    """
    Determine if metrics are stable at a given threshold.
    A metric is stable if its standard deviation across subjects is < stability_threshold.
    """
    stability = {}
    for metric, stats in aggregated_metrics.items():
        std_dev = stats['std']
        if not np.isnan(std_dev):
            is_stable = std_dev < stability_threshold
            stability[metric] = is_stable
        else:
            stability[metric] = False  # Cannot determine stability if no data
    return stability

def run_sensitivity_analysis(
    epochs_dir: Path,
    output_path: Path,
    stability_threshold: float = 0.05
) -> pd.DataFrame:
    """
    Run sensitivity analysis across a range of thresholds.
    Generates a report CSV with threshold, metric_name, std_dev, is_stable.
    """
    logger.info(f"Loading connectivity matrices from {epochs_dir}")
    matrices = load_connectivity_matrices(epochs_dir)

    if not matrices:
        raise ValueError("No connectivity matrices found. Ensure preprocessing has been run.")

    all_metric_names = ['global_efficiency', 'local_efficiency', 'clustering_coefficient', 'characteristic_path_length', 'modularity']
    results = []

    logger.info(f"Running sensitivity analysis across {len(THRESHOLD_RANGE)} thresholds")
    for threshold in THRESHOLD_RANGE:
        logger.info(f"Processing threshold: {threshold:.2f}")
        all_subject_metrics = []

        for subject_id, subject_matrices in matrices.items():
            for matrix in subject_matrices:
                try:
                    metrics = compute_metrics_at_threshold(matrix, threshold)
                    all_subject_metrics.append(metrics)
                except Exception as e:
                    logger.warning(f"Error computing metrics for subject {subject_id} at threshold {threshold}: {e}")

        if not all_subject_metrics:
            logger.warning(f"No metrics computed for threshold {threshold}, skipping")
            continue

        aggregated = aggregate_metrics(all_subject_metrics, all_metric_names)
        stability = calculate_stability(aggregated, threshold, stability_threshold)

        for metric in all_metric_names:
            std_dev = aggregated[metric]['std']
            is_stable = stability.get(metric, False)
            results.append({
                'threshold': threshold,
                'metric_name': metric,
                'std_dev': std_dev,
                'is_stable': is_stable
            })

    # Create DataFrame and save
    df = pd.DataFrame(results)
    ensure_dirs(output_path.parent)
    df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity report saved to {output_path}")
    return df

def main():
    """
    Main entry point for sensitivity analysis.
    """
    from config import ensure_dirs
    import sys

    # Default paths
    epochs_dir = Path("data/processed/epochs")
    output_path = Path("data/results/sensitivity_report.csv")

    # Allow overriding via command line
    if len(sys.argv) > 1:
        epochs_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    try:
        run_sensitivity_analysis(epochs_dir, output_path)
        print(f"Sensitivity analysis completed. Report saved to {output_path}")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
