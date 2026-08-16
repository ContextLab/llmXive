"""
Modeling module for Propensity Score Weighting (PSW) and GLS fallback.
Implements FR-002, FR-003, FR-004, FR-008.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import Tuple, Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

def derive_baseline_interest_vector(history_categories: List[str]) -> np.ndarray:
    """
    Derive a baseline interest vector from pre-study history.
    Creates a frequency distribution vector representing the user's historical interests.
    
    Args:
        history_categories: List of historical category strings.
    
    Returns:
        Numpy array representing the interest vector (normalized frequencies).
    """
    if not history_categories:
        return np.array([])
    
    counts = {}
    for cat in history_categories:
        counts[cat] = counts.get(cat, 0) + 1
    
    total = len(history_categories)
    # Normalize to probability distribution
    vector = np.array([count / total for count in counts.values()])
    return vector

def calculate_propensity_scores(df: pd.DataFrame, 
                                treatment_col: str = "is_high_recommendation", 
                                covariates: Optional[List[str]] = None) -> pd.Series:
    """
    Calculate propensity scores using logistic regression.
    Estimates the probability of receiving the treatment (high recommendation exposure)
    given the observed covariates.
    
    Args:
        df: DataFrame with data.
        treatment_col: Name of the binary treatment column (0 or 1).
        covariates: List of covariate column names to use in the model.
    
    Returns:
        Series of propensity scores (probability of treatment).
    """
    if covariates is None:
        covariates = []
    
    # Ensure treatment is numeric and binary
    y = df[treatment_col].astype(float)
    
    # Prepare features
    if covariates:
        # Filter to existing columns only
        available_covariates = [c for c in covariates if c in df.columns]
        if not available_covariates:
            logger.warning("No valid covariates found. Using intercept only model.")
            X = pd.DataFrame(index=df.index)
        else:
            X = df[available_covariates]
    else:
        X = pd.DataFrame(index=df.index)
    
    # Add constant term
    X = sm.add_constant(X)
    
    # Handle missing values in treatment or covariates
    mask = ~(X.isna().any(axis=1) | y.isna())
    if mask.sum() < 10:
        raise ValueError("Insufficient non-missing data to fit propensity model.")
    
    X_fit = X[mask]
    y_fit = y[mask]
    
    # Fit logistic regression
    try:
        model = sm.Logit(y_fit, X_fit)
        result = model.fit(disp=0, maxiter=100)
    except Exception as e:
        logger.error(f"Logit model fitting failed: {e}")
        # Fallback to intercept-only if features fail
        if covariates:
            logger.info("Retrying with intercept-only model.")
            X_simple = sm.add_constant(pd.Series(1, index=y_fit.index))
            model = sm.Logit(y_fit, X_simple)
            result = model.fit(disp=0, maxiter=100)
        else:
            raise e
    
    # Map predictions back to original index
    propensity = pd.Series(np.nan, index=df.index)
    propensity[mask] = result.fittedvalues
    
    # Clip extreme probabilities to avoid division by zero in weights
    propensity = propensity.clip(lower=1e-6, upper=1-1e-6)
    
    return propensity

def calculate_stabilized_weights(propensity: pd.Series, treatment: pd.Series) -> pd.Series:
    """
    Calculate stabilized inverse propensity weights (IPW).
    Stabilized weights reduce variance compared to standard IPW by including
    the marginal probability of treatment in the numerator.
    
    Formula:
      If T=1: P(T=1) / P(T=1|X)
      If T=0: (1 - P(T=1)) / (1 - P(T=1|X))
    
    Args:
        propensity: Series of propensity scores (probability of treatment).
        treatment: Series of binary treatment indicators (0 or 1).
    
    Returns:
        Series of stabilized weights.
    """
    # Marginal probability of treatment
    p_treat = treatment.mean()
    
    # Ensure propensity is numeric and within bounds
    propensity = propensity.astype(float)
    propensity = propensity.clip(lower=1e-6, upper=1-1e-6)
    
    # Calculate weights
    weights = np.where(
        treatment == 1,
        p_treat / propensity,
        (1 - p_treat) / (1 - propensity)
    )
    
    return pd.Series(weights, index=treatment.index)

def check_weight_stability(weights: pd.Series, threshold: float = 10.0) -> bool:
    """
    Check if weights are stable (not extreme).
    
    Args:
        weights: Series of weights.
        threshold: Max allowed ratio of max_weight to median_weight.
    
    Returns:
        True if stable (ratio <= threshold), False otherwise.
    """
    if weights.empty:
        return False
    
    median_weight = weights.median()
    if median_weight == 0:
        logger.warning("Median weight is zero; stability check failed.")
        return False
    
    max_weight = weights.max()
    ratio = max_weight / median_weight
    
    if ratio > threshold:
        logger.warning(f"Extreme weights detected: max/median = {ratio:.2f} > {threshold}. "
                       "Consider trimming or using GLS fallback.")
        return False
    
    logger.info(f"Weight stability check passed (max/median = {ratio:.2f}).")
    return True

def fit_weighted_regression(df: pd.DataFrame, 
                            outcome: str, 
                            treatment: str, 
                            weights: pd.Series, 
                            covariates: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fit a weighted linear regression (WLS) to estimate the treatment effect.
    
    Args:
        df: DataFrame containing variables.
        outcome: Name of the outcome variable.
        treatment: Name of the treatment variable.
        weights: Series of weights (IPW).
        covariates: List of covariate names to include as controls.
    
    Returns:
        Dictionary with results: treatment_coef, treatment_se, treatment_pvalue, vif, r_squared.
    """
    # Prepare variables
    y = df[outcome]
    X_cols = [treatment]
    if covariates:
        X_cols.extend([c for c in covariates if c in df.columns])
    
    X = df[X_cols]
    
    # Align weights
    common_idx = y.index.intersection(X.index).intersection(weights.index)
    y = y.loc[common_idx]
    X = X.loc[common_idx]
    w = weights.loc[common_idx]
    
    if len(y) < 3:
        raise ValueError("Insufficient data points for regression.")
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit WLS
    model = sm.WLS(y, X, weights=w)
    result = model.fit()
    
    # Calculate VIF for multicollinearity diagnostics
    vif_data = {}
    for i, col in enumerate(X.columns):
        if col != 'const':
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
    
    return {
        "treatment_coef": result.params[treatment],
        "treatment_se": result.bse[treatment],
        "treatment_pvalue": result.pvalues[treatment],
        "vif": vif_data,
        "r_squared": result.rsquared,
        "n_obs": len(y),
        "method": "WLS"
    }

def fit_gls_fallback(df: pd.DataFrame, 
                     outcome: str, 
                     treatment: str, 
                     covariates: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fallback to Ordinary Least Squares (OLS) with Robust Standard Errors (HC3).
    Used when PSW fails, N < 30, or weights are unstable.
    
    Args:
        df: DataFrame containing variables.
        outcome: Name of the outcome variable.
        treatment: Name of the treatment variable.
        covariates: List of covariate names to include as controls.
    
    Returns:
        Dictionary with results: treatment_coef, treatment_se, treatment_pvalue, r_squared, method.
    """
    # Prepare variables
    y = df[outcome]
    X_cols = [treatment]
    if covariates:
        X_cols.extend([c for c in covariates if c in df.columns])
    
    X = df[X_cols]
    
    # Align indices
    common_idx = y.index.intersection(X.index)
    y = y.loc[common_idx]
    X = X.loc[common_idx]
    
    if len(y) < 3:
        raise ValueError("Insufficient data points for regression.")
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit OLS with robust standard errors (HC3)
    model = sm.OLS(y, X)
    result = model.fit(cov_type='HC3')
    
    return {
        "treatment_coef": result.params[treatment],
        "treatment_se": result.bse[treatment],
        "treatment_pvalue": result.pvalues[treatment],
        "r_squared": result.rsquared,
        "n_obs": len(y),
        "method": "OLS_HC3"
    }

def run_ps_analysis(df: pd.DataFrame, 
                    outcome: str, 
                    treatment: str, 
                    propensity_col: str, 
                    weights_col: str, 
                    covariates: Optional[List[str]] = None,
                    min_n: int = 30,
                    weight_stability_threshold: float = 10.0) -> Dict[str, Any]:
    """
    Orchestrates the full PSW analysis with fallback logic.
    
    Logic:
    1. Check sample size. If N < min_n, use GLS fallback immediately.
    2. Calculate propensity scores and stabilized weights.
    3. Check weight stability. If unstable, use GLS fallback.
    4. Fit weighted regression if stable.
    
    Args:
        df: DataFrame with data.
        outcome: Outcome variable name.
        treatment: Treatment variable name.
        propensity_col: Column name for pre-calculated propensity scores (optional).
        weights_col: Column name for pre-calculated weights (optional).
        covariates: List of covariate names.
        min_n: Minimum sample size to attempt PSW.
        weight_stability_threshold: Threshold for weight stability check.
    
    Returns:
        Dictionary containing model results and method used.
    """
    n = len(df)
    logger.info(f"Running analysis with N={n}. Threshold={min_n}.")
    
    # Fallback conditions
    use_fallback = False
    fallback_reason = ""
    
    if n < min_n:
        use_fallback = True
        fallback_reason = f"Sample size (N={n}) < minimum ({min_n})"
        logger.warning(f"Fallback to GLS: {fallback_reason}")
    
    if not use_fallback:
        # Check if weights are provided or need calculation
        if weights_col in df.columns:
            weights = df[weights_col]
            # Still check stability if weights exist
            stable = check_weight_stability(weights, weight_stability_threshold)
            if not stable:
                use_fallback = True
                fallback_reason = "Weight stability check failed"
                logger.warning(f"Fallback to GLS: {fallback_reason}")
        else:
            # Calculate propensity and weights
            if propensity_col in df.columns:
                propensity = df[propensity_col]
            else:
                logger.info("Calculating propensity scores...")
                propensity = calculate_propensity_scores(df, treatment_col=treatment, covariates=covariates)
            
            logger.info("Calculating stabilized weights...")
            weights = calculate_stabilized_weights(propensity, df[treatment])
            
            if not check_weight_stability(weights, weight_stability_threshold):
                use_fallback = True
                fallback_reason = "Calculated weights are unstable"
                logger.warning(f"Fallback to GLS: {fallback_reason}")
        
        if not use_fallback:
            logger.info("Fitting Weighted Linear Regression...")
            results = fit_weighted_regression(df, outcome, treatment, weights, covariates)
            results["method_used"] = "PSW"
            results["fallback_reason"] = None
            return results
    
    # Execute fallback
    logger.info("Executing GLS Fallback...")
    results = fit_gls_fallback(df, outcome, treatment, covariates)
    results["method_used"] = "GLS_Fallback"
    results["fallback_reason"] = fallback_reason
    return results