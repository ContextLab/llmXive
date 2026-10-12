"""Motion artifact handling and exclusion logic."""
import logging
import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple, List

from code.config import get_config
from code.utils.logging import log_exclusion

logger = logging.getLogger(__name__)

def calculate_mean_fd(motion_params: np.ndarray) -> float:
    """
    Calculate mean framewise displacement from motion parameters.
    
    FD is computed as the sum of absolute values of the derivatives
    of the 6 rigid-body motion parameters.
    
    Args:
        motion_params: Array of shape (n_timepoints, 6) containing
            3 translation and 3 rotation parameters.
    
    Returns:
        Mean framewise displacement in mm.
    """
    if motion_params.ndim != 2 or motion_params.shape[1] != 6:
        raise ValueError(
            f"Expected motion_params shape (n_timepoints, 6), "
            f"got {motion_params.shape}"
        )
    
    # Calculate derivatives (differences between consecutive timepoints)
    derivatives = np.diff(motion_params, axis=0)
    
    # For rotational parameters (columns 3-5), convert to mm
    # Using the approximation: rotation_in_mm = rotation_in_radians * radius
    # Standard brain radius ~50mm
    radius_mm = 50.0
    derivatives[:, 3:6] = derivatives[:, 3:6] * radius_mm
    
    # Calculate FD as sum of absolute derivatives
    fd_per_timepoint = np.sum(np.abs(derivatives), axis=1)
    
    # Mean FD (excluding first timepoint which has no derivative)
    mean_fd = np.mean(fd_per_timepoint)
    
    return float(mean_fd)

def is_motion_excluded(mean_fd: float, threshold: Optional[float] = None) -> bool:
    """
    Check if a subject should be excluded based on motion.
    
    Args:
        mean_fd: Mean framewise displacement value.
        threshold: FD threshold (mm). If None, uses config value.
    
    Returns:
        True if subject should be excluded (Mean FD > threshold).
    """
    if threshold is None:
        config = get_config()
        threshold = config['fd_threshold']
    
    return mean_fd > threshold

def log_motion_exclusion(subject_id: str, mean_fd: float) -> None:
    """Log a motion-based exclusion."""
    log_exclusion(
        subject_id=subject_id,
        reason='Motion',
        metadata={'Mean_FD': mean_fd}
    )

def filter_by_motion(df: pd.DataFrame, threshold: Optional[float] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter DataFrame to exclude subjects with excessive motion.
    
    Args:
        df: DataFrame with 'Subject_ID' and 'Mean_FD' columns.
        threshold: FD threshold (mm). If None, uses config value.
    
    Returns:
        Tuple of (filtered_df, list_of_excluded_subject_ids).
    """
    if 'Mean_FD' not in df.columns:
        logger.warning("Mean_FD column not found in DataFrame. Skipping motion filter.")
        return df, []
    
    if threshold is None:
        config = get_config()
        threshold = config['fd_threshold']
    
    # Identify subjects exceeding threshold
    excluded_mask = df['Mean_FD'] > threshold
    excluded_subjects = df[excluded_mask]['Subject_ID'].tolist()
    
    # Log exclusions
    for subject_id in excluded_subjects:
        mean_fd = df[df['Subject_ID'] == subject_id]['Mean_FD'].iloc[0]
        log_motion_exclusion(subject_id, mean_fd)
    
    # Filter
    filtered_df = df[~excluded_mask].reset_index(drop=True)
    
    logger.info(
        f"Motion filtering: Excluded {len(excluded_subjects)} subjects "
        f"with Mean FD > {threshold} mm. Retained {len(filtered_df)} subjects."
    )
    
    return filtered_df, excluded_subjects
