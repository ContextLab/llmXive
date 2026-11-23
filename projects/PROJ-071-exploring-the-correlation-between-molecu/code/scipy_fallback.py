"""
Scipy Fallback Module for Residual Diagnostics.

This module provides robust implementations of statistical tests used in
residual diagnostics (Shapiro-Wilk and Breusch-Pagan) using scipy and numpy.
It serves as a fallback or primary implementation to ensure statistical
rigor even if statsmodels is unavailable or behaves unexpectedly.

These functions are integrated into the analysis pipeline (T025) to ensure
statistical validity without external dependencies beyond scipy/numpy.
"""
import numpy as np
import scipy.stats as stats
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def shapiro_wilk_test(residuals: np.ndarray) -> Tuple[float, float, bool]:
    """
    Perform the Shapiro-Wilk test for normality on residuals.

    Args:
        residuals: Array of residuals from a regression model.

    Returns:
        Tuple of (statistic, p_value, is_normal) where is_normal is True
        if p_value > 0.05 (fail to reject null hypothesis of normality).

    Raises:
        ValueError: If residuals are empty or have fewer than 3 samples.
    """
    if len(residuals) < 3:
        raise ValueError("Shapiro-Wilk test requires at least 3 samples.")
    
    if np.all(residuals == residuals[0]):
        # If all residuals are identical, variance is zero, not normal distribution in typical sense
        logger.warning("All residuals are identical. Shapiro-Wilk test may be invalid.")
        return 0.0, 1.0, True

    try:
        stat, p_value = stats.shapiro(residuals)
        is_normal = p_value > 0.05
        logger.debug(f"Shapiro-Wilk: stat={stat:.4f}, p={p_value:.4f}, normal={is_normal}")
        return stat, p_value, is_normal
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        raise

def breusch_pagan_test(residuals: np.ndarray, fitted_values: np.ndarray) -> Tuple[float, float, bool]:
    """
    Perform the Breusch-Pagan test for homoscedasticity.
    
    The test checks if the variance of the residuals is constant (homoscedastic)
    or if it depends on the fitted values (heteroscedastic).
    
    Implementation uses the auxiliary regression approach:
    1. Square the residuals.
    2. Regress squared residuals against fitted values.
    3. Calculate LM = N * R^2 from this auxiliary regression.
    4. Compare LM to Chi-squared distribution with k degrees of freedom.

    Args:
        residuals: Array of residuals from the primary regression.
        fitted_values: Array of fitted values from the primary regression.

    Returns:
        Tuple of (lm_statistic, p_value, is_homoscedastic) where is_homoscedastic 
        is True if p_value > 0.05 (fail to reject null hypothesis of homoscedasticity).

    Raises:
        ValueError: If inputs are empty or have fewer than 4 samples.
    """
    if len(residuals) < 4:
        raise ValueError("Breusch-Pagan test requires at least 4 samples.")
    
    if len(residuals) != len(fitted_values):
        raise ValueError("Residuals and fitted values must have the same length.")

    n = len(residuals)
    
    # Step 1: Square the residuals
    sq_residuals = residuals ** 2
    
    # Step 2: Simple linear regression of sq_residuals on fitted_values
    # y = a + b * x
    # We use numpy's polyfit for simplicity (degree 1)
    try:
        # Centering to avoid numerical issues if fitted_values are constant
        if np.var(fitted_values) < 1e-9:
            logger.warning("Fitted values have near-zero variance. Breusch-Pagan test may be invalid.")
            # If fitted values are constant, we can't test for heteroscedasticity dependent on them.
            # Assume homoscedasticity by default in this degenerate case.
            return 0.0, 1.0, True

        slope, intercept = np.polyfit(fitted_values, sq_residuals, 1)
        predictions = slope * fitted_values + intercept
        
        # Calculate R-squared of the auxiliary regression
        ss_res = np.sum((sq_residuals - predictions) ** 2)
        ss_tot = np.sum((sq_residuals - np.mean(sq_residuals)) ** 2)
        
        if ss_tot == 0:
            r_squared = 0.0
        else:
            r_squared = 1.0 - (ss_res / ss_tot)
        
    except Exception as e:
        logger.error(f"Auxiliary regression for Breusch-Pagan failed: {e}")
        raise

    # Step 3: Calculate LM statistic
    lm_stat = n * r_squared
    
    # Step 4: P-value from Chi-squared distribution (1 degree of freedom for simple regression)
    # Degrees of freedom = number of independent variables in auxiliary regression = 1
    p_value = 1.0 - stats.chi2.cdf(lm_stat, df=1)
    
    is_homoscedastic = p_value > 0.05
    logger.debug(f"Breusch-Pagan: LM={lm_stat:.4f}, p={p_value:.4f}, homoscedastic={is_homoscedastic}")
    
    return lm_stat, p_value, is_homoscedastic

def run_residual_diagnostics_scipy(residuals: np.ndarray, fitted_values: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    Run a suite of residual diagnostics using scipy.

    Args:
        residuals: Array of residuals.
        fitted_values: Array of fitted values (required for Breusch-Pagan).

    Returns:
        Dictionary containing test results:
        - shapiro_wilk: {statistic, p_value, passed}
        - breusch_pagan: {statistic, p_value, passed} (if fitted_values provided)
        - summary: "PASS" or "FAIL" based on thresholds

    Raises:
        ValueError: If inputs are invalid or tests fail.
    """
    results = {}
    
    # Shapiro-Wilk
    try:
        sw_stat, sw_p, sw_passed = shapiro_wilk_test(residuals)
        results["shapiro_wilk"] = {
            "statistic": float(sw_stat),
            "p_value": float(sw_p),
            "passed": bool(sw_passed)
        }
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        results["shapiro_wilk"] = {
            "error": str(e),
            "passed": False
        }

    # Breusch-Pagan
    if fitted_values is not None:
        try:
            bp_stat, bp_p, bp_passed = breusch_pagan_test(residuals, fitted_values)
            results["breusch_pagan"] = {
                "statistic": float(bp_stat),
                "p_value": float(bp_p),
                "passed": bool(bp_passed)
            }
        except Exception as e:
            logger.error(f"Breusch-Pagan test failed: {e}")
            results["breusch_pagan"] = {
                "error": str(e),
                "passed": False
            }
    else:
        logger.warning("Fitted values not provided; skipping Breusch-Pagan test.")
        results["breusch_pagan"] = {
            "skipped": True,
            "passed": False
        }

    # Summary
    # Pass if both tests pass (or are skipped with no error)
    sw_ok = results.get("shapiro_wilk", {}).get("passed", False)
    bp_ok = results.get("breusch_pagan", {}).get("passed", False)
    
    # If BP was skipped, we only check SW
    if "skipped" in results.get("breusch_pagan", {}):
        results["summary"] = "PASS" if sw_ok else "FAIL"
    else:
        results["summary"] = "PASS" if (sw_ok and bp_ok) else "FAIL"

    return results