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
    # per task T014 description. If args are default or None, fallback to config.
    if window_size is None or window_size == 0:
        window_size = config.WINDOW_SIZES[0] if config.WINDOW_SIZES else 30
    if step is None or step == 0:
        step = config.STEP if config.STEP else 5

    n_timepoints, n_rois = fmri_data.shape
    
    if n_timepoints < window_size:
        raise ValueError(
            f"Insufficient timepoints: {n_timepoints} < window_size {window_size}. "
            "Cannot compute sliding window connectivity."
        )
    
    windows = []
    
    # Slide window across time
    for start in range(0, n_timepoints - window_size + 1, step):
        end = start + window_size
        window_data = fmri_data[start:end, :]
        
        # Compute correlation matrix for this window
        # corrcoef expects variables as rows or columns; here rows are timepoints, cols are ROIs
        # We need correlation between ROIs, so we transpose (ROIs x timepoints)
        try:
            corr_matrix = np.corrcoef(window_data.T)
        except ValueError as e:
            # Handle cases where correlation cannot be computed (e.g., constant rows)
            raise ValueError(f"Failed to compute correlation for window [{start}:{end}]: {e}")
        
        # Handle NaNs that might occur if a row is constant or variance is zero
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
    try:
        corr_matrix = np.corrcoef(fmri_data.T)
    except ValueError as e:
        raise ValueError(f"Failed to compute static correlation matrix: {e}")
    
    # Handle NaNs
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    # Extract upper triangle (excluding diagonal) to get unique pairs
    n = corr_matrix.shape[0]
    upper_triangle_indices = np.triu_indices(n, k=1)
    upper_triangle_values = corr_matrix[upper_triangle_indices]
    
    if len(upper_triangle_values) == 0:
        return 0.0
    
    # Compute mean of absolute values
    mean_abs_corr = float(np.mean(np.abs(upper_triangle_values)))
    
    return mean_abs_corr
