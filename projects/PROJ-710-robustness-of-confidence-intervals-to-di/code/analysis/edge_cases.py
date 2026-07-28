"""
Edge case handling utilities for the DP-CI robustness pipeline.

This module provides reusable functions to handle:
1. Clamping noise scale for small epsilon values
2. Collinearity detection in regression
3. Minimum sample size enforcement for bootstrap
4. Zero variance handling
5. Covariance matrix validation

These functions are designed to be called by the orchestration loop (main.py)
before or during simulation steps to ensure numerical stability and valid results.
"""

import numpy as np
from typing import Union, Tuple, Optional, Dict, Any, List
from scipy import stats
import warnings
import logging

# Configure logger
logger = logging.getLogger(__name__)


def clamp_noise_scale(
    epsilon: float,
    sensitivity: float,
    noise_type: str = "laplace",
    min_epsilon: float = 0.1,
    max_scale: Optional[float] = None
) -> Tuple[float, bool]:
    """
    Clamp noise scale parameters to prevent numerical instability for very small epsilon.

    For differential privacy, the noise scale is proportional to 1/epsilon.
    As epsilon approaches 0, the noise scale approaches infinity, causing
    numerical overflow and meaningless results.

    This function enforces a minimum epsilon threshold and optionally a maximum
    noise scale to ensure stable computations.

    Args:
        epsilon: The privacy budget (must be > 0)
        sensitivity: The global sensitivity of the query
        noise_type: Either "laplace" or "gaussian"
        min_epsilon: Minimum epsilon value to use (default: 0.1)
        max_scale: Maximum allowed noise scale (default: None, uses 10 * sensitivity)

    Returns:
        Tuple of (effective_epsilon, was_clamped):
            - effective_epsilon: The epsilon value actually used (may be clamped)
            - was_clamped: True if the original epsilon was below min_epsilon
    """
    if epsilon <= 0:
        raise ValueError(f"Epsilon must be positive, got {epsilon}")

    was_clamped = False
    effective_epsilon = epsilon

    # Clamp epsilon to minimum threshold
    if epsilon < min_epsilon:
        effective_epsilon = min_epsilon
        was_clamped = True
        logger.warning(
            f"Epsilon {epsilon} below minimum {min_epsilon}, "
            f"clamping to {min_epsilon} to prevent numerical instability"
        )

    # Calculate noise scale
    if noise_type.lower() == "laplace":
        # Laplace noise scale = sensitivity / epsilon
        scale = sensitivity / effective_epsilon
    elif noise_type.lower() == "gaussian":
        # Gaussian noise scale (simplified, assuming delta is handled elsewhere)
        # For (epsilon, delta)-DP, scale = sensitivity * sqrt(2 * ln(1.25/delta)) / epsilon
        # Using a simplified version here
        scale = sensitivity / effective_epsilon
    else:
        raise ValueError(f"Unknown noise type: {noise_type}. Use 'laplace' or 'gaussian'")

    # Enforce maximum scale if specified
    if max_scale is not None and scale > max_scale:
        effective_epsilon = sensitivity / max_scale
        was_clamped = True
        logger.warning(
            f"Noise scale {scale} exceeds maximum {max_scale}, "
            f"adjusting epsilon to {effective_epsilon:.4f}"
        )

    return effective_epsilon, was_clamped


def detect_collinearity(
    X: np.ndarray,
    tol: float = 1e-6,
    condition_number_threshold: float = 30.0
) -> Dict[str, Any]:
    """
    Detect collinearity in predictor matrix for regression analysis.

    This function checks for:
    1. Near-zero variance predictors
    2. High condition number (indicating multicollinearity)
    3. Perfect or near-perfect correlations between columns

    Args:
        X: Predictor matrix (n_samples, n_features)
        tol: Tolerance for detecting near-zero variance
        condition_number_threshold: Threshold above which collinearity is flagged

    Returns:
        Dictionary with keys:
            - 'is_collinear': bool, True if collinearity detected
            - 'condition_number': float, condition number of X^T X
            - 'near_zero_var': list, indices of near-zero variance columns
            - 'high_corr_pairs': list of tuples, pairs with correlation > 0.99
            - 'recommendation': str, suggested action
    """
    result = {
        'is_collinear': False,
        'condition_number': float('inf'),
        'near_zero_var': [],
        'high_corr_pairs': [],
        'recommendation': 'No issues detected'
    }

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    n_samples, n_features = X.shape

    if n_samples < n_features:
        result['is_collinear'] = True
        result['recommendation'] = (
            f"Samples ({n_samples}) < features ({n_features}). "
            "Cannot fit regression model. Consider dimensionality reduction."
        )
        return result

    # Check for near-zero variance columns
    col_stds = np.std(X, axis=0)
    near_zero_indices = np.where(col_stds < tol)[0].tolist()
    result['near_zero_var'] = near_zero_indices

    if near_zero_indices:
        result['is_collinear'] = True
        result['recommendation'] = (
            f"Found {len(near_zero_indices)} near-zero variance columns. "
            "Remove these predictors or apply regularization."
        )

    # Calculate condition number
    try:
        # Use X^T X for condition number calculation
        XtX = X.T @ X
        # Add small regularization for numerical stability
        XtX_reg = XtX + tol * np.eye(n_features)
        eigvals = np.linalg.eigvalsh(XtX_reg)
        condition_number = np.max(eigvals) / np.min(eigvals)
        result['condition_number'] = float(condition_number)

        if condition_number > condition_number_threshold:
            result['is_collinear'] = True
            result['recommendation'] = (
                f"High condition number ({condition_number:.2f}) indicates "
                "multicollinearity. Consider PCA, regularization, or removing correlated features."
            )
    except np.linalg.LinAlgError:
        result['is_collinear'] = True
        result['condition_number'] = float('inf')
        result['recommendation'] = (
            "Matrix is singular. Cannot compute condition number. "
            "Remove linearly dependent features."
        )

    # Check for high correlations between pairs
    if n_features > 1:
        try:
            corr_matrix = np.corrcoef(X, rowvar=False)
            # Handle NaN correlations (from constant columns)
            corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

            for i in range(n_features):
                for j in range(i + 1, n_features):
                    if abs(corr_matrix[i, j]) > 0.99:
                        result['high_corr_pairs'].append((i, j))

            if result['high_corr_pairs']:
                result['is_collinear'] = True
                if result['recommendation'] == 'No issues detected':
                    result['recommendation'] = (
                        f"Found {len(result['high_corr_pairs'])} highly correlated "
                        "feature pairs (r > 0.99). Consider removing one from each pair."
                    )
        except Exception as e:
            logger.warning(f"Could not compute correlation matrix: {e}")

    return result


def enforce_minimum_sample_size(
    n_samples: int,
    min_samples: int = 30,
    bootstrap_resamples: int = 1000,
    statistic_type: str = "mean"
) -> Tuple[bool, str]:
    """
    Enforce minimum sample size requirements for valid statistical inference.

    Different statistics and methods have different minimum sample size requirements:
    - Mean/Proportion: Central Limit Theorem typically requires n >= 30
    - Regression: Need n > p (features), ideally n >= 10 * p
    - Bootstrap: Need sufficient samples to generate stable resamples

    Args:
        n_samples: Current number of samples
        min_samples: Minimum required samples (default: 30)
        bootstrap_resamples: Number of bootstrap resamples requested
        statistic_type: Type of statistic ('mean', 'regression', 'variance')

    Returns:
        Tuple of (is_valid, message):
            - is_valid: True if sample size is sufficient
            - message: Explanation of the check result
    """
    if n_samples < min_samples:
        msg = (
            f"Insufficient samples: {n_samples} < {min_samples} (minimum). "
            f"Cannot perform reliable {statistic_type} estimation with "
            f"{bootstrap_resamples} bootstrap resamples. "
            "Consider increasing population size or reducing bootstrap resamples."
        )
        return False, msg

    # Additional checks for bootstrap
    if n_samples < bootstrap_resamples:
        # This is not strictly an error, but worth noting
        msg = (
            f"Sample size ({n_samples}) is less than bootstrap resamples "
            f"({bootstrap_resamples}). Bootstrap may have many duplicate samples. "
            "Consider reducing bootstrap resamples or increasing sample size."
        )
        warnings.warn(msg, UserWarning)
        logger.warning(msg)

    # Regression-specific check
    if statistic_type == "regression":
        # We can't know the number of features here, but we can enforce a hard minimum
        regression_min = 50  # Heuristic minimum for regression
        if n_samples < regression_min:
            msg = (
                f"Sample size ({n_samples}) may be too small for regression analysis. "
                f"Minimum recommended: {regression_min}."
            )
            warnings.warn(msg, UserWarning)
            logger.warning(msg)

    return True, f"Sample size {n_samples} meets minimum requirement of {min_samples}."


def validate_covariance_matrix(
    cov_matrix: np.ndarray,
    tol: float = 1e-10
) -> Tuple[bool, str]:
    """
    Validate that a covariance matrix is positive semi-definite and well-conditioned.

    A valid covariance matrix must be:
    1. Symmetric
    2. Positive semi-definite (all eigenvalues >= 0)
    3. Well-conditioned (not near-singular)

    Args:
        cov_matrix: Covariance matrix to validate
        tol: Tolerance for numerical checks

    Returns:
        Tuple of (is_valid, message)
    """
    if cov_matrix.shape[0] != cov_matrix.shape[1]:
        return False, "Covariance matrix must be square"

    # Check symmetry
    if not np.allclose(cov_matrix, cov_matrix.T, atol=tol):
        return False, "Covariance matrix is not symmetric"

    # Check positive semi-definiteness
    try:
        eigvals = np.linalg.eigvalsh(cov_matrix)
        if np.any(eigvals < -tol):
            return False, f"Covariance matrix has negative eigenvalues (min: {np.min(eigvals)})"
    except np.linalg.LinAlgError as e:
        return False, f"Could not compute eigenvalues: {e}"

    # Check condition number
    try:
        eigvals = np.linalg.eigvalsh(cov_matrix)
        pos_eigvals = eigvals[eigvals > tol]
        if len(pos_eigvals) == 0:
            return False, "Covariance matrix is singular (all eigenvalues near zero)"

        condition_number = np.max(pos_eigvals) / np.min(pos_eigvals)
        if condition_number > 1e10:
            return False, f"Covariance matrix is ill-conditioned (cond: {condition_number})"
    except Exception as e:
        return False, f"Condition number check failed: {e}"

    return True, "Covariance matrix is valid"


def handle_zero_variance(
    data: np.ndarray,
    axis: int = 0,
    replace_value: float = 0.0,
    warn: bool = True
) -> Tuple[np.ndarray, List[int]]:
    """
    Handle zero-variance columns in data by replacing them with a constant value.

    Zero-variance columns can cause division by zero in CI calculations and
    lead to infinite or NaN confidence intervals.

    Args:
        data: Input data array
        axis: Axis along which to compute variance (0 for columns, 1 for rows)
        replace_value: Value to replace zero-variance entries with
        warn: Whether to issue a warning

    Returns:
        Tuple of (cleaned_data, zero_var_indices):
            - cleaned_data: Data with zero-variance columns replaced
            - zero_var_indices: Indices of columns/rows that had zero variance
    """
    data = np.asarray(data, dtype=np.float64)
    zero_var_indices = []

    if axis == 0:
        variances = np.var(data, axis=0)
        zero_mask = variances < 1e-15
        zero_var_indices = np.where(zero_mask)[0].tolist()

        if zero_var_indices and warn:
            msg = f"Found {len(zero_var_indices)} zero-variance columns at indices {zero_var_indices}"
            warnings.warn(msg, UserWarning)
            logger.warning(msg)

        # Replace zero-variance columns with replace_value
        if zero_var_indices:
            data[:, zero_var_indices] = replace_value

    elif axis == 1:
        variances = np.var(data, axis=1)
        zero_mask = variances < 1e-15
        zero_var_indices = np.where(zero_mask)[0].tolist()

        if zero_var_indices and warn:
            msg = f"Found {len(zero_var_indices)} zero-variance rows at indices {zero_var_indices}"
            warnings.warn(msg, UserWarning)
            logger.warning(msg)

        if zero_var_indices:
            data[zero_var_indices, :] = replace_value
    else:
        raise ValueError(f"Axis must be 0 or 1, got {axis}")

    return data, zero_var_indices


def get_edge_case_status(
    epsilon: float,
    n_samples: int,
    X: Optional[np.ndarray] = None,
    noise_type: str = "laplace",
    bootstrap_resamples: int = 1000
) -> Dict[str, Any]:
    """
    Comprehensive edge case status check for a simulation condition.

    This is a convenience function that runs all edge case checks and returns
    a unified status report.

    Args:
        epsilon: Privacy budget
        n_samples: Sample size
        X: Optional predictor matrix for regression checks
        noise_type: Type of DP noise
        bootstrap_resamples: Number of bootstrap resamples

    Returns:
        Dictionary with status for all edge case checks
    """
    status = {
        'epsilon_clamped': False,
        'clamped_epsilon': epsilon,
        'sample_size_valid': True,
        'sample_size_message': '',
        'collinearity_detected': False,
        'collinearity_details': {},
        'zero_variance_detected': False,
        'warnings': []
    }

    # Check epsilon
    clamped_eps, was_clamped = clamp_noise_scale(epsilon, sensitivity=1.0, noise_type=noise_type)
    status['epsilon_clamped'] = was_clamped
    status['clamped_epsilon'] = clamped_eps
    if was_clamped:
        status['warnings'].append(f"Epsilon clamped from {epsilon} to {clamped_eps}")

    # Check sample size
    is_valid, msg = enforce_minimum_sample_size(
        n_samples,
        min_samples=30,
        bootstrap_resamples=bootstrap_resamples
    )
    status['sample_size_valid'] = is_valid
    status['sample_size_message'] = msg
    if not is_valid:
        status['warnings'].append(msg)

    # Check collinearity if X provided
    if X is not None:
        collinearity_info = detect_collinearity(X)
        status['collinearity_details'] = collinearity_info
        status['collinearity_detected'] = collinearity_info['is_collinear']
        if collinearity_info['is_collinear']:
            status['warnings'].append(f"Collinearity detected: {collinearity_info['recommendation']}")

    return status