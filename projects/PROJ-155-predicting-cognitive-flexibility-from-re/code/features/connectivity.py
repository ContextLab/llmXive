import os
import logging
from typing import List, Dict, Tuple, Optional, Union, Generator
import numpy as np
import pandas as pd
from scipy import stats

from code.config import get_config
from code.data.paths import get_processed_path, get_results_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging

def compute_sliding_window_correlation(
    time_series: np.ndarray,
    window_size: int,
    step_size: int
) -> np.ndarray:
    """
    Compute sliding-window Pearson correlation matrices for a subject's ROI time series.

    Args:
        time_series: Array of shape (time_points, n_rois).
        window_size: Number of time points per window (e.g., 60s at TR=1s).
        step_size: Step size between windows.

    Returns:
        Array of shape (n_windows, n_rois, n_rois) containing correlation matrices.
    """
    n_timepoints, n_rois = time_series.shape
    
    if n_timepoints < window_size:
        raise ValueError(
            f"Time series length ({n_timepoints}) is shorter than window size ({window_size}). "
            "Cannot compute sliding window correlations."
        )

    n_windows = (n_timepoints - window_size) // step_size + 1
    corr_matrices = np.zeros((n_windows, n_rois, n_rois))

    for i in range(n_windows):
        start_idx = i * step_size
        end_idx = start_idx + window_size
        window_data = time_series[start_idx:end_idx, :]

        # Compute correlation matrix for the window
        # Using numpy.corrcoef which returns (n_rois, n_rois)
        # Handle constant columns (zero variance) to avoid NaNs
        with np.errstate(all='ignore'):
            corr_matrix = np.corrcoef(window_data, rowvar=False)
        
        # Replace NaNs (from constant columns) with 0.0
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        corr_matrices[i] = corr_matrix

    return corr_matrices

def compute_edge_metrics(
    corr_matrices: np.ndarray
) -> Tuple[np.ndarray, float]:
    """
    Compute edge-wise standard deviation and Shannon entropy from sliding-window correlation matrices.

    Args:
        corr_matrices: Array of shape (n_windows, n_rois, n_rois).

    Returns:
        Tuple of:
            - edge_sd: Array of shape (n_edges,) containing SD of correlations for each unique edge.
            - entropy: Shannon entropy of the distribution of edge-wise SDs.
    """
    n_windows, n_rois, _ = corr_matrices.shape
    
    # Extract unique edges (upper triangle, excluding diagonal)
    # Indices for upper triangle
    triu_indices = np.triu_indices(n_rois, k=1)
    n_edges = len(triu_indices[0])

    # Extract edge time series: shape (n_windows, n_edges)
    edge_time_series = corr_matrices[:, triu_indices[0], triu_indices[1]]

    # Compute edge-wise standard deviation: shape (n_edges,)
    edge_sd = np.std(edge_time_series, axis=0)

    # Compute Shannon entropy of the edge-wise SD distribution
    # Normalize to form a probability distribution
    # Add small epsilon to avoid log(0) if any SD is 0
    epsilon = 1e-10
    prob_dist = edge_sd + epsilon
    prob_dist = prob_dist / np.sum(prob_dist)
    
    entropy = -np.sum(prob_dist * np.log(prob_dist))

    return edge_sd, entropy

def extract_subject_connectivity_metrics(
    subject_id: str,
    time_series: np.ndarray,
    window_size: int,
    step_size: int
) -> Dict[str, Union[str, float]]:
    """
    Extract connectivity variability metrics for a single subject.

    Args:
        subject_id: Subject identifier.
        time_series: ROI time series of shape (time_points, n_rois).
        window_size: Window size in time points.
        step_size: Step size in time points.

    Returns:
        Dictionary with Subject_ID, Variability_Metric (mean edge SD), and Entropy.
    """
    try:
        # Compute sliding window correlations
        corr_matrices = compute_sliding_window_correlation(
            time_series, window_size, step_size
        )

        # Compute edge metrics
        edge_sd, entropy = compute_edge_metrics(corr_matrices)

        # Variability Metric: Mean of edge-wise SDs
        variability_metric = float(np.mean(edge_sd))
        entropy_val = float(entropy)

        return {
            "Subject_ID": subject_id,
            "Variability_Metric": variability_metric,
            "Entropy": entropy_val
        }

    except Exception as e:
        log_error(f"Failed to compute connectivity metrics for {subject_id}: {str(e)}")
        raise

def run_connectivity_pipeline(
    subject_ids: List[str],
    time_series_data: Dict[str, np.ndarray],
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run connectivity metric computation for a list of subjects.

    Args:
        subject_ids: List of subject identifiers.
        time_series_data: Dictionary mapping subject_id to time_series array.
        output_path: Optional path to save the results CSV.

    Returns:
        DataFrame containing Subject_ID, Variability_Metric, and Entropy for each subject.
    """
    config = get_config()
    window_size = config.get("window_size", 60)  # seconds
    step_size = config.get("step_size", 1)       # seconds
    
    # If TR is not 1s, we need to convert seconds to time points
    # Assuming TR=1s for HCP data as per standard preprocessing
    tr = config.get("tr", 1.0)
    window_points = int(window_size / tr)
    step_points = int(step_size / tr)

    results = []
    
    for subject_id in subject_ids:
        if subject_id not in time_series_data:
            log_warning(f"Time series data not found for {subject_id}. Skipping.")
            continue
        
        time_series = time_series_data[subject_id]
        
        try:
            metrics = extract_subject_connectivity_metrics(
                subject_id, time_series, window_points, step_points
            )
            results.append(metrics)
        except Exception as e:
            log_error(f"Skipping {subject_id} due to error: {str(e)}")
            continue

    df = pd.DataFrame(results)
    
    if output_path:
        ensure_dir(output_path)
        df.to_csv(output_path, index=False)
        logging.info(f"Connectivity metrics saved to {output_path}")
    
    return df