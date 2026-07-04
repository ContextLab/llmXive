"""
Compute intra-modal consistency metrics using cross-correlation analysis.

This module implements the calculation of consistency metrics between
facial and vocal features using max absolute cross-correlation within
a specified time lag window.
"""
import numpy as np
from typing import Optional
from logging_config import get_logger
from utils import handle_corrupted_file

logger = get_logger(__name__)

def compute_max_abs_cross_correlation(
    features: np.ndarray, 
    max_lag: int = 20,
    sample_rate: int = 25
) -> float:
    """
    Compute the maximum absolute cross-correlation between feature channels.
    
    This function calculates the cross-correlation between all pairs of feature
    channels and returns the maximum absolute correlation value within the
    specified lag window.
    
    Parameters
    ----------
    features : np.ndarray
        2D array of shape (n_samples, n_features) containing time-series features
    max_lag : int
        Maximum lag (in samples) to consider for cross-correlation
    sample_rate : int
        Sample rate in Hz (default 25 Hz, typical for OpenFace)
    
    Returns
    -------
    float
        Maximum absolute cross-correlation value (normalized between 0 and 1)
        Returns NaN if input is invalid or no correlation can be computed
    """
    if features is None or features.size == 0:
        logger.warning("Empty or None features provided")
        return np.nan
    
    if not isinstance(features, np.ndarray):
        logger.error(f"Invalid input type: {type(features)}")
        return np.nan
    
    if features.ndim != 2:
        logger.error(f"Features must be 2D array, got {features.ndim}D")
        return np.nan
    
    n_samples, n_features = features.shape
    
    if n_features < 2:
        logger.warning("Need at least 2 features for cross-correlation")
        return np.nan
    
    if n_samples == 0:
        return np.nan
    
    # Handle NaN values by replacing with mean of each feature
    features_clean = features.copy()
    for i in range(n_features):
        col = features_clean[:, i]
        if np.any(np.isnan(col)):
            mean_val = np.nanmean(col)
            features_clean[:, i] = np.where(np.isnan(col), mean_val, col)
            logger.debug(f"Replaced {np.sum(np.isnan(col))} NaN values in feature {i} with mean")
    
    max_corr = 0.0
    n_pairs = 0
    
    # Compute cross-correlation for all feature pairs
    for i in range(n_features):
        for j in range(i + 1, n_features):
            try:
                # Compute cross-correlation
                corr = np.correlate(
                    features_clean[:, i] - np.mean(features_clean[:, i]),
                    features_clean[:, j] - np.mean(features_clean[:, j]),
                    mode='full'
                )
                
                # Normalize
                corr = corr / (np.std(features_clean[:, i]) * np.std(features_clean[:, j]) * n_samples)
                
                # Extract the relevant lag window (centered at 0)
                mid = len(corr) // 2
                start_idx = max(0, mid - max_lag)
                end_idx = min(len(corr), mid + max_lag + 1)
                
                window_corr = corr[start_idx:end_idx]
                
                # Get maximum absolute correlation in the window
                max_window_corr = np.max(np.abs(window_corr))
                
                if max_window_corr > max_corr:
                    max_corr = max_window_corr
                
                n_pairs += 1
                
            except Exception as e:
                logger.warning(f"Error computing cross-correlation for pair ({i}, {j}): {e}")
                continue
    
    if n_pairs == 0:
        logger.warning("No valid cross-correlation pairs computed")
        return np.nan
    
    # Normalize to [0, 1] range (already normalized by correlation formula)
    # But ensure it doesn't exceed 1 due to numerical errors
    max_corr = min(max_corr, 1.0)
    max_corr = max(max_corr, 0.0)
    
    logger.debug(f"Computed cross-correlation for {n_pairs} pairs, max corr: {max_corr:.4f}")
    return max_corr

def compute_consistency_score(
    facial_features: np.ndarray,
    vocal_features: np.ndarray,
    max_lag_samples: int = 50,  # ~2 seconds at 25Hz
    sample_rate: int = 25
) -> dict:
    """
    Compute intra-modal and inter-modal consistency scores.
    
    Parameters
    ----------
    facial_features : np.ndarray
        2D array of facial features (n_samples, n_facial_features)
    vocal_features : np.ndarray
        2D array of vocal features (n_samples, n_vocal_features)
    max_lag_samples : int
        Maximum lag in samples to consider
    sample_rate : int
        Sample rate in Hz
    
    Returns
    -------
    dict
        Dictionary containing consistency scores:
        - 'facial_consistency': intra-modal facial consistency
        - 'vocal_consistency': intra-modal vocal consistency
        - 'inter_modal_consistency': inter-modal consistency
        - 'overall_consistency': average of all three
    """
    logger.info("Computing consistency scores")
    
    # Compute intra-modal consistency
    facial_consistency = compute_max_abs_cross_correlation(
        facial_features, 
        max_lag=max_lag_samples,
        sample_rate=sample_rate
    )
    
    vocal_consistency = compute_max_abs_cross_correlation(
        vocal_features,
        max_lag=max_lag_samples,
        sample_rate=sample_rate
    )
    
    # Compute inter-modal consistency (concatenate features)
    if facial_features.shape[0] == vocal_features.shape[0]:
        combined_features = np.hstack([facial_features, vocal_features])
        inter_modal_consistency = compute_max_abs_cross_correlation(
            combined_features,
            max_lag=max_lag_samples,
            sample_rate=sample_rate
        )
    else:
        logger.warning("Facial and vocal features have different lengths, skipping inter-modal")
        inter_modal_consistency = np.nan
    
    # Calculate overall consistency
    valid_scores = [s for s in [facial_consistency, vocal_consistency, inter_modal_consistency] 
                   if not np.isnan(s)]
    
    if len(valid_scores) > 0:
        overall_consistency = np.mean(valid_scores)
    else:
        overall_consistency = np.nan
    
    result = {
        'facial_consistency': float(facial_consistency),
        'vocal_consistency': float(vocal_consistency),
        'inter_modal_consistency': float(inter_modal_consistency),
        'overall_consistency': float(overall_consistency)
    }
    
    logger.info(f"Consistency scores computed: {result}")
    return result

def validate_feature_input(
    features: np.ndarray,
    min_samples: int = 100,
    min_features: int = 2
) -> bool:
    """
    Validate that feature input meets minimum requirements.
    
    Parameters
    ----------
    features : np.ndarray
        Feature array to validate
    min_samples : int
        Minimum number of samples required
    min_features : int
        Minimum number of features required
    
    Returns
    -------
    bool
        True if input is valid, False otherwise
    """
    if features is None:
        logger.error("Features is None")
        return False
    
    if not isinstance(features, np.ndarray):
        logger.error(f"Features must be numpy array, got {type(features)}")
        return False
    
    if features.ndim != 2:
        logger.error(f"Features must be 2D, got {features.ndim}D")
        return False
    
    n_samples, n_features = features.shape
    
    if n_samples < min_samples:
        logger.error(f"Insufficient samples: {n_samples} < {min_samples}")
        return False
    
    if n_features < min_features:
        logger.error(f"Insufficient features: {n_features} < {min_features}")
        return False
    
    if np.any(np.isnan(features)):
        nan_count = np.sum(np.isnan(features))
        logger.warning(f"Found {nan_count} NaN values in features")
        # Don't fail, but warn
    
    return True

def process_interaction_features(
    interaction_id: str,
    features_data: dict
) -> dict:
    """
    Process features for a single interaction and compute consistency metrics.
    
    Parameters
    ----------
    interaction_id : str
        Unique identifier for the interaction
    features_data : dict
        Dictionary containing 'facial' and 'vocal' feature arrays
    
    Returns
    -------
    dict
        Dictionary with interaction_id and computed consistency scores
    """
    logger.info(f"Processing interaction: {interaction_id}")
    
    facial_features = features_data.get('facial')
    vocal_features = features_data.get('vocal')
    
    if facial_features is None or vocal_features is None:
        logger.error(f"Missing features for interaction {interaction_id}")
        return {
            'interaction_id': interaction_id,
            'error': 'Missing features',
            'facial_consistency': np.nan,
            'vocal_consistency': np.nan,
            'inter_modal_consistency': np.nan,
            'overall_consistency': np.nan
        }
    
    # Validate inputs
    if not validate_feature_input(facial_features) or not validate_feature_input(vocal_features):
        logger.error(f"Invalid features for interaction {interaction_id}")
        return {
            'interaction_id': interaction_id,
            'error': 'Invalid features',
            'facial_consistency': np.nan,
            'vocal_consistency': np.nan,
            'inter_modal_consistency': np.nan,
            'overall_consistency': np.nan
        }
    
    # Compute consistency scores
    scores = compute_consistency_score(facial_features, vocal_features)
    scores['interaction_id'] = interaction_id
    
    return scores
