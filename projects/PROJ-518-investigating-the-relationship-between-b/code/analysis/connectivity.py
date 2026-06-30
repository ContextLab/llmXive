"""
Connectivity analysis functions for brain network dynamics.
"""
import numpy as np
from typing import List
from config import get_config

def compute_sliding_window_connectivity(
    fmri_data: np.ndarray, 
    window_size: int, 
    step: int
) -> List[np.ndarray]:
    """
    Compute sliding window connectivity matrices from fMRI time series.
    
    Args:
        fmri_data: fMRI time series data (n_timepoints x n_rois)
        window_size: Size of the sliding window in time points
        step: Step size for sliding the window
    
    Returns:
        List of connectivity matrices (one per window)
    """
    n_timepoints, n_rois = fmri_data.shape
    windows = []
    
    for start in range(0, n_timepoints - window_size + 1, step):
        end = start + window_size
        window_data = fmri_data[start:end, :]
        
        # Compute correlation matrix
        corr_matrix = np.corrcoef(window_data.T)
        
        # Handle potential NaN values
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        windows.append(corr_matrix)
    
    return windows

def compute_static_connectivity_strength(fmri_data: np.ndarray) -> float:
    """
    Compute the mean of absolute pairwise correlations from the full-window static matrix.
    
    Args:
        fmri_data: fMRI time series data (n_timepoints x n_rois)
    
    Returns:
        Mean absolute correlation strength across all ROI pairs
    """
    # Compute full correlation matrix
    corr_matrix = np.corrcoef(fmri_data.T)
    
    # Extract upper triangle (excluding diagonal)
    n_rois = corr_matrix.shape[0]
    upper_tri_indices = np.triu_indices(n_rois, k=1)
    correlations = corr_matrix[upper_tri_indices]
    
    # Compute mean absolute correlation
    mean_strength = np.mean(np.abs(correlations))
    
    return float(mean_strength)
