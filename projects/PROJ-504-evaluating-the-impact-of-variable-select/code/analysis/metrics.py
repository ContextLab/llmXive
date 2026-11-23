from __future__ import annotations

import logging
from typing import List, Tuple, Optional, Union, Dict, Any

import numpy as np
import pandas as pd
import statsmodels.api as sm

# Ensure logger is set up (assumes setup_logging called elsewhere or in utils)
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


def calculate_condition_number(X: np.ndarray) -> float:
    """
    Calculate the condition number of the design matrix X.
    
    The condition number measures the sensitivity of the solution of a linear
    system to errors in the data. A high condition number indicates potential
    multicollinearity.
    
    Args:
        X: Design matrix (n_samples, n_features). Should NOT include intercept
           unless explicitly intended for that calculation.
    
    Returns:
        Condition number (float). Returns np.inf if matrix is singular or
        calculation fails.
    """
    if X.shape[0] < X.shape[1]:
        logger.warning("Design matrix has more features than samples; condition number may be infinite.")
        return float('inf')
    
    try:
        # Center the matrix to remove intercept effects if not already centered
        # though condition number is usually calculated on the raw design matrix
        # for collinearity diagnostics.
        singular_values = np.linalg.svd(X, compute_uv=False)
        if singular_values[-1] == 0:
            return float('inf')
        return float(singular_values[0] / singular_values[-1])
    except np.linalg.LinAlgError:
        logger.error("SVD calculation failed for condition number.")
        return float('inf')


def calculate_vif(X: np.ndarray, feature_names: Optional[List[str]] = None) -> Union[pd.Series, Dict[str, float]]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature in the design matrix.
    
    VIF quantifies the severity of multicollinearity in an ordinary least squares
    regression analysis. A VIF > 10 (or sometimes > 5) indicates high multicollinearity.
    
    Args:
        X: Design matrix (n_samples, n_features). Should NOT include the intercept column.
        feature_names: Optional list of feature names. If None, returns a dict with
                       indices as keys.
    
    Returns:
        If feature_names provided, returns a pandas Series with feature names as index.
        Otherwise, returns a dict mapping feature indices to VIF values.
    """
    n_features = X.shape[1]
    
    if feature_names is None:
        feature_names = [f"Feature_{i}" for i in range(n_features)]
    
    if len(feature_names) != n_features:
        raise ValueError("feature_names length must match number of columns in X")
    
    vif_values = {}
    
    for i in range(n_features):
        # Create a design matrix for the i-th feature against all other features
        y_i = X[:, i]
        X_others = np.delete(X, i, axis=1)
        
        # Add intercept for the auxiliary regression
        X_others_with_intercept = sm.add_constant(X_others)
        
        try:
            # Fit OLS model: Feature_i ~ All Other Features
            model = sm.OLS(y_i, X_others_with_intercept).fit()
            r_squared = model.rsquared
            
            # Calculate VIF: 1 / (1 - R^2)
            if r_squared == 1.0:
                vif = float('inf')
            else:
                vif = 1.0 / (1.0 - r_squared)
            
            vif_values[feature_names[i]] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for feature {feature_names[i]}: {e}")
            vif_values[feature_names[i]] = float('inf')
    
    # Return as Series if names provided, else dict
    if feature_names:
        return pd.Series(vif_values)
    return vif_values


def calculate_empirical_power(
    true_coefficients: np.ndarray,
    selected_mask: np.ndarray,
    p_values: np.ndarray,
    alpha: float = 0.05
) -> float:
    """
    Calculate empirical power as the proportion of true non-zero coefficients
    that are selected AND significant.
    
    Args:
        true_coefficients: Array of true coefficients.
        selected_mask: Boolean array indicating which variables were selected.
        p_values: Array of p-values for the selected variables (aligned with true_coefficients).
        alpha: Significance threshold.
    
    Returns:
        Empirical power (float between 0 and 1).
    """
    # Identify true non-zero coefficients
    true_nonzero_mask = true_coefficients != 0
    
    if not np.any(true_nonzero_mask):
        logger.warning("No true non-zero coefficients found; power is undefined (returning 0.0).")
        return 0.0
    
    # Find true positives: selected AND significant AND truly non-zero
    significant_mask = p_values < alpha
    true_positives = selected_mask & significant_mask & true_nonzero_mask
    
    num_true_nonzero = np.sum(true_nonzero_mask)
    num_true_positives = np.sum(true_positives)
    
    if num_true_nonzero == 0:
        return 0.0
    
    return float(num_true_positives / num_true_nonzero)


def calculate_false_discovery_rate(
    selected_mask: np.ndarray,
    true_coefficients: np.ndarray,
    p_values: np.ndarray,
    alpha: float = 0.05
) -> float:
    """
    Calculate False Discovery Rate (FDR) among selected variables.
    
    FDR = (False Positives) / (Total Selected & Significant)
    
    Args:
        selected_mask: Boolean array indicating selected variables.
        true_coefficients: Array of true coefficients.
        p_values: Array of p-values.
        alpha: Significance threshold.
    
    Returns:
        FDR (float between 0 and 1).
    """
    significant_mask = p_values < alpha
    selected_and_significant = selected_mask & significant_mask
    
    if not np.any(selected_and_significant):
        return 0.0
    
    # False positives: selected AND significant BUT truly zero
    false_positives = selected_and_significant & (true_coefficients == 0)
    
    num_selected_significant = np.sum(selected_and_significant)
    num_false_positives = np.sum(false_positives)
    
    return float(num_false_positives / num_selected_significant)


def main():
    """
    Main entry point for metrics calculations.
    
    This function is intended to be called by the pipeline to compute
    collinearity diagnostics (VIF, Condition Number) and power metrics
    for the simulation results.
    
    It expects to be integrated into the broader pipeline flow where
    simulation data is available.
    """
    logger.info("Metrics module loaded. Ready to calculate VIF, Condition Number, and Power.")
    # This function serves as an entry point for integration testing or
    # direct execution if specific diagnostic runs are needed.
    pass


if __name__ == "__main__":
    main()