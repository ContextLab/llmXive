"""
Metrics module for calculating statistical power and other evaluation metrics.

Implements T027, T028: Power calculation logic.
Referenced by T021 (Unit Test).
"""
import numpy as np
from typing import List, Tuple, Optional, Union
import logging

# Import logger from existing utility
# Note: The API surface says `from utils.logger import get_logger`
# We assume the path is relative to code/
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback for direct execution or different path setup
    import logging
    def get_logger(name: str):
        return logging.getLogger(name)

logger = get_logger(__name__)

def calculate_empirical_power(
    true_coefficients: np.ndarray,
    selected_mask: np.ndarray,
    p_values: np.ndarray,
    alpha: float = 0.05
) -> float:
    """
    Calculate empirical power for a single simulation run.
    
    Power is defined as the proportion of true non-zero coefficients that were
    both selected by the variable selection method AND found to be statistically
    significant (p < alpha) in the refitted OLS model.
    
    Formula: Power = (True Positives) / (Total True Non-Zero Coefficients)
    True Positive = (Selected AND Significant AND True Non-Zero)
    
    Args:
        true_coefficients: Array of true coefficients (ground truth) from the data generation process.
        selected_mask: Boolean array indicating which variables were selected by the method.
        p_values: Array of p-values corresponding to the coefficients in the refitted model.
                  Must align with the dimensions of true_coefficients and selected_mask.
        alpha: Significance threshold (default 0.05).
    
    Returns:
        Empirical power as a float between 0.0 and 1.0.
        Returns 0.0 if there are no true non-zero coefficients (undefined power).
    """
    # Ensure inputs are numpy arrays
    true_coefficients = np.asarray(true_coefficients, dtype=float)
    selected_mask = np.asarray(selected_mask, dtype=bool)
    p_values = np.asarray(p_values, dtype=float)
    
    # Validate shapes
    if not (true_coefficients.shape == selected_mask.shape == p_values.shape):
        raise ValueError(
            f"Input arrays must have the same shape. "
            f"Got true_coefficients: {true_coefficients.shape}, "
            f"selected_mask: {selected_mask.shape}, "
            f"p_values: {p_values.shape}"
        )
    
    # Identify true non-zero coefficients (ground truth signal)
    # Using a small epsilon for float comparison safety
    epsilon = 1e-8
    true_non_zero_mask = np.abs(true_coefficients) > epsilon
    
    num_true_non_zero = np.sum(true_non_zero_mask)
    
    # If no true signal exists, power is undefined. Return 0.0.
    if num_true_non_zero == 0:
        logger.debug("No true non-zero coefficients found. Returning power = 0.0.")
        return 0.0
    
    # Identify significant coefficients (p < alpha)
    significant_mask = p_values < alpha
    
    # True Positives: Selected AND Significant AND True Non-Zero
    true_positives_mask = selected_mask & significant_mask & true_non_zero_mask
    num_true_positives = np.sum(true_positives_mask)
    
    # Calculate Power
    power = num_true_positives / num_true_non_zero
    
    logger.debug(
        f"Power calculation: TP={num_true_positives}, "
        f"TotalSignal={num_true_non_zero}, Power={power:.4f}"
    )
    
    return float(power)

def calculate_false_discovery_rate(
    selected_mask: np.ndarray,
    true_coefficients: np.ndarray
) -> float:
    """
    Calculate False Discovery Rate (FDR).
    FDR = (False Positives) / (Total Selected)
    False Positive = Selected AND True Zero
    
    Args:
        selected_mask: Boolean array of selected variables.
        true_coefficients: Array of true coefficients.
        
    Returns:
        FDR as a float. Returns 0.0 if no variables selected.
    """
    selected_mask = np.asarray(selected_mask, dtype=bool)
    true_coefficients = np.asarray(true_coefficients, dtype=float)
    
    if not np.any(selected_mask):
        return 0.0
    
    true_zero_mask = np.abs(true_coefficients) <= 1e-8
    false_positives = np.sum(selected_mask & true_zero_mask)
    total_selected = np.sum(selected_mask)
    
    return float(false_positives / total_selected)

def calculate_condition_number(X: np.ndarray) -> float:
    """
    Calculate the condition number of the design matrix X.
    Used for collinearity diagnostics (FR-007).
    
    Args:
        X: Design matrix (n_samples, n_features).
        
    Returns:
        Condition number (float).
    """
    try:
        # Use SVD for stability
        _, s, _ = np.linalg.svd(X, full_matrices=False)
        if s[-1] == 0:
            return float('inf')
        return float(s[0] / s[-1])
    except np.linalg.LinAlgError:
        logger.error("Error calculating condition number (singular matrix).")
        return float('inf')

def calculate_vif(X: np.ndarray) -> np.ndarray:
    """
    Calculate Variance Inflation Factors (VIF) for each predictor.
    Used for collinearity diagnostics (FR-007).
    
    Args:
        X: Design matrix (n_samples, n_features).
        
    Returns:
        Array of VIF values.
    """
    n_features = X.shape[1]
    vif_values = np.zeros(n_features)
    
    # Add intercept if not present? Assuming X is centered or includes intercept
    # Standard VIF calculation: Regress X_j on all other X_k
    
    for i in range(n_features):
        y = X[:, i]
        X_others = np.delete(X, i, axis=1)
        
        # Simple OLS: (X_others^T X_others)^-1 X_others^T y
        # Check for singularity
        try:
            # Add a small regularization if needed, but standard OLS first
            coeffs = np.linalg.lstsq(X_others, y, rcond=None)[0]
            y_pred = X_others @ coeffs
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            
            if ss_tot == 0:
                vif_values[i] = 0.0
            else:
                r_squared = 1 - (ss_res / ss_tot)
                vif_values[i] = 1.0 / (1 - r_squared) if (1 - r_squared) > 1e-10 else float('inf')
        except np.linalg.LinAlgError:
            vif_values[i] = float('inf')
    
    return vif_values

# Placeholder for main execution if needed
def main():
    logger.info("Metrics module loaded. No direct execution defined.")

if __name__ == "__main__":
    main()
