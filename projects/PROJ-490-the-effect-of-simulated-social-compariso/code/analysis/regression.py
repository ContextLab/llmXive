import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
from code.utils.logger import get_logger

logger = get_logger(__name__)

def check_normality(residuals: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test for normality of residuals.
    
    Args:
        residuals: Array of regression residuals.
        alpha: Significance level for the test.
        
    Returns:
        Dictionary containing test statistic, p-value, and boolean pass/fail.
    """
    if len(residuals) < 3:
        logger.warning("Not enough residuals for normality test.")
        return {"statistic": np.nan, "p_value": np.nan, "passed": True, "message": "Insufficient data"}
        
    stat, p_value = stats.shapiro(residuals)
    passed = p_value > alpha
    status = "PASSED" if passed else "FAILED"
    logger.info(f"Normality (Shapiro-Wilk): statistic={stat:.4f}, p={p_value:.4f} [{status}]")
    
    return {
        "test": "shapiro_wilk",
        "statistic": float(stat),
        "p_value": float(p_value),
        "passed": passed,
        "message": f"Normality assumption {status} (p={p_value:.4f})"
    }

def check_homoscedasticity(residuals: np.ndarray, predicted: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Breusch-Pagan test for homoscedasticity.
    
    Args:
        residuals: Array of regression residuals.
        predicted: Array of predicted values.
        alpha: Significance level.
        
    Returns:
        Dictionary containing test statistic, p-value, and boolean pass/fail.
    """
    # Breusch-Pagan test implementation using statsmodels
    # LM = n * R^2 from auxiliary regression of squared residuals on predictors
    # We use the residuals and predicted values to approximate this
    if len(residuals) < 10:
        logger.warning("Not enough data for homoscedasticity test.")
        return {"statistic": np.nan, "p_value": np.nan, "passed": True, "message": "Insufficient data"}

    try:
        # Auxiliary regression: squared residuals ~ predicted values
        X = sm.add_constant(predicted)
        y_aux = residuals ** 2
        aux_model = sm.OLS(y_aux, X).fit()
        lm_stat = len(residuals) * aux_model.rsquared
        
        # Degrees of freedom = number of predictors in auxiliary model (excluding const)
        df = X.shape[1] - 1
        p_value = 1 - stats.chi2.cdf(lm_stat, df)
        
        passed = p_value > alpha
        status = "PASSED" if passed else "FAILED"
        logger.info(f"Homoscedasticity (Breusch-Pagan): statistic={lm_stat:.4f}, p={p_value:.4f} [{status}]")
        
        return {
            "test": "breusch_pagan",
            "statistic": float(lm_stat),
            "p_value": float(p_value),
            "passed": passed,
            "message": f"Homoscedasticity assumption {status} (p={p_value:.4f})"
        }
    except Exception as e:
        logger.error(f"Homoscedasticity test failed: {e}")
        return {
            "test": "breusch_pagan",
            "statistic": np.nan,
            "p_value": np.nan,
            "passed": False,
            "message": f"Test failed: {str(e)}"
        }

def check_collinearity(X: pd.DataFrame, threshold: float = 5.0) -> Dict[str, Any]:
    """
    Calculate Variance Inflation Factors (VIF) for predictors.
    
    Args:
        X: DataFrame of predictor variables (including intercept if added).
        threshold: VIF threshold above which collinearity is flagged (default 5.0).
        
    Returns:
        Dictionary containing VIF for each feature, max VIF, and collinearity status.
    """
    if X.empty:
        logger.warning("Empty predictor matrix for collinearity check.")
        return {"vifs": {}, "max_vif": 0.0, "passed": True, "message": "No predictors"}

    # Ensure we have a constant if not already
    if not np.any(np.all(X == 1, axis=0)):
        try:
            X_with_const = sm.add_constant(X)
        except Exception:
            X_with_const = X
    else:
        X_with_const = X

    vifs = {}
    feature_names = X_with_const.columns
    
    for i, col in enumerate(feature_names):
        if col == 'const':
            continue
        
        # VIF calculation: 1 / (1 - R^2) where R^2 is from regression of col on all other cols
        y_vif = X_with_const[col]
        X_vif = X_with_const.drop(columns=[col])
        
        try:
            if X_vif.shape[1] == 0:
                vifs[col] = 1.0
                continue
                
            model_vif = sm.OLS(y_vif, X_vif).fit()
            r_squared = model_vif.rsquared
            vif_val = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else np.inf
            vifs[col] = float(vif_val)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vifs[col] = np.nan

    max_vif = max([v for v in vifs.values() if not np.isnan(v)] + [0.0])
    passed = max_vif < threshold
    
    status = "PASSED" if passed else "FLAGGED"
    message = f"Max VIF: {max_vif:.2f} (Threshold: {threshold}). "
    if not passed:
        message += f"Collinearity detected. Results should be framed descriptively without claiming independent effects."
    else:
        message += "No significant collinearity detected."
        
    logger.info(f"Collinearity (VIF): Max={max_vif:.2f} [{status}]")
    
    return {
        "test": "vif",
        "vifs": vifs,
        "max_vif": float(max_vif),
        "threshold": float(threshold),
        "passed": passed,
        "message": message
    }

def validate_model_assumptions(
    model: sm.OLSResults, 
    X: pd.DataFrame, 
    threshold_vif: float = 5.0
) -> Dict[str, Any]:
    """
    Run all assumption checks and aggregate results.
    
    Args:
        model: Fitted statsmodels OLS results object.
        X: Predictor DataFrame used for the model.
        threshold_vif: VIF threshold for collinearity.
        
    Returns:
        Aggregated dictionary of all assumption check results.
    """
    residuals = model.resid
    predicted = model.fittedvalues
    
    results = {
        "normality": check_normality(residuals),
        "homoscedasticity": check_homoscedasticity(residuals, predicted),
        "collinearity": check_collinearity(X, threshold_vif)
    }
    
    # Determine overall pass status
    all_passed = all([
        results["normality"]["passed"],
        results["homoscedasticity"]["passed"],
        results["collinearity"]["passed"]
    ])
    
    results["all_passed"] = all_passed
    results["summary"] = (
        "All assumptions met." if all_passed 
        else "One or more assumptions violated. Interpret with caution."
    )
    
    return results

# Aliases for compatibility
run_assumption_validation = validate_model_assumptions
validate_regression_assumptions = validate_model_assumptions