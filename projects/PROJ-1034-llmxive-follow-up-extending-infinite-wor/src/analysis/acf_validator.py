"""
ACF Validator: Checks lag-1 autocorrelation for stability.
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

def validate_lag1_autocorrelation(values: np.ndarray, threshold: float = 0.1) -> bool:
    """
    Compute lag-1 autocorrelation and check if it is below threshold.
    """
    if len(values) < 2:
        return True
    
    # Simple lag-1 autocorrelation calculation
    mean = np.mean(values)
    var = np.var(values)
    if var == 0:
        return True
    
    cov = np.mean((values[:-1] - mean) * (values[1:] - mean))
    acf_lag1 = cov / var
    
    logger.info(f"Lag-1 ACF: {acf_lag1:.4f}, Threshold: {threshold}")
    return abs(acf_lag1) < threshold
