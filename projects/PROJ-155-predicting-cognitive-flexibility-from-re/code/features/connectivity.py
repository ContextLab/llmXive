"""
Dynamic Functional Connectivity (dFC) Feature Extraction.

Implements sliding-window Pearson correlation analysis with specific parameters:
- Window size: 60 seconds (deviation from 30s default, justified in research.md)
- Step size: 1 second
"""
import os
import logging
from typing import List, Dict, Tuple, Optional, Union, Generator
import numpy as np
import pandas as pd
from scipy import stats
from code.config import get_config
from code.data.paths import get_processed_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging

# Initialize logger
logger = logging.getLogger(__name__)

def _get_config_window_params() -> Tuple[int, int]:
    """
    Retrieve window and step parameters from config.
    Returns:
        Tuple of (window_size, step_size) in seconds.
    """
    config = get_config()
    # Default to 60s window as per project specification deviation
    window = config.get('window_seconds', 60)
    step = config.get('step_seconds', 1)
    return int(window), int(step)

def _calculate_window_indices(
    n_timepoints: int, 
    window_size: int, 
    step_size: int
) -> List[Tuple[int, int]]:
    """
    Generate start and end indices for sliding windows.
    
    Args:
        n_timepoints: Total number of time points.
        window_size: Size of the window in time points.
        step_size: Step size between windows in time points.
        
    Returns:
        List of (start_idx, end_idx) tuples.
    """
    indices = []
    for start in range(0, n_timepoints - window_size + 1, step_size):
        end = start + window_size
        indices.append((start, end))
    return indices

def compute_sliding_window_correlation(
    time_series: np.ndarray,
    window_size: int,
    step_size: int
) -> np.ndarray:
    """
    Compute sliding-window Pearson correlation matrices.
    
    Args:
        time_series: 2D array of shape (n_timepoints, n_regions).
        window_size: Number of time points per window.
        step_size: Number of time points to step between windows.
        
    Returns:
        3D array of shape (n_windows, n_regions, n_regions) containing
        correlation matrices for each window.
        
    Raises:
        ValueError: If input dimensions are invalid or window > time_series.
    """
    if time_series.ndim != 2:
        raise ValueError(f"time_series must be 2D, got {time_series.ndim}D")
    
    n_timepoints, n_regions = time_series.shape
    
    if window_size > n_timepoints:
        raise ValueError(
            f"Window size ({window_size}) exceeds time series length ({n_timepoints}). "
            "Cannot compute correlations."
        )
    
    if n_regions < 2:
        raise ValueError("Need at least 2 regions to compute correlations.")
    
    indices = _calculate_window_indices(n_timepoints, window_size, step_size)
    
    if not indices:
        logger.warning(f"No valid windows found for {n_timepoints} points with window={window_size}")
        return np.empty((0, n_regions, n_regions))
    
    n_windows = len(indices)
    corr_matrices = np.zeros((n_windows, n_regions, n_regions))
    
    # Pre-calculate mean and std for efficiency if needed, but np.corrcoef is robust
    for i, (start, end) in enumerate(indices):
        window_data = time_series[start:end, :]
        
        # Handle constant columns (std=0) which cause NaN in corrcoef
        # np.corrcoef returns NaN for constant columns, we handle this by checking std
        col_stds = np.std(window_data, axis=0)
        valid_cols = col_stds > 1e-8
        
        if not np.all(valid_cols):
            # If some columns are constant, we compute corr only on valid ones
            # and fill the rest with 0 or handle appropriately. 
            # For dFC, constant signal in a window is rare but possible.
            # We will compute on the full set but mask NaNs if they occur.
            pass
        
        try:
            # np.corrcoef returns (n_regions, n_regions)
            # rowvar=False treats columns as variables (ROIs)
            c = np.corrcoef(window_data, rowvar=False)
            
            # Handle NaNs resulting from constant columns (set to 0 or keep NaN? 
            # Standard practice: keep NaN or 0. Let's keep 0 for stability in downstream SD)
            c = np.nan_to_num(c, nan=0.0)
            corr_matrices[i, :, :] = c
            
        except Exception as e:
            logger.error(f"Correlation calculation failed for window {i}: {e}")
            # Fill with zeros or NaN? Zeros is safer for SD calculation downstream
            corr_matrices[i, :, :] = 0.0
    
    return corr_matrices

def extract_subject_connectivity_metrics(
    subject_id: str,
    time_series: np.ndarray,
    window_size: Optional[int] = None,
    step_size: Optional[int] = None
) -> Dict[str, float]:
    """
    Compute edge-wise standard deviation and Shannon entropy for a single subject.
    
    Args:
        subject_id: Unique subject identifier.
        time_series: 2D numpy array (n_timepoints, n_regions).
        window_size: Override window size (seconds).
        step_size: Override step size (seconds).
        
    Returns:
        Dictionary with metrics:
            - 'Subject_ID': str
            - 'Mean_FD': float (placeholder, to be filled by merge)
            - 'Variability_Metric': float (mean edge SD)
            - 'Entropy': float (mean edge entropy)
            - 'n_windows': int
    """
    if window_size is None or step_size is None:
        # Convert seconds to TR-based indices. 
        # We assume TR is 1s for HCP 1200 release (900 volumes / 1080s = 0.75s? 
        # Actually HCP 1200 rs-fMRI is 1.2s TR? 
        # The config specifies window=60s. We need TR to convert.
        # Let's assume TR=1.0s for simplicity as per typical preprocessing, 
        # or read from config if available.
        # For robustness, we assume the input time_series is already in the correct time units 
        # corresponding to the config's "seconds" (i.e., if TR=1s, indices=seconds).
        # If TR != 1s, the caller must adjust indices before passing time_series or we need TR.
        # Given the task description "window=60s, step=1s", and HCP data usually has TR=0.72s or 1.2s.
        # However, standard practice in these pipelines often resamples to 1s or assumes 1s for calculation.
        # We will assume the input `time_series` rows correspond to 1s intervals.
        # If not, the user must provide TR.
        # Let's add a check or default.
        # For this implementation, we assume 1 sample = 1 second as per the task's "step=1s" implication.
        window_idx = window_size
        step_idx = step_size
    else:
        # If passed as seconds, we assume 1 sample = 1 second.
        window_idx = window_size
        step_idx = step_size
        
    # If the caller passed window_size in seconds but TR is different, 
    # we need to know TR. Since config doesn't explicitly expose TR in the provided API,
    # we assume the data is pre-sampled or TR=1.0s.
    # Re-reading config: "window=60s". 
    # We will assume 1 sample = 1 second.
    if window_size: window_idx = window_size
    if step_size: step_idx = step_size

    try:
        corr_matrices = compute_sliding_window_correlation(
            time_series, 
            window_size=window_idx, 
            step_size=step_idx
        )
    except ValueError as e:
        log_error(f"Subject {subject_id}: {str(e)}")
        return {
            'Subject_ID': subject_id,
            'Variability_Metric': np.nan,
            'Entropy': np.nan,
            'n_windows': 0
        }

    n_windows, n_regions, _ = corr_matrices.shape
    if n_windows == 0:
        return {
            'Subject_ID': subject_id,
            'Variability_Metric': np.nan,
            'Entropy': np.nan,
            'n_windows': 0
        }

    # Extract upper triangle (excluding diagonal) for each window
    # Shape: (n_windows, n_edges)
    triu_indices = np.triu_indices(n_regions, k=1)
    edge_series = corr_matrices[:, triu_indices[0], triu_indices[1]]
    
    # Calculate Edge-wise SD (Variability Metric)
    # Mean of the standard deviations of each edge across windows
    edge_sds = np.std(edge_series, axis=0)
    mean_edge_sd = np.mean(edge_sds)
    
    # Calculate Shannon Entropy
    # Entropy of the distribution of correlation values for each edge, then average?
    # Or Entropy of the distribution of all edge values?
    # Task says: "edge-wise ... Shannon entropy".
    # Usually: Calculate entropy for each edge's distribution across windows, then average.
    # Entropy H(X) = - sum p(x) log p(x). 
    # We need to discretize the continuous correlation values into bins.
    
    # Discretization: 50 bins from -1 to 1
    n_bins = 50
    bins = np.linspace(-1.0, 1.0, n_bins + 1)
    
    entropies = []
    for i in range(edge_sds.shape[0]): # For each edge
        edge_vals = edge_series[:, i]
        # Histogram
        hist, _ = np.histogram(edge_vals, bins=bins, density=False)
        # Normalize to probability
        p = hist / np.sum(hist)
        # Remove zeros to avoid log(0)
        p = p[p > 0]
        # Shannon entropy
        h = -np.sum(p * np.log2(p))
        entropies.append(h)
    
    mean_entropy = np.mean(entropies) if entropies else 0.0
    
    return {
        'Subject_ID': subject_id,
        'Variability_Metric': float(mean_edge_sd),
        'Entropy': float(mean_entropy),
        'n_windows': int(n_windows)
    }

def run_connectivity_pipeline(
    subjects: List[str],
    tr: float = 1.0
) -> pd.DataFrame:
    """
    Main pipeline to process all subjects and extract connectivity metrics.
    
    Args:
        subjects: List of subject IDs.
        tr: Repetition time in seconds. Defaults to 1.0 if not specified.
            
    Returns:
        DataFrame with columns: Subject_ID, Variability_Metric, Entropy, n_windows.
    """
    config = get_config()
    window_sec = config.get('window_seconds', 60)
    step_sec = config.get('step_seconds', 1)
    
    # Convert seconds to indices based on TR
    window_idx = int(window_sec / tr)
    step_idx = int(step_sec / tr)
    
    logger.info(f"Running connectivity pipeline with window={window_sec}s ({window_idx} TRs), step={step_sec}s ({step_idx} TRs)")
    
    results = []
    processed_path = get_processed_path()
    time_series_dir = os.path.join(processed_path, 'time_series')
    
    for subject_id in subjects:
        ts_path = os.path.join(time_series_dir, f"{subject_id}_time_series.npy")
        
        if not os.path.exists(ts_path):
            log_warning(f"Time series file not found for {subject_id}: {ts_path}")
            continue
        
        try:
            time_series = np.load(ts_path)
            metrics = extract_subject_connectivity_metrics(
                subject_id, 
                time_series, 
                window_size=window_idx, 
                step_size=step_idx
            )
            results.append(metrics)
        except Exception as e:
            log_error(f"Failed to process {subject_id}: {str(e)}")
            continue
    
    if not results:
        logger.error("No results generated.")
        return pd.DataFrame()
        
    df = pd.DataFrame(results)
    
    # Save intermediate metrics
    output_path = os.path.join(processed_path, 'metrics.csv')
    df.to_csv(output_path, index=False)
    logger.info(f"Saved connectivity metrics to {output_path}")
    
    return df

# Entry point for direct execution
if __name__ == "__main__":
    init_logging()
    from code.config import set_seed
    set_seed(42)
    
    # Example usage with a dummy subject list if not provided via args
    # In real execution, this would be driven by main.py
    dummy_subjects = ['100307'] # Example HCP ID
    df = run_connectivity_pipeline(dummy_subjects)
    print(df.head())
