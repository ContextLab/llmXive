"""
Connectivity features computation for resting-state fMRI.

Implements sliding-window correlation, edge-wise metrics (SD, entropy),
and aggregation into subject-level variability metrics.

Optimized for memory efficiency using generators for time-series buffering.
"""

import os
import logging
from typing import List, Dict, Tuple, Optional, Union, Generator, Any

import numpy as np
import pandas as pd
from scipy import stats

from code.config import get_config
from code.data.paths import get_processed_path, ensure_dir

logger = logging.getLogger(__name__)

def _get_window_indices(
    n_timepoints: int, 
    window_size: int, 
    step_size: int
) -> Generator[Tuple[int, int], None, None]:
    """
    Generator yielding (start, end) indices for sliding windows.
    
    This replaces list-based buffering to reduce memory footprint.
    
    Args:
        n_timepoints: Total number of time points in the time series.
        window_size: Size of the sliding window in time points.
        step_size: Step size between windows in time points.
        
    Yields:
        Tuples of (start_index, end_index) for each window.
    """
    start = 0
    while start + window_size <= n_timepoints:
        end = start + window_size
        yield start, end
        start += step_size

def compute_sliding_window_correlation(
    timeseries: np.ndarray,
    window_size: Optional[int] = None,
    step_size: Optional[int] = None
) -> Generator[np.ndarray, None, None]:
    """
    Compute sliding-window Pearson correlation matrices using a generator.
    
    Instead of storing all correlation matrices in a list (which consumes O(N) memory),
    this function yields them one by one, allowing downstream consumers to process
    and discard each matrix immediately.
    
    Args:
        timeseries: 2D numpy array of shape (n_timepoints, n_rois).
        window_size: Window size in time points. Defaults to config value (60s).
        step_size: Step size in time points. Defaults to config value (1s).
        
    Yields:
        2D numpy array of shape (n_rois, n_rois) for each window's correlation matrix.
        
    Note:
        Window and step sizes are converted from seconds to time points based on
        the TR (repetition time) from the config.
    """
    config = get_config()
    
    if window_size is None:
        window_seconds = config.get('window_seconds', 60)
        tr = config.get('tr', 0.72)  # HCP TR
        window_size = int(window_seconds / tr)
    
    if step_size is None:
        step_seconds = config.get('step_seconds', 1)
        tr = config.get('tr', 0.72)
        step_size = int(step_seconds / tr)
    
    n_timepoints, n_rois = timeseries.shape
    
    if n_timepoints < window_size:
        logger.warning(f"Time series too short ({n_timepoints} < {window_size})")
        return
    
    # Use generator for window indices
    for start, end in _get_window_indices(n_timepoints, window_size, step_size):
        window_data = timeseries[start:end, :]
        
        # Compute correlation matrix for this window
        # Use scipy.stats.pearsonr or numpy.corrcoef
        try:
            corr_matrix = np.corrcoef(window_data.T)
            # Handle NaNs from constant time series
            corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
            yield corr_matrix
        except Exception as e:
            logger.warning(f"Failed to compute correlation for window [{start}:{end}]: {e}")
            continue

def compute_edge_metrics(
    correlation_matrices: Generator[np.ndarray, None, None],
    n_rois: int
) -> Tuple[np.ndarray, float]:
    """
    Compute edge-wise standard deviation and Shannon entropy from a generator of correlation matrices.
    
    Instead of storing all matrices, this function processes them in a streaming fashion,
    accumulating statistics online to compute the final metrics.
    
    Args:
        correlation_matrices: Generator yielding correlation matrices (n_rois x n_rois).
        n_rois: Number of ROIs (regions of interest).
        
    Returns:
        Tuple of:
            - edge_sd: 1D array of shape (n_edges,) containing SD for each edge.
            - entropy: Shannon entropy of the edge-wise SD distribution.
    """
    # Initialize accumulators for online computation
    # We need: mean, sum of squared differences for variance
    edge_sums = np.zeros(n_rois * n_rois)
    edge_sq_sums = np.zeros(n_rois * n_rois)
    n_windows = 0
    
    # Process each matrix from the generator
    for corr_matrix in correlation_matrices:
        if corr_matrix.shape != (n_rois, n_rois):
            logger.warning(f"Unexpected matrix shape: {corr_matrix.shape}")
            continue
        
        # Flatten upper triangle (including diagonal) for edge-wise processing
        # We only care about unique edges (upper triangle)
        upper_tri_indices = np.triu_indices(n_rois)
        edge_values = corr_matrix[upper_tri_indices]
        
        edge_sums += edge_values
        edge_sq_sums += edge_values ** 2
        n_windows += 1
    
    if n_windows == 0:
        logger.error("No valid windows processed")
        return np.array([]), 0.0
    
    # Compute mean and variance
    edge_means = edge_sums / n_windows
    edge_variances = (edge_sq_sums / n_windows) - (edge_means ** 2)
    
    # Ensure non-negative variance (numerical stability)
    edge_variances = np.maximum(edge_variances, 0)
    edge_sd = np.sqrt(edge_variances)
    
    # Compute Shannon entropy of the edge SD distribution
    # Normalize to probability distribution
    edge_sd_nonzero = edge_sd[edge_sd > 0]
    if len(edge_sd_nonzero) == 0:
        entropy = 0.0
    else:
        prob = edge_sd_nonzero / np.sum(edge_sd_nonzero)
        # Avoid log(0)
        prob = prob[prob > 0]
        entropy = -np.sum(prob * np.log2(prob))
    
    return edge_sd, entropy

def extract_subject_connectivity_metrics(
    subject_id: str,
    timeseries: np.ndarray,
    window_size: Optional[int] = None,
    step_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Extract connectivity metrics for a single subject using generator-based processing.
    
    This function orchestrates the sliding-window correlation and edge metric computation
    while maintaining low memory usage through generator usage.
    
    Args:
        subject_id: Subject identifier.
        timeseries: 2D numpy array of shape (n_timepoints, n_rois).
        window_size: Window size in time points (optional, uses config if None).
        step_size: Step size in time points (optional, uses config if None).
        
    Returns:
        Dictionary containing:
            - 'Subject_ID': Subject identifier.
            - 'Variability_Metric': Mean edge standard deviation.
            - 'Entropy': Shannon entropy of edge SD distribution.
            - 'n_windows': Number of windows processed.
    """
    n_rois = timeseries.shape[1]
    
    # Create generator for correlation matrices
    corr_gen = compute_sliding_window_correlation(
        timeseries, 
        window_size=window_size, 
        step_size=step_size
    )
    
    # Compute edge metrics from the generator
    edge_sd, entropy = compute_edge_metrics(corr_gen, n_rois)
    
    if len(edge_sd) == 0:
        return {
            'Subject_ID': subject_id,
            'Variability_Metric': np.nan,
            'Entropy': np.nan,
            'n_windows': 0
        }
    
    # Aggregate to subject-level metric
    variability_metric = np.mean(edge_sd)
    
    return {
        'Subject_ID': subject_id,
        'Variability_Metric': variability_metric,
        'Entropy': entropy,
        'n_windows': int(np.sum([1 for _ in compute_sliding_window_correlation(timeseries, window_size, step_size)]))
    }

def run_connectivity_pipeline(
    input_data: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run the connectivity analysis pipeline on a list of subjects.
    
    Args:
        input_data: List of dictionaries, each containing:
            - 'Subject_ID': Subject identifier.
            - 'timeseries': 2D numpy array of time series data.
        output_path: Optional path to save the results CSV.
        
    Returns:
        DataFrame containing connectivity metrics for all subjects.
    """
    config = get_config()
    window_size = config.get('window_seconds', 60)
    step_size = config.get('step_seconds', 1)
    tr = config.get('tr', 0.72)
    
    window_points = int(window_size / tr)
    step_points = int(step_size / tr)
    
    results = []
    
    for subject_data in input_data:
        subject_id = subject_data['Subject_ID']
        timeseries = subject_data['timeseries']
        
        logger.info(f"Processing subject {subject_id}...")
        
        try:
            metrics = extract_subject_connectivity_metrics(
                subject_id=subject_id,
                timeseries=timeseries,
                window_size=window_points,
                step_size=step_points
            )
            results.append(metrics)
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
            results.append({
                'Subject_ID': subject_id,
                'Variability_Metric': np.nan,
                'Entropy': np.nan,
                'n_windows': 0
            })
    
    df = pd.DataFrame(results)
    
    if output_path:
        ensure_dir(os.path.dirname(output_path))
        df.to_csv(output_path, index=False)
        logger.info(f"Results saved to {output_path}")
    
    return df

def main():
    """Main entry point for connectivity analysis."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (typically called from main.py or batch processor)
    logger.info("Connectivity pipeline initialized with generator-based processing.")
    logger.info("This implementation uses generators to reduce memory footprint.")

if __name__ == "__main__":
    main()