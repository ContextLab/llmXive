"""
Edge case handling utilities for Differential Privacy confidence interval analysis.

This module encapsulates reusable functions to handle:
1. Clamping noise scale for small epsilon values to prevent numerical instability.
2. Collinearity detection in regression analysis.
3. Minimum sample size enforcement for bootstrap resampling.
"""

import numpy as np
from typing import Union, Tuple, Optional, Dict, Any
from scipy import stats
import warnings


# Constants for edge case handling
MIN_EPSILON = 1e-6  # Minimum epsilon to prevent division by zero
MIN_SAMPLE_SIZE_BOOTSTRAP = 30  # Minimum sample size for reliable bootstrap
MIN_SAMPLE_SIZE_REGRESSION = 10  # Minimum sample size for regression
VARIANCE_FLOOR = 1e-10  # Floor for variance to prevent numerical issues
COLLINEARITY_THRESHOLD = 0.99  # Correlation threshold for detecting collinearity


def clamp_noise_scale(
    epsilon: float,
    sensitivity: float,
    noise_type: str = "laplace",
    min_epsilon: float = MIN_EPSILON
) -> Tuple[float, bool]:
    """
    Clamp the noise scale parameter to prevent numerical instability for very small epsilon.

    For Laplace noise: scale = sensitivity / epsilon
    For Gaussian noise: scale = sensitivity * sqrt(2 * log(1.25/delta)) / epsilon

    Args:
        epsilon: Privacy budget (must be > 0)
        sensitivity: Query sensitivity
        noise_type: Type of noise ("laplace" or "gaussian")
        min_epsilon: Minimum epsilon threshold

    Returns:
        Tuple of (clamped_scale, was_clamped)
    """
    if epsilon <= 0:
        warnings.warn(f"Epsilon {epsilon} is non-positive. Clamping to {min_epsilon}.")
        epsilon = min_epsilon
        was_clamped = True
    elif epsilon < min_epsilon:
        warnings.warn(f"Epsilon {epsilon} is below threshold {min_epsilon}. Clamping to {min_epsilon}.")
        epsilon = min_epsilon
        was_clamped = True
    else:
        was_clamped = False

    if noise_type.lower() == "laplace":
        scale = sensitivity / epsilon
    elif noise_type.lower() == "gaussian":
        # Using delta = 1e-5 as a common default for approximate DP
        delta = 1e-5
        scale = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
    else:
        raise ValueError(f"Unsupported noise type: {noise_type}. Use 'laplace' or 'gaussian'.")

    # Ensure scale is not too small (prevents division by zero later)
    scale = max(scale, 1e-10)

    return scale, was_clamped


def detect_collinearity(X: np.ndarray, threshold: float = COLLINEARITY_THRESHOLD) -> Dict[str, Any]:
    """
    Detect collinearity in regression design matrix X.

    Uses Variance Inflation Factor (VIF) and correlation matrix to detect
    multicollinearity issues that would destabilize regression coefficient estimates.

    Args:
        X: Design matrix (n_samples, n_features), should include intercept if needed
        threshold: Correlation threshold for flagging collinearity

    Returns:
        Dictionary with:
        - 'has_collinearity': bool
        - 'max_correlation': float
        - 'vif_values': list of VIF for each feature
        - 'problematic_pairs': list of (i, j) pairs with high correlation
        - 'condition_number': float (matrix condition number)
    """
    if X.ndim == 1:
        X = X.reshape(-1, 1)

    n_samples, n_features = X.shape

    if n_samples < n_features:
        return {
            'has_collinearity': True,
            'max_correlation': float('inf'),
            'vif_values': [float('inf')] * n_features,
            'problematic_pairs': [(i, j) for i in range(n_features) for j in range(i+1, n_features)],
            'condition_number': float('inf'),
            'message': "Sample size smaller than feature count - perfect multicollinearity"
        }

    # Compute correlation matrix
    try:
        corr_matrix = np.corrcoef(X, rowvar=False)
        if np.any(np.isnan(corr_matrix)):
            # Handle case with constant features
            corr_matrix = np.eye(n_features)
    except:
        corr_matrix = np.eye(n_features)

    # Find max off-diagonal correlation
    mask = ~np.eye(n_features, dtype=bool)
    max_corr = np.max(np.abs(corr_matrix[mask])) if n_features > 1 else 0.0

    # Compute VIF (Variance Inflation Factor)
    vif_values = []
    for i in range(n_features):
        try:
            # Regress feature i against all other features
            y = X[:, i]
            X_other = np.delete(X, i, axis=1)
            if X_other.shape[1] > 0:
                # Add intercept if not present
                if not np.allclose(X_other.mean(axis=0), 0) or n_features == 2:
                    X_other_with_intercept = np.column_stack([np.ones(n_samples), X_other])
                else:
                    X_other_with_intercept = X_other

                coeffs, residuals, rank, s = np.linalg.lstsq(X_other_with_intercept, y, rcond=None)
                if rank < X_other_with_intercept.shape[1]:
                    vif = float('inf')
                else:
                    # R-squared from the auxiliary regression
                    ss_res = np.sum((y - X_other_with_intercept @ coeffs) ** 2)
                    ss_tot = np.sum((y - y.mean()) ** 2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                    vif = 1 / (1 - r_squared) if (1 - r_squared) > 1e-10 else float('inf')
            else:
                vif = 1.0  # Single feature, no collinearity possible
        except:
            vif = float('inf')
        vif_values.append(vif)

    # Identify problematic pairs
    problematic_pairs = []
    for i in range(n_features):
        for j in range(i + 1, n_features):
            if np.abs(corr_matrix[i, j]) > threshold:
                problematic_pairs.append((i, j))

    # Compute condition number
    try:
        condition_number = np.linalg.cond(X)
    except:
        condition_number = float('inf')

    has_collinearity = (
        max_corr > threshold or
        any(v > 10 for v in vif_values) or
        condition_number > 1e10
    )

    return {
        'has_collinearity': has_collinearity,
        'max_correlation': float(max_corr),
        'vif_values': vif_values,
        'problematic_pairs': problematic_pairs,
        'condition_number': float(condition_number),
        'message': "Collinearity detected" if has_collinearity else "No significant collinearity"
    }


def enforce_minimum_sample_size(
    data: np.ndarray,
    min_size: int = MIN_SAMPLE_SIZE_BOOTSTRAP,
    method: str = "truncate"
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Enforce minimum sample size requirements for bootstrap/resampling operations.

    Args:
        data: Input data array
        min_size: Minimum required sample size
        method: How to handle insufficient data ("truncate", "error", "warn")

    Returns:
        Tuple of (processed_data, status_info)
        status_info contains:
        - 'original_size': int
        - 'final_size': int
        - 'was_truncated': bool
        - 'enforcement_applied': bool
        - 'message': str
    """
    if data.ndim == 1:
        n = len(data)
    else:
        n = data.shape[0]

    status = {
        'original_size': n,
        'final_size': n,
        'was_truncated': False,
        'enforcement_applied': False,
        'message': "Sample size sufficient"
    }

    if n < min_size:
        status['enforcement_applied'] = True
        status['message'] = f"Sample size {n} below minimum {min_size}"

        if method == "error":
            raise ValueError(
                f"Insufficient samples: {n} < {min_size}. "
                f"Bootstrap requires at least {min_size} samples."
            )
        elif method == "warn":
            warnings.warn(
                f"Insufficient samples: {n} < {min_size}. "
                f"Bootstrap results may be unreliable."
            )
            status['message'] += " - proceeding with warning"
        elif method == "truncate":
            # Use available data but flag the issue
            status['message'] += " - proceeding with available data"
        else:
            raise ValueError(f"Unknown method: {method}. Use 'truncate', 'error', or 'warn'.")

    return data, status


def validate_covariance_matrix(
    cov_matrix: np.ndarray,
    floor: float = VARIANCE_FLOOR
) -> Tuple[np.ndarray, bool]:
    """
    Ensure covariance matrix is positive semi-definite and numerically stable.

    Args:
        cov_matrix: Input covariance matrix
        floor: Minimum value for diagonal elements

    Returns:
        Tuple of (valid_cov_matrix, was_corrected)
    """
    was_corrected = False
    cov = cov_matrix.copy()

    # Ensure diagonal is positive
    np.fill_diagonal(cov, np.maximum(np.diag(cov), floor))

    # Check for positive semi-definiteness
    try:
        eigvals = np.linalg.eigvalsh(cov)
        if np.min(eigvals) < 0:
            # Apply nearest PSD correction
            cov = (cov + cov.T) / 2  # Symmetrize
            eigvals, eigvecs = np.linalg.eigh(cov)
            eigvals = np.maximum(eigvals, 0)
            cov = eigvecs @ np.diag(eigvals) @ eigvecs.T
            was_corrected = True
    except:
        # Fallback: return identity scaled by average variance
        avg_var = np.mean(np.diag(cov_matrix))
        cov = np.eye(cov_matrix.shape[0]) * avg_var
        was_corrected = True

    return cov, was_corrected


def handle_zero_variance(
    data: np.ndarray,
    floor: float = VARIANCE_FLOOR
) -> Tuple[np.ndarray, bool]:
    """
    Handle zero or near-zero variance in data to prevent division by zero.

    Args:
        data: Input data array
        floor: Minimum variance floor

    Returns:
        Tuple of (processed_data, was_modified)
    """
    was_modified = False
    data = np.asarray(data, dtype=np.float64)

    if data.ndim == 1:
        var = np.var(data)
        if var < floor:
            # Add tiny noise to break degeneracy
            data = data + np.random.normal(0, np.sqrt(floor), size=data.shape)
            was_modified = True
    else:
        vars = np.var(data, axis=0)
        if np.any(vars < floor):
            for i in range(data.shape[1]):
                if vars[i] < floor:
                    data[:, i] = data[:, i] + np.random.normal(0, np.sqrt(floor), size=data.shape[0])
            was_modified = True

    return data, was_modified