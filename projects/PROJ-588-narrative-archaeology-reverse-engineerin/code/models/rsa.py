"""
Representational Similarity Analysis (RSA) utilities.
Computes dissimilarity matrices and compares Early vs Late events.
"""
import numpy as np
from scipy.spatial.distance import pdist, squareform
import logging
import code.config as config

logger = logging.getLogger(__name__)

def compute_dissimilarity_matrix(data, metric='correlation'):
    """
    Compute pairwise dissimilarity matrix.
    """
    # data shape: (n_samples, n_features)
    if len(data) == 0:
        return np.array([])
    
    # Convert correlation distance to dissimilarity (1 - r)
    dists = pdist(data, metric=metric)
    return squareform(dists)

def compare_early_late(early_data, late_data):
    """
    Compare Early vs Late event patterns.
    Computes mean dissimilarity within Early, within Late, and between.
    """
    if len(early_data) == 0 or len(late_data) == 0:
        logger.warning("Empty data for Early/Late comparison")
        return {}

    # Within-group dissimilarities
    early_dists = compute_dissimilarity_matrix(early_data)
    late_dists = compute_dissimilarity_matrix(late_data)
    
    # Between-group dissimilarities (Early vs Late)
    # Concatenate and compute, then extract cross terms
    combined = np.vstack([early_data, late_data])
    combined_dists = compute_dissimilarity_matrix(combined)
    
    n_early = len(early_data)
    n_late = len(late_data)
    
    # Extract cross-block
    between_dists = combined_dists[:n_early, n_early:]
    
    return {
        "mean_within_early": float(np.mean(early_dists)),
        "mean_within_late": float(np.mean(late_dists)),
        "mean_between": float(np.mean(between_dists)),
        "early_shape": early_data.shape,
        "late_shape": late_data.shape
    }
