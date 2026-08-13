"""
Representational Similarity Analysis (RSA) utilities.
"""
import numpy as np
from scipy.spatial.distance import pdist, squareform
import logging
import code.config as config

logger = logging.getLogger(__name__)

def compute_dissimilarity_matrix(timecourses):
    """
    Compute the dissimilarity matrix (1 - correlation) for a set of timecourses.
    
    Args:
        timecourses (np.array): 2D array (n_events, n_voxels) or 3D (n_events, n_timepoints, n_voxels).
    
    Returns:
        np.array: Dissimilarity matrix.
    """
    if timecourses.ndim == 3:
        # Average over timepoints if necessary
        timecourses = timecourses.mean(axis=1)
    
    # Use correlation distance
    dist = pdist(timecourses, metric='correlation')
    dissimilarity_matrix = squareform(dist)
    return dissimilarity_matrix

def compare_early_late(early_matrix, late_matrix):
    """
    Compare Early vs. Late event dissimilarity matrices.
    
    Returns:
        float: Mean difference in dissimilarity.
    """
    diff = np.mean(early_matrix) - np.mean(late_matrix)
    logger.info(f"Mean Early-Late dissimilarity difference: {diff}")
    return diff
