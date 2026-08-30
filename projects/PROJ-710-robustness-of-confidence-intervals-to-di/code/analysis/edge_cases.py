"""
Edge case handling utilities for DP noise and statistical analysis.

This module provides functions to handle specific edge cases that can arise
during differential privacy noise injection and statistical inference:
1. Clamping noise scale when it exceeds data range (small epsilon)
2. Detecting collinearity in regression predictors
3. Enforcing minimum sample sizes for bootstrap validity
"""
import numpy as np
from typing import Union, Tuple, Optional, Dict, Any, List
from scipy import stats
import warnings
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)


def clamp_noise_scale(
    data: Union[np.ndarray, List[float]],
    noise_scale: float,
    epsilon: float,
    sensitivity: float = 1.0
) -> Tuple[float, bool, str]:
    """
    Clamp the noise scale if it exceeds the data range to prevent invalid noise injection.
    
    In differential privacy, the noise scale (sigma for Gaussian, b for Laplace) is 
    inversely proportional to epsilon: scale = sensitivity / epsilon (for Laplace) or 
    scale = sensitivity * sqrt(2 * ln(1.25/delta)) / epsilon (for Gaussian).
    
    When epsilon is very small, the noise scale can become extremely large, potentially
    exceeding the range of the data itself, which would make the noisy data meaningless.
    
    This function checks if the noise scale is reasonable relative to the data range
    and clamps it if necessary.
    
    Args:
        data: The input data array.
        noise_scale: The calculated noise scale (sigma or b).
        epsilon: The privacy budget.
        sensitivity: The sensitivity of the query (default 1.0).
        
    Returns:
      A tuple containing:
          - clamped_scale: The noise scale to use (possibly clamped).
          - was_clamped: Boolean indicating if clamping was applied.
          - reason: A string describing the action taken.
    """
    if not isinstance(data, np.ndarray):
        data = np.array(data)
    
    if data.size == 0:
        raise ValueError("Input data cannot be empty.")
    
    if epsilon <= 0:
        raise ValueError("Epsilon must be positive.")
    
    if noise_scale <= 0:
        raise ValueError("Noise scale must be positive.")
        
    data_min = np.min(data)
    data_max = np.max(data)
    data_range = data_max - data_min
    
    # Handle constant data (zero range)
    if data_range == 0:
        # If all values are the same, any noise will change the distribution
        # We set a default small scale based on machine epsilon or a small fraction
        # of typical data magnitude
        default_scale = np.finfo(float).eps * max(np.abs(data_min), 1.0)
        if default_scale == 0:
            default_scale = 1e-9
        
        logger.warning(
            f"Data has zero range (constant value {data_min}). "
            f"Setting noise scale to {default_scale:.2e}."
        )
        return default_scale, True, "Data range is zero; using minimal default scale."
    
    # Define a threshold: noise scale should not exceed the data range.
    # A stricter threshold might be 10% of the range, but we use 100% here
    # to allow for significant noise while ensuring the signal isn't completely
    # overwhelmed by noise.
    max_allowed_scale = data_range
    
    # Alternatively, we could use a fraction of the range (e.g., 0.5 * data_range)
    # to ensure the noise doesn't dominate the data entirely.
    # Let's use a conservative approach: if noise_scale > data_range, clamp it.
    if noise_scale > max_allowed_scale:
        clamped_scale = max_allowed_scale
        reason = (
            f"Noise scale ({noise_scale:.4f}) exceeds data range ({data_range:.4f}). "
            f"Clamped to data range to prevent signal obliteration. "
            f"Effective epsilon: {sensitivity / clamped_scale:.4f}."
        )
        logger.warning(reason)
        warnings.warn(reason, UserWarning)
        return clamped_scale, True, reason
    
    return noise_scale, False, "Noise scale within acceptable range."


def detect_collinearity(
    X: np.ndarray,
    threshold: float = 1e-6
) -> Tuple[List[int], List[str]]:
    """
    Detect collinear predictors in a regression design matrix.
    
    This function checks for linear dependencies among the columns of X
    by examining the condition number of the matrix or using rank deficiency.
    If collinearity is detected, it identifies which columns are likely
    redundant and suggests dropping one.
    
    Args:
        X: Design matrix (n_samples, n_features).
        threshold: Threshold for determining collinearity (based on condition number).
                   A condition number > threshold indicates potential collinearity.
                   
    Returns:
        A tuple containing:
            - drop_indices: List of column indices to drop.
            - messages: List of log messages describing the collinearity found.
    """
    if X.ndim == 1:
        X = X.reshape(-1, 1)
        
    n_samples, n_features = X.shape
    
    if n_features <= 1:
        return [], ["Only one predictor; no collinearity possible."]
        
    if n_samples < n_features:
        # Underdetermined system; all features beyond n_samples are linearly dependent
        drop_indices = list(range(n_features))
        messages = [
            f"Underdetermined system: {n_samples} samples < {n_features} features. "
            f"All features are linearly dependent."
        ]
        logger.warning(messages[0])
        return drop_indices, messages
    
    # Calculate condition number
    try:
        # Use SVD to compute condition number
        _, s, _ = np.linalg.svd(X, full_matrices=False)
        condition_number = s[0] / s[-1] if s[-1] > 0 else np.inf
    except np.linalg.LinAlgError:
        condition_number = np.inf
    
    messages = []
    drop_indices = []
    
    if condition_number > threshold:
        msg = (
            f"High condition number ({condition_number:.2e}) detected. "
            f"Potential collinearity among predictors."
        )
        logger.warning(msg)
        messages.append(msg)
        
        # Identify redundant columns by checking for near-zero singular values
        # and projecting onto the null space, or simpler: check correlation matrix
        # For simplicity in this implementation, we'll drop the last column if
        # the condition number is too high, as a heuristic.
        # A more robust approach would involve QR decomposition with pivoting.
        drop_idx = n_features - 1
        drop_indices.append(drop_idx)
        
        msg_drop = (
            f"Collinearity detected. Dropping column index {drop_idx} "
            f"(last predictor) to improve numerical stability."
        )
        logger.warning(msg_drop)
        messages.append(msg_drop)
    
    if not drop_indices:
        messages.append("No significant collinearity detected.")
        
    return drop_indices, messages


def enforce_min_sample_size(
    n: int,
    min_size: int = 10,
    raise_on_fail: bool = False
) -> Tuple[bool, str]:
    """
    Enforce minimum sample size for valid bootstrap resampling.
    
    Bootstrap resampling requires a sufficient sample size to produce
    reliable confidence intervals. A common rule of thumb is n >= 10.
    
    Args:
        n: The current sample size.
        min_size: The minimum required sample size (default 10).
        raise_on_fail: If True, raise a ValueError instead of returning a status.
        
    Returns:
        A tuple containing:
            - is_valid: Boolean indicating if n >= min_size.
            - message: A string describing the validation result.
    """
    if n < min_size:
        msg = (
            f"Sample size ({n}) is below minimum threshold ({min_size}). "
            f"Bootstrap resampling may yield unreliable results."
        )
        logger.warning(msg)
        if raise_on_fail:
            raise ValueError(msg)
        return False, msg
    
    msg = f"Sample size ({n}) meets minimum threshold ({min_size})."
    logger.debug(msg)
    return True, msg


def validate_covariance_matrix(
    cov_matrix: np.ndarray,
    tol: float = 1e-8
) -> Tuple[bool, str]:
    """
    Validate that a covariance matrix is positive semi-definite.
    
    Args:
        cov_matrix: The covariance matrix to validate.
        tol: Tolerance for eigenvalue check.
        
    Returns:
        A tuple containing:
            - is_valid: Boolean indicating if the matrix is PSD.
            - message: A string describing the validation result.
    """
    if cov_matrix.ndim != 2 or cov_matrix.shape[0] != cov_matrix.shape[1]:
        msg = "Covariance matrix must be square."
        logger.error(msg)
        return False, msg
        
    try:
        eigenvalues = np.linalg.eigvalsh(cov_matrix)
        if np.any(eigenvalues < -tol):
            min_eig = np.min(eigenvalues)
            msg = (
                f"Covariance matrix is not positive semi-definite. "
                f"Minimum eigenvalue: {min_eig:.2e}."
            )
            logger.error(msg)
            return False, msg
        return True, "Covariance matrix is valid (positive semi-definite)."
    except np.linalg.LinAlgError as e:
        msg = f"Error computing eigenvalues of covariance matrix: {e}"
        logger.error(msg)
        return False, msg


def handle_zero_variance(
    data: np.ndarray,
    epsilon: float,
    noise_type: str = 'laplace'
) -> Tuple[np.ndarray, str]:
    """
    Handle cases where data has zero variance (constant).
    
    When data has zero variance, standard error is zero, and confidence intervals
    cannot be constructed in the usual way. This function adds a tiny amount of
    noise to break the degeneracy if necessary, or returns a specific status.
    
    Args:
        data: Input data array.
        epsilon: Privacy budget (used to determine noise scale if needed).
        noise_type: Type of noise ('laplace' or 'gaussian').
        
    Returns:
        A tuple containing:
            - processed_data: The data (possibly perturbed).
            - status: A string describing the action taken.
    """
    if np.var(data) == 0:
        msg = "Data has zero variance. Adding minimal noise to break degeneracy."
        logger.warning(msg)
        # Add a tiny amount of noise proportional to machine epsilon
        noise_scale = np.finfo(float).eps * max(np.abs(np.mean(data)), 1.0)
        if noise_scale == 0:
            noise_scale = 1e-12
            
        if noise_type == 'laplace':
            noise = np.random.laplace(0, noise_scale, size=data.shape)
        else:  # gaussian
            noise = np.random.normal(0, noise_scale, size=data.shape)
            
        processed_data = data + noise
        return processed_data, f"Zero variance handled; added noise with scale {noise_scale:.2e}."
    
    return data, "Data variance is non-zero; no special handling needed."


def get_edge_case_status(
    data: np.ndarray,
    noise_scale: float,
    epsilon: float,
    X: Optional[np.ndarray] = None,
    min_sample_size: int = 10
) -> Dict[str, Any]:
    """
    Comprehensive edge case check for a simulation condition.
    
    Args:
        data: The data array for the current simulation.
        noise_scale: The calculated noise scale.
        epsilon: The privacy budget.
        X: Optional design matrix for regression (for collinearity check).
        min_sample_size: Minimum sample size threshold.
        
    Returns:
        A dictionary containing status flags and messages for all checked edge cases.
    """
    status = {
        "clamp_noise": {},
        "collinearity": {},
        "min_sample_size": {},
        "zero_variance": {},
        "overall_valid": True
    }
    
    # Check noise scale
    clamped_scale, was_clamped, msg = clamp_noise_scale(data, noise_scale, epsilon)
    status["clamp_noise"] = {
        "was_clamped": was_clamped,
        "original_scale": noise_scale,
        "clamped_scale": clamped_scale,
        "message": msg
    }
    if was_clamped:
        status["overall_valid"] = False
        
    # Check sample size
    n = len(data)
    is_valid, msg = enforce_min_sample_size(n, min_sample_size)
    status["min_sample_size"] = {
        "sample_size": n,
        "is_valid": is_valid,
        "message": msg
    }
    if not is_valid:
        status["overall_valid"] = False
        
    # Check zero variance
    _, msg = handle_zero_variance(data, epsilon)
    status["zero_variance"] = {
        "message": msg
    }
    
    # Check collinearity if X is provided
    if X is not None:
        drop_indices, messages = detect_collinearity(X)
        status["collinearity"] = {
            "drop_indices": drop_indices,
            "messages": messages,
            "has_collinearity": len(drop_indices) > 0
        }
        if len(drop_indices) > 0:
            status["overall_valid"] = False
    
    return status
