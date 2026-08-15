import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats
from utils import setup_logging

# Configure logger for this module
logger = setup_logging(__name__)

def calculate_analytical_variance(data: np.ndarray, n_bootstrap: int = 1000) -> float:
    """
    Calculate the analytical variance of the mean for the given data.
    
    Args:
        data: 1D numpy array of observations.
        n_bootstrap: Number of bootstrap samples (used for comparison, not calculation).
        
    Returns:
        Analytical variance of the mean (sigma^2 / n).
    """
    if len(data) < 2:
        raise ValueError("Need at least 2 data points to calculate variance.")
    sample_variance = np.var(data, ddof=1)
    n = len(data)
    return sample_variance / n

def bootstrap_validity_check(data: np.ndarray, bootstrap_variances: List[float], 
                             threshold: float = 2.0) -> Tuple[bool, float, float]:
    """
    Compare bootstrap variance to analytical variance and flag unreliable estimates.
    
    Args:
        data: Original data array.
        bootstrap_variances: List of variances calculated from bootstrap samples.
        threshold: Multiplier for the analytical variance to define the acceptable range.
        
    Returns:
        Tuple of (is_valid, mean_bootstrap_variance, analytical_variance).
    """
    if not bootstrap_variances:
        logger.warning("No bootstrap variances provided for validity check.")
        return False, 0.0, 0.0
        
    analytical_var = calculate_analytical_variance(data)
    mean_bootstrap_var = np.mean(bootstrap_variances)
    
    # Check if the mean bootstrap variance is within the threshold of analytical variance
    lower_bound = analytical_var / threshold
    upper_bound = analytical_var * threshold
    
    is_valid = lower_bound <= mean_bootstrap_var <= upper_bound
    
    if not is_valid:
        logger.warning(
            f"Bootstrap validity check failed. Analytical: {analytical_var:.4f}, "
            f"Mean Bootstrap: {mean_bootstrap_var:.4f}. Ratio: {mean_bootstrap_var/analytical_var:.2f}"
        )
    else:
        logger.info(f"Bootstrap validity check passed. Ratio: {mean_bootstrap_var/analytical_var:.2f}")
        
    return is_valid, mean_bootstrap_var, analytical_var

def verify_achieved_magnitude(injected_data: np.ndarray, target_param: float, 
                              param_type: str = "ar1", tolerance: float = 0.05) -> Tuple[bool, float]:
    """
    Verify that the achieved magnitude of an injected parameter matches the target.
    This implements FR-009: Framework to verify and log achieved violation magnitudes.
    
    Args:
        injected_data: The data after perturbation.
        target_param: The intended parameter value (e.g., AR coefficient).
        param_type: Type of parameter ('ar1', 'heavy_tailed', etc.).
        tolerance: Acceptable deviation from target (absolute).
        
    Returns:
        Tuple of (is_match, achieved_value).
    """
    achieved_value = None
    is_match = False
    
    if param_type == "ar1":
        # Estimate AR(1) coefficient using lag-1 autocorrelation
        if len(injected_data) < 2:
            logger.error("Insufficient data to estimate AR(1) coefficient.")
            return False, 0.0
        
        # Calculate lag-1 autocorrelation
        x = injected_data
        x_mean = np.mean(x)
        numerator = np.sum((x[:-1] - x_mean) * (x[1:] - x_mean))
        denominator = np.sum((x[:-1] - x_mean) ** 2)
        
        if denominator == 0:
            logger.warning("Zero denominator in AR(1) estimation.")
            return False, 0.0
            
        achieved_value = numerator / denominator
        
    elif param_type == "heavy_tailed":
        # For heavy-tailed, we might check kurtosis or fit a t-distribution
        # Here we simply check if the data has heavier tails than normal
        # A simple proxy: excess kurtosis > 0
        if len(injected_data) < 4:
            logger.error("Insufficient data to estimate kurtosis.")
            return False, 0.0
        
        achieved_value = stats.kurtosis(injected_data, fisher=True)
        # Target for heavy-tailed is usually > 0 (excess kurtosis)
        # We treat 'target_param' as a minimum threshold for kurtosis
        is_match = achieved_value >= target_param
        
    elif param_type == "heterogeneity":
        # For heterogeneity, we might check variance inflation
        # Target could be a minimum variance ratio
        achieved_value = np.var(injected_data)
        is_match = achieved_value >= target_param
        
    else:
        logger.warning(f"Unknown parameter type: {param_type}. Skipping verification.")
        return True, 0.0
        
    if achieved_value is not None and param_type != "heavy_tailed" and param_type != "heterogeneity":
        # For AR(1) and others, check absolute difference
        if abs(achieved_value - target_param) <= tolerance:
            is_match = True
        else:
            logger.warning(
                f"Achieved {param_type} magnitude ({achieved_value:.4f}) deviates from target ({target_param:.4f}) "
                f"by {abs(achieved_value - target_param):.4f} (tolerance: {tolerance})"
            )
            
    logger.info(f"Verified {param_type}: Target={target_param}, Achieved={achieved_value:.4f}, Match={is_match}")
    return is_match, achieved_value

def should_exclude_dataset(validation_results: Dict[str, Any]) -> bool:
    """
    Determine if a dataset should be excluded from bias calculation based on validation results.
    
    Args:
        validation_results: Dictionary containing validation flags (e.g., 'bootstrap_valid', 'magnitude_verified').
        
    Returns:
        True if the dataset should be excluded, False otherwise.
    """
    # Exclude if bootstrap validity check failed
    if not validation_results.get('bootstrap_valid', True):
        logger.info("Excluding dataset: Bootstrap validity check failed.")
        return True
        
    # Exclude if achieved magnitude verification failed (for perturbation tasks)
    if 'magnitude_verified' in validation_results and not validation_results['magnitude_verified']:
        logger.info("Excluding dataset: Achieved magnitude verification failed.")
        return True
        
    # Exclude if sample size is too small (handled elsewhere, but double check)
    if validation_results.get('sample_size', 0) < 30:
        logger.info("Excluding dataset: Insufficient sample size.")
        return True
        
    return False

def run_full_validation(data: np.ndarray, bootstrap_variances: Optional[List[float]] = None,
                        injected_param: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run the full validation suite for a dataset.
    This combines bootstrap validity check and achieved magnitude verification.
    
    Args:
        data: Original or injected data.
        bootstrap_variances: List of variances from bootstrap samples.
        injected_param: Dictionary with 'target', 'type', and 'tolerance' for magnitude verification.
        
    Returns:
        Dictionary with validation results.
    """
    results = {
        'bootstrap_valid': True,
        'magnitude_verified': True,
        'exclude': False,
        'details': {}
    }
    
    # 1. Bootstrap Validity Check
    if bootstrap_variances is not None:
        is_valid, boot_var, anal_var = bootstrap_validity_check(data, bootstrap_variances)
        results['bootstrap_valid'] = is_valid
        results['details']['bootstrap_variance'] = boot_var
        results['details']['analytical_variance'] = anal_var
    else:
        logger.info("No bootstrap variances provided; skipping bootstrap validity check.")
        
    # 2. Achieved Magnitude Verification
    if injected_param is not None:
        target = injected_param.get('target')
        p_type = injected_param.get('type', 'ar1')
        tol = injected_param.get('tolerance', 0.05)
        
        if target is not None:
            is_match, achieved = verify_achieved_magnitude(data, target, p_type, tol)
            results['magnitude_verified'] = is_match
            results['details']['achieved_magnitude'] = achieved
            results['details']['target_magnitude'] = target
            results['details']['parameter_type'] = p_type
        else:
            logger.warning("Target parameter missing in injected_param; skipping magnitude verification.")
    else:
        logger.info("No injected parameters provided; skipping magnitude verification.")
        
    # 3. Determine Exclusion
    results['exclude'] = should_exclude_dataset(results)
    
    logger.info(f"Full validation complete. Exclude: {results['exclude']}")
    return results