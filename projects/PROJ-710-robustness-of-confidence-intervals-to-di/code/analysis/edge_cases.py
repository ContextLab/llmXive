"""
Edge case handling for DP noise and statistical analysis.
Implements clamping, collinearity detection, and sample size enforcement.
"""
import numpy as np
from typing import Union, Tuple, Optional, Dict, Any, List
from scipy import stats
import warnings
import logging

logger = logging.getLogger(__name__)

def clamp_noise_scale(data: Union[np.ndarray, Any], noise_scale: float, noise_type: str) -> float:
    """
    Clamps the noise scale to a reasonable fraction of the data range.
    Prevents noise from overwhelming the signal in small samples.
    """
    if isinstance(data, dict) or hasattr(data, 'values'):
        # Assume pandas-like
        data_array = np.array(data.values.flatten())
    else:
        data_array = np.array(data).flatten()
    
    if len(data_array) == 0:
        return noise_scale
    
    data_range = np.max(data_array) - np.min(data_array)
    if data_range == 0:
        # If all data is the same, noise scale should be 0 or very small
        return 0.0
    
    # Clamp to max 50% of the range
    max_scale = data_range * 0.5
    if noise_scale > max_scale:
        logger.warning(f"Noise scale {noise_scale} exceeds 50% of data range {data_range}. Clamping to {max_scale}.")
        return max_scale
    return noise_scale

def detect_collinearity(X: np.ndarray, threshold: float = 0.95) -> Dict[str, Any]:
    """
    Detects collinearity in predictor matrix X.
    Returns status and cleaned X if collinearity is detected.
    """
    if X.shape[1] < 2:
        return {"is_valid": True, "message": "No collinearity check needed for < 2 features", "clean_X": X}
    
    try:
        corr_matrix = np.corrcoef(X.T)
        # Check for high correlation between any pair
        for i in range(corr_matrix.shape[0]):
            for j in range(i + 1, corr_matrix.shape[1]):
                if abs(corr_matrix[i, j]) > threshold:
                    msg = f"High collinearity detected between features {i} and {j} (r={corr_matrix[i,j]:.2f})"
                    logger.warning(msg)
                    # Drop feature j
                    clean_X = np.delete(X, j, axis=1)
                    return {"is_valid": False, "message": msg, "clean_X": clean_X}
        
        return {"is_valid": True, "message": "No collinearity detected", "clean_X": X}
    except Exception as e:
        logger.error(f"Collinearity check failed: {e}")
        return {"is_valid": False, "message": str(e), "clean_X": X}

def enforce_min_sample_size(n: int, min_size: int = 10) -> Dict[str, Any]:
    """
    Enforces minimum sample size for valid bootstrap.
    """
    if n < min_size:
        msg = f"Sample size {n} is less than minimum {min_size}."
        logger.warning(msg)
        return {"is_valid": False, "message": msg, "n": n}
    return {"is_valid": True, "message": "Sample size sufficient", "n": n}

def validate_covariance_matrix(cov: np.ndarray) -> bool:
    """
    Validates that a covariance matrix is positive semi-definite.
    """
    try:
        np.linalg.cholesky(cov)
        return True
    except np.linalg.LinAlgError:
        return False

def handle_zero_variance(data: np.ndarray) -> np.ndarray:
    """
    Handles zero variance in data by adding a tiny epsilon.
    """
    if np.var(data) == 0:
        warnings.warn("Zero variance detected. Adding small epsilon.")
        return data + 1e-10
    return data

def get_edge_case_status(noise_scale: float, data_range: float, n_samples: int) -> Dict[str, Any]:
    """
    Returns a summary of edge case status.
    """
    status = {
        "noise_clamped": noise_scale > data_range * 0.5,
        "sample_size_valid": n_samples >= 10,
        "data_range_valid": data_range > 0
    }
    return status
