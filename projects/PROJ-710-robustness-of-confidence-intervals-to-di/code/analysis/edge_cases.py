"""
Edge case handling utilities for DP-robustness simulations.

This module encapsulates reusable functions for handling critical edge cases:
1. Clamping noise scale for small epsilon values
2. Detecting collinearity in regression contexts
3. Enforcing minimum sample size for bootstrap resampling
4. Validating covariance matrices
5. Handling zero variance scenarios

All functions are designed to be called by the orchestration loop (main.py)
and return structured status information for logging and decision making.
"""

import numpy as np
from typing import Union, Tuple, Optional, Dict, Any, List
from scipy import stats
import warnings
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Constants for edge case thresholds
DEFAULT_MIN_EPSILON = 0.1
DEFAULT_MIN_SAMPLE_SIZE_BOOTSTRAP = 30
DEFAULT_COLLINEARITY_TOLERANCE = 1e-6
DEFAULT_MIN_VARIANCE = 1e-10


def clamp_noise_scale(
    epsilon: float,
    sensitivity: float,
    noise_type: str = "laplace",
    min_epsilon: float = DEFAULT_MIN_EPSILON,
    max_scale: Optional[float] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Clamp noise scale to prevent numerical instability at very small epsilon.

    For Laplace noise: scale = sensitivity / epsilon
    For Gaussian noise: scale = sensitivity * sqrt(2 * log(1.25/delta)) / epsilon

    When epsilon is too small, the noise scale becomes unreasonably large,
    potentially causing numerical overflow or rendering the data useless.

    Args:
        epsilon: Privacy budget (must be > 0)
        sensitivity: L1 or L2 sensitivity of the query
        noise_type: Type of noise ("laplace" or "gaussian")
        min_epsilon: Minimum epsilon value to clamp to
        max_scale: Optional maximum noise scale (if None, computed from min_epsilon)

    Returns:
        Tuple of (clamped_epsilon, status_dict)
        status_dict contains:
          - original_epsilon: original epsilon value
          - clamped_epsilon: epsilon after clamping
          - was_clamped: boolean indicating if clamping occurred
          - noise_scale: the resulting noise scale
          - reason: explanation if clamping occurred
    """
    if epsilon <= 0:
        raise ValueError(f"Epsilon must be positive, got {epsilon}")

    status = {
        "original_epsilon": epsilon,
        "clamped_epsilon": epsilon,
        "was_clamped": False,
        "noise_scale": None,
        "reason": None
    }

    # Determine effective epsilon
    effective_epsilon = epsilon
    if epsilon < min_epsilon:
        effective_epsilon = min_epsilon
        status["was_clamped"] = True
        status["reason"] = f"Epsilon {epsilon} below minimum {min_epsilon}, clamped to {min_epsilon}"
        logger.warning(status["reason"])

    # Compute noise scale based on type
    if noise_type.lower() == "laplace":
        noise_scale = sensitivity / effective_epsilon
    elif noise_type.lower() == "gaussian":
        # For Gaussian, we need a delta parameter; use a standard value
        delta = 1e-5
        noise_scale = (sensitivity * np.sqrt(2 * np.log(1.25 / delta))) / effective_epsilon
    else:
        raise ValueError(f"Unsupported noise type: {noise_type}")

    # Apply max scale clamp if provided
    if max_scale is not None and noise_scale > max_scale:
        status["was_clamped"] = True
        status["reason"] = f"Noise scale {noise_scale:.4f} exceeds max {max_scale}, clamping epsilon"
        # Recompute epsilon to achieve max_scale
        if noise_type.lower() == "laplace":
            effective_epsilon = sensitivity / max_scale
        else:
            effective_epsilon = (sensitivity * np.sqrt(2 * np.log(1.25 / delta))) / max_scale
        noise_scale = max_scale
        logger.warning(status["reason"])

    status["clamped_epsilon"] = effective_epsilon
    status["noise_scale"] = noise_scale

    return effective_epsilon, status


def detect_collinearity(
    X: np.ndarray,
    y: Optional[np.ndarray] = None,
    tolerance: float = DEFAULT_COLLINEARITY_TOLERANCE
) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect collinearity in design matrix for regression analysis.

    Uses condition number and variance inflation factors (VIF) to detect
    multicollinearity that could destabilize regression coefficient estimates.

    Args:
        X: Design matrix (n_samples, n_features)
        y: Optional response vector (not used for collinearity detection but kept for API consistency)
        tolerance: Threshold for condition number and VIF

    Returns:
        Tuple of (is_collinear, status_dict)
        status_dict contains:
          - condition_number: condition number of X
          - max_vif: maximum variance inflation factor
          - vif_values: list of VIF for each feature
          - is_collinear: boolean indicating if collinearity detected
          - problematic_features: indices of features with high VIF
    """
    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if X.shape[0] < X.shape[1]:
        # More features than samples - guaranteed collinearity
        return True, {
            "condition_number": np.inf,
            "max_vif": np.inf,
            "vif_values": [np.inf] * X.shape[1],
            "is_collinear": True,
            "problematic_features": list(range(X.shape[1])),
            "reason": "More features than samples"
        }

    # Compute condition number
    try:
        # Add small regularization for numerical stability
        X_reg = X + np.eye(X.shape[1]) * 1e-10
        condition_number = np.linalg.cond(X_reg)
    except np.linalg.LinAlgError:
        condition_number = np.inf

    # Compute VIF for each feature
    vif_values = []
    problematic_features = []

    for i in range(X.shape[1]):
        # Regress feature i against all other features
        X_other = np.delete(X, i, axis=1)
        try:
            # Fit linear model: X[:, i] ~ X_other
            beta = np.linalg.lstsq(X_other, X[:, i], rcond=None)[0]
            residuals = X[:, i] - X_other @ beta
            if np.var(residuals) < 1e-10:
                vif = np.inf
            else:
                total_var = np.var(X[:, i])
                vif = total_var / np.var(residuals)
        except np.linalg.LinAlgError:
            vif = np.inf

        vif_values.append(vif)
        if vif > tolerance:
            problematic_features.append(i)

    is_collinear = (condition_number > tolerance) or (len(problematic_features) > 0)

    status = {
        "condition_number": float(condition_number) if not np.isinf(condition_number) else float('inf'),
        "max_vif": float(max(vif_values)) if vif_values else 0.0,
        "vif_values": [float(v) if not np.isinf(v) else float('inf') for v in vif_values],
        "is_collinear": is_collinear,
        "problematic_features": problematic_features,
        "tolerance": tolerance
    }

    if is_collinear:
        logger.warning(
            f"Collinearity detected: condition_number={status['condition_number']:.2e}, "
            f"max_vif={status['max_vif']:.2e}"
        )

    return is_collinear, status


def enforce_minimum_sample_size(
    n_samples: int,
    n_bootstrap: int = 1000,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE_BOOTSTRAP,
    min_bootstrap_ratio: float = 0.3
) -> Tuple[bool, Dict[str, Any]]:
    """
    Enforce minimum sample size requirements for reliable bootstrap resampling.

    Bootstrap resampling requires sufficient sample size to:
    1. Generate meaningful resamples
    2. Achieve stable confidence interval estimates
    3. Avoid excessive ties in small samples

    Args:
        n_samples: Original sample size
        n_bootstrap: Number of bootstrap resamples requested
        min_sample_size: Absolute minimum sample size
        min_bootstrap_ratio: Minimum ratio of bootstrap samples to original sample

    Returns:
        Tuple of (is_valid, status_dict)
        status_dict contains:
          - original_n: original sample size
          - is_valid: whether sample size is sufficient
          - recommended_n_bootstrap: recommended number of bootstrap resamples
          - reason: explanation if validation failed
    """
    status = {
        "original_n": n_samples,
        "requested_n_bootstrap": n_bootstrap,
        "is_valid": True,
        "recommended_n_bootstrap": n_bootstrap,
        "reason": None
    }

    # Check absolute minimum
    if n_samples < min_sample_size:
        status["is_valid"] = False
        status["reason"] = f"Sample size {n_samples} below minimum {min_sample_size}"
        status["recommended_n_bootstrap"] = 0
        logger.error(status["reason"])
        return False, status

    # Check bootstrap ratio
    max_bootstrap = int(n_samples / min_bootstrap_ratio)
    if n_bootstrap > max_bootstrap:
        status["is_valid"] = False
        status["reason"] = f"Bootstrap count {n_bootstrap} exceeds maximum {max_bootstrap} for sample size {n_samples}"
        status["recommended_n_bootstrap"] = max_bootstrap
        logger.warning(status["reason"])
        return False, status

    return True, status


def validate_covariance_matrix(
    cov_matrix: np.ndarray,
    tolerance: float = 1e-10
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that a covariance matrix is positive semi-definite and numerically stable.

    Args:
        cov_matrix: Covariance matrix to validate
        tolerance: Tolerance for eigenvalue checks

    Returns:
        Tuple of (is_valid, status_dict)
    """
    status = {
        "is_valid": True,
        "min_eigenvalue": None,
        "condition_number": None,
        "reason": None
    }

    if cov_matrix.shape[0] != cov_matrix.shape[1]:
        status["is_valid"] = False
        status["reason"] = "Matrix is not square"
        return False, status

    # Check symmetry
    if not np.allclose(cov_matrix, cov_matrix.T, atol=tolerance):
        status["is_valid"] = False
        status["reason"] = "Matrix is not symmetric"
        return False, status

    # Check positive semi-definiteness
    try:
        eigenvalues = np.linalg.eigvalsh(cov_matrix)
        min_eigenvalue = np.min(eigenvalues)
        status["min_eigenvalue"] = float(min_eigenvalue)

        if min_eigenvalue < -tolerance:
            status["is_valid"] = False
            status["reason"] = f"Matrix is not positive semi-definite (min eigenvalue: {min_eigenvalue:.2e})"
            return False, status

        # Check condition number
        pos_eigenvalues = eigenvalues[eigenvalues > tolerance]
        if len(pos_eigenvalues) > 0:
            condition_number = np.max(pos_eigenvalues) / np.min(pos_eigenvalues)
            status["condition_number"] = float(condition_number)
            if condition_number > 1e10:
                logger.warning(f"Covariance matrix has high condition number: {condition_number:.2e}")
        else:
            status["condition_number"] = float('inf')

    except np.linalg.LinAlgError as e:
        status["is_valid"] = False
        status["reason"] = f"Eigenvalue computation failed: {str(e)}"
        return False, status

    return True, status


def handle_zero_variance(
    data: np.ndarray,
    threshold: float = DEFAULT_MIN_VARIANCE
) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect and handle zero or near-zero variance in data.

    Zero variance causes division by zero in standard error calculations
    and leads to degenerate confidence intervals.

    Args:
        data: Input data array (can be 1D or 2D)
        threshold: Variance threshold below which data is considered constant

    Returns:
        Tuple of (has_zero_var, status_dict)
        status_dict contains:
          - variances: computed variances
          - zero_variance_indices: indices of columns with zero variance
          - is_constant: whether entire array is constant
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    variances = np.var(data, axis=0)
    zero_variance_indices = np.where(variances < threshold)[0].tolist()

    status = {
        "variances": variances.tolist(),
        "zero_variance_indices": zero_variance_indices,
        "is_constant": len(zero_variance_indices) == data.shape[1],
        "threshold": threshold
    }

    if status["is_constant"]:
        logger.warning("All features have zero variance - data is constant")
    elif zero_variance_indices:
        logger.warning(f"Features {zero_variance_indices} have zero variance")

    return len(zero_variance_indices) > 0, status


def get_edge_case_status(
    epsilon: float,
    sensitivity: float,
    noise_type: str,
    X: Optional[np.ndarray] = None,
    data: Optional[np.ndarray] = None,
    n_samples: Optional[int] = None,
    n_bootstrap: int = 1000
) -> Dict[str, Any]:
    """
    Comprehensive edge case check for a simulation condition.

    Runs all edge case checks and aggregates results into a single status report.

    Args:
        epsilon: Privacy budget
        sensitivity: Query sensitivity
        noise_type: Type of noise ("laplace" or "gaussian")
        X: Design matrix for regression (optional)
        data: Data array for variance check (optional)
        n_samples: Sample size (optional)
        n_bootstrap: Number of bootstrap resamples

    Returns:
        Dictionary containing all edge case status information
    """
    result = {
        "epsilon_clamp": None,
        "collinearity": None,
        "sample_size": None,
        "covariance_valid": None,
        "zero_variance": None,
        "overall_valid": True,
        "warnings": []
    }

    # Check epsilon clamping
    _, epsilon_status = clamp_noise_scale(epsilon, sensitivity, noise_type)
    result["epsilon_clamp"] = epsilon_status
    if epsilon_status["was_clamped"]:
        result["warnings"].append(f"Epsilon clamped: {epsilon_status['reason']}")

    # Check collinearity if X provided
    if X is not None:
        is_collinear, collinearity_status = detect_collinearity(X)
        result["collinearity"] = collinearity_status
        if is_collinear:
            result["warnings"].append(f"Collinearity detected: {collinearity_status['max_vif']:.2e} max VIF")

    # Check sample size if provided
    if n_samples is not None:
        is_valid, sample_status = enforce_minimum_sample_size(n_samples, n_bootstrap)
        result["sample_size"] = sample_status
        if not is_valid:
            result["warnings"].append(sample_status["reason"])
            result["overall_valid"] = False

    # Check zero variance if data provided
    if data is not None:
        has_zero_var, variance_status = handle_zero_variance(data)
        result["zero_variance"] = variance_status
        if has_zero_var:
            result["warnings"].append(f"Zero variance detected in {len(variance_status['zero_variance_indices'])} features")

    # Log all warnings
    for warning in result["warnings"]:
        logger.warning(warning)

    return result