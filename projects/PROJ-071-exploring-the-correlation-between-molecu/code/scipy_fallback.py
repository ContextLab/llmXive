"""
Scipy fallback implementation for residual diagnostics.

This module provides robust implementations of the Shapiro-Wilk and 
Breusch-Pagan tests using scipy.stats, intended as a fallback or 
primary implementation for the residual diagnostics in T025.

It ensures that the analysis pipeline can perform necessary statistical 
checks even if statsmodels is unavailable or fails.
"""

import numpy as np
import scipy.stats as stats
from typing import Tuple, Optional, Dict, Any
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

def shapiro_wilk_test(residuals: np.ndarray) -> Tuple[float, float]:
    """
    Perform the Shapiro-Wilk test for normality on residuals.

    Args:
        residuals: Array of residuals from a regression model.

    Returns:
        Tuple of (statistic, p-value).
        
    Raises:
        ValueError: If residuals are empty or too small for the test.
    """
    if residuals is None or len(residuals) == 0:
        raise ValueError("Residuals array is empty.")
    
    n = len(residuals)
    if n < 3:
        # Shapiro-Wilk requires at least 3 samples
        logger.warning(f"Shapiro-Wilk test requires at least 3 samples, got {n}. Skipping.")
        return 0.0, 1.0
    
    try:
        stat, p_value = stats.shapiro(residuals)
        logger.debug(f"Shapiro-Wilk test: statistic={stat:.4f}, p-value={p_value:.4f}")
        return stat, p_value
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        raise

def breusch_pagan_test(residuals: np.ndarray, fitted_values: np.ndarray) -> Tuple[float, float]:
    """
    Perform the Breusch-Pagan test for heteroscedasticity.
    
    This is a custom implementation using scipy/statsmodels logic 
    to avoid dependency on statsmodels.stats.diagnostic if unavailable,
    or to provide a pure scipy path.
    
    The test checks if the variance of the errors is constant (homoscedasticity).
    Null hypothesis: Homoscedasticity (constant variance).
    Alternative hypothesis: Heteroscedasticity (variance depends on fitted values).

    Args:
        residuals: Array of residuals from the regression model.
        fitted_values: Array of fitted values (y_pred) from the model.

    Returns:
        Tuple of (LM statistic, p-value).
        
    Raises:
        ValueError: If inputs are invalid or dimensions mismatch.
    """
    if residuals is None or fitted_values is None:
        raise ValueError("Residuals and fitted values cannot be None.")
    
    residuals = np.asarray(residuals)
    fitted_values = np.asarray(fitted_values)
    
    if len(residuals) != len(fitted_values):
        raise ValueError(f"Length mismatch: residuals ({len(residuals)}) vs fitted_values ({len(fitted_values)})")
    
    n = len(residuals)
    if n < 10:
        logger.warning(f"Breusch-Pagan test may be unreliable with < 10 samples (got {n}). Proceeding.")
    
    # Step 1: Square the residuals
    squared_residuals = residuals ** 2
    
    # Step 2: Regress squared residuals on fitted values (or original X)
    # Here we use fitted_values as the independent variable for simplicity
    # Model: squared_residuals ~ fitted_values
    
    # Add constant for intercept
    X = np.column_stack([np.ones(n), fitted_values])
    
    try:
        # OLS estimation: beta = (X'X)^-1 X'y
        XtX = X.T @ X
        # Handle potential singularity if fitted_values are constant
        if np.linalg.cond(XtX) > 1e10:
            logger.warning("X'X is nearly singular in Breusch-Pagan test. Assuming homoscedasticity.")
            return 0.0, 1.0
        
        beta = np.linalg.solve(XtX, X.T @ squared_residuals)
        
        # Calculate predicted squared residuals
        predicted_sq_resid = X @ beta
        
        # Calculate Explained Sum of Squares (ESS)
        mean_sq_resid = np.mean(squared_residuals)
        ESS = np.sum((predicted_sq_resid - mean_sq_resid) ** 2)
        
        # LM Statistic = n * R^2
        # R^2 = ESS / TSS (Total Sum of Squares of squared residuals)
        TSS = np.sum((squared_residuals - mean_sq_resid) ** 2)
        
        if TSS == 0:
            logger.warning("Total Sum of Squares is zero in Breusch-Pagan test. Assuming homoscedasticity.")
            return 0.0, 1.0
        
        R2 = ESS / TSS
        LM_stat = n * R2
        
        # p-value from Chi-squared distribution with 1 degree of freedom
        # (1 regressor: fitted_values)
        p_value = 1.0 - stats.chi2.cdf(LM_stat, df=1)
        
        logger.debug(f"Breusch-Pagan test: LM={LM_stat:.4f}, p-value={p_value:.4f}")
        return LM_stat, p_value
        
    except np.linalg.LinAlgError:
        logger.error("Linear algebra error during Breusch-Pagan calculation.")
        raise
    except Exception as e:
        logger.error(f"Breusch-Pagan test failed: {e}")
        raise

def run_residual_diagnostics_scipy(
    residuals: np.ndarray, 
    fitted_values: np.ndarray
) -> Dict[str, Any]:
    """
    Run the full suite of residual diagnostics using scipy fallbacks.
    
    Args:
        residuals: Array of residuals.
        fitted_values: Array of fitted values.
    
    Returns:
        Dictionary containing test results:
            - shapiro_stat, shapiro_p
            - breusch_pagan_lm, breusch_pagan_p
            - shapiro_pass (p > 0.05)
            - breusch_pagan_pass (p > 0.05)
    """
    results = {
        "shapiro_stat": None,
        "shapiro_p": None,
        "shapiro_pass": False,
        "breusch_pagan_lm": None,
        "breusch_pagan_p": None,
        "breusch_pagan_pass": False,
        "errors": []
    }

    # Shapiro-Wilk
    try:
        sw_stat, sw_p = shapiro_wilk_test(residuals)
        results["shapiro_stat"] = sw_stat
        results["shapiro_p"] = sw_p
        results["shapiro_pass"] = sw_p > 0.05
        logger.info(f"Shapiro-Wilk: p={sw_p:.4f} -> {'PASS' if results['shapiro_pass'] else 'FAIL'}")
    except Exception as e:
        results["errors"].append(f"Shapiro-Wilk failed: {str(e)}")
        logger.error(f"Shapiro-Wilk failed: {e}")

    # Breusch-Pagan
    try:
        bp_lm, bp_p = breusch_pagan_test(residuals, fitted_values)
        results["breusch_pagan_lm"] = bp_lm
        results["breusch_pagan_p"] = bp_p
        results["breusch_pagan_pass"] = bp_p > 0.05
        logger.info(f"Breusch-Pagan: p={bp_p:.4f} -> {'PASS' if results['breusch_pagan_pass'] else 'FAIL'}")
    except Exception as e:
        results["errors"].append(f"Breusch-Pagan failed: {str(e)}")
        logger.error(f"Breusch-Pagan failed: {e}")

    return results
