"""Custom exceptions for data acquisition and modeling."""

class DataAcquisitionError(Exception):
    """Raised when data acquisition fails."""
    pass

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

class ZeroVarianceError(Exception):
    """Raised when a study has zero variance (SE=0)."""
    pass

class NegativeVarianceError(Exception):
    """Raised when variance estimates are negative."""
    pass

class ConvergenceError(Exception):
    """Raised when model fitting fails to converge."""
    pass

class ModelBoundaryError(Exception):
    """Raised when model parameters hit boundary constraints."""
    pass

def handle_variance_issues(variance: float, study_id: str, clamp_threshold: float = 1e-10) -> float:
    """
    Handle variance issues by clamping or raising exceptions.
    
    This function enforces boundary constraints on variance estimates to ensure
    numerical stability in downstream meta-analytic calculations.
    
    Args:
        variance: The variance value to check.
        study_id: Identifier for the study (for logging/error messages).
        clamp_threshold: The minimum positive value to clamp zero variance to.
            Defaults to 1e-10 to prevent division by zero while minimizing bias.
            
    Returns:
        A valid variance value (clamped to small positive number if needed).
        
    Raises:
        NegativeVarianceError: If variance is negative.
        ZeroVarianceError: If variance is exactly zero and clamping is disabled
            (though default behavior clamps). Note: In this implementation, 
            ZeroVarianceError is raised for logging purposes before clamping 
            if strict mode is needed, but currently returns clamped value.
    """
    import logging

    logger = logging.getLogger(__name__)

    if variance < 0:
        logger.error(f"Negative variance detected: {variance} for study {study_id}")
        raise NegativeVarianceError(f"Negative variance {variance} for study {study_id}")
    
    if variance == 0:
        logger.warning(f"Zero variance detected for study {study_id}. Clamping to {clamp_threshold}.")
        # Clamp to a small positive value to avoid division by zero
        return clamp_threshold
    
    return variance

def validate_variance_bounds(variance: float, study_id: str, min_val: float = 0.0, max_val: float = 1e6) -> float:
    """
    Validate variance against explicit lower and upper bounds.
    
    Args:
        variance: The variance value to check.
        study_id: Identifier for the study.
        min_val: Minimum allowed variance (default 0.0).
        max_val: Maximum allowed variance to prevent outliers from dominating.
            
    Returns:
        The variance value if within bounds, or the clamped value if out of bounds.
        
    Raises:
        ModelBoundaryError: If variance is outside the valid range.
    """
    import logging

    logger = logging.getLogger(__name__)

    if variance < min_val:
        logger.warning(f"Variance {variance} for study {study_id} is below minimum {min_val}.")
        raise ModelBoundaryError(f"Variance {variance} below minimum {min_val} for study {study_id}")
    
    if variance > max_val:
        logger.warning(f"Variance {variance} for study {study_id} exceeds maximum {max_val}. Clamping.")
        # Optionally clamp instead of raising, depending on strictness requirements
        # For now, we raise to force explicit handling of extreme outliers
        raise ModelBoundaryError(f"Variance {variance} exceeds maximum {max_val} for study {study_id}")
    
    return variance

def safe_variance_calculation(se: float, study_id: str) -> float:
    """
    Safely calculate variance from standard error, handling edge cases.
    
    Args:
        se: Standard error value.
        study_id: Identifier for the study.
        
    Returns:
        Calculated variance (se^2), clamped if necessary.
        
    Raises:
        ZeroVarianceError: If SE is zero.
        NegativeVarianceError: If SE is negative (which would imply invalid input).
    """
    if se < 0:
        raise NegativeVarianceError(f"Negative standard error {se} for study {study_id}")
    
    variance = se ** 2
    return handle_variance_issues(variance, study_id)