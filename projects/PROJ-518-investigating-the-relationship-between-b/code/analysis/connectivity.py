import numpy as np
from typing import List
from config import get_config


def compute_sliding_window_connectivity(
    fmri_data: np.ndarray,
    window_size: int,
    step: int
) -> List[np.ndarray]:
    """
    Compute sliding window connectivity matrices.

    Args:
        fmri_data: Preprocessed fMRI data (timepoints x ROIs).
        window_size: Size of the sliding window in timepoints.
        step: Step size between windows in timepoints.

    Returns:
        List of connectivity matrices (window_size x ROIs x ROIs).
    """
    config = get_config()
    # Use config values if not provided, but this function expects explicit args
    # per task T014 description.
    
    n_timepoints, n_rois = fmri_data.shape
    windows = []
    
    for start in range(0, n_timepoints - window_size + 1, step):
        end = start + window_size
        window_data = fmri_data[start:end, :]
        
        # Compute correlation matrix for this window
        corr_matrix = np.corrcoef(window_data.T)
        
        # Handle NaNs that might occur if a row is constant
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        windows.append(corr_matrix)
        
    return windows


def compute_static_connectivity_strength(fmri_data: np.ndarray) -> float:
    """
    Calculate the mean of absolute pairwise correlations from the full-window static matrix.

    Args:
        fmri_data: Preprocessed fMRI data (timepoints x ROIs).

    Returns:
        Mean absolute correlation value (float).
    """
    n_timepoints, n_rois = fmri_data.shape
    
    if n_timepoints < 2:
        raise ValueError("Need at least 2 timepoints to compute connectivity.")
        
    # Compute full correlation matrix
    corr_matrix = np.corrcoef(fmri_data.T)
    
    # Handle NaNs
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    # Extract upper triangle (excluding diagonal)
    n = corr_matrix.shape[0]
    upper_triangle_indices = np.triu_indices(n, k=1)
    upper_triangle_values = corr_matrix[upper_triangle_indices]
    
    # Compute mean of absolute values
    mean_abs_corr = np.mean(np.abs(upper_triangle_values))
    
    return float(mean_abs_corr)
