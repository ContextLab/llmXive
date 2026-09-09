import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import GLS, WLS
from statsmodels.tools import add_constant
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class RegressionResult:
    """Container for regression analysis results."""
    coefficient: float
    std_error: float
    p_value: float
    method: str
    weights_stable: bool
    extreme_weights_detected: bool
    max_weight_ratio: float
    vif_values: Optional[Dict[str, float]] = None
    diagnostics: Optional[Dict[str, Any]] = None

def derive_baseline_interest_vector(df: pd.DataFrame, history_col: str = 'pre_study_history') -> np.ndarray:
    """
    Derive baseline interest vector from pre-study history.
    
    Args:
        df: DataFrame with historical category data
        history_col: Column name containing historical category lists
        
    Returns:
        Normalized baseline interest vector
    """
    if history_col not in df.columns:
        logger.warning(f"Column '{history_col}' not found. Returning zero vector.")
        return np.zeros(1)
    
    # Flatten all historical categories
    all_cats = []
    for cats in df[history_col].dropna():
        if isinstance(cats, list):
            all_cats.extend(cats)
        elif isinstance(cats, str):
            all_cats.append(cats)
    
    if not all_cats:
        return np.zeros(1)
    
    # Create frequency vector (simplified for demonstration)
    unique_cats = list(set(all_cats))
    counts = np.array([all_cats.count(c) for c in unique_cats])
    return counts / counts.sum() if counts.sum() > 0 else np.zeros(1)

def calculate_propensity_scores(df: pd.DataFrame, treatment_col: str = 'high_diversity_rec', 
                                covariates: Optional[list] = None) -> pd.Series:
    """
    Calculate propensity scores for treatment assignment.
    
    Args:
        df: DataFrame with treatment and covariate data
        treatment_col: Column indicating treatment assignment
        covariates: List of covariate column names
        
    Returns:
        Series of propensity scores
    """
    if covariates is None:
        covariates = ['learner_diversity_score', 'baseline_interest_vector']
    
    # Filter to available columns
    available_covariates = [c for c in covariates if c in df.columns]
    
    if not available_covariates:
        logger.warning("No covariates available. Using intercept-only model.")
        X = sm.add_constant(pd.Series([1] * len(df)))
    else:
        X = df[available_covariates]
        X = sm.add_constant(X)
    
    y = df[treatment_col].astype(int)
    
    # Fit logistic regression
    model = sm.Logit(y, X)
    result = model.fit(disp=False)
    
    return result.fittedvalues

def calculate_stabilized_weights(df: pd.DataFrame, propensity: pd.Series, 
                                 treatment_col: str = 'high_diversity_rec') -> pd.Series:
    """
    Calculate stabilized inverse probability weights.
    
    Args:
        df: DataFrame with treatment data
        propensity: Series of propensity scores
        treatment_col: Column indicating treatment assignment
        
    Returns:
        Series of stabilized weights
    """
    treatment = df[treatment_col].astype(int)
    ps = propensity.clip(0.01, 0.99)  # Clip to avoid division by zero
    
    weights = np.where(
        treatment == 1,
        ps.mean() / ps,
        (1 - ps.mean()) / (1 - ps)
    )
    
    return pd.Series(weights, index=df.index)

def check_weight_stability(weights: pd.Series, threshold: float = 10.0) -> Tuple[bool, float]:
    """
    Check if weights are stable (not extreme).
    
    Args:
        weights: Series of propensity weights
        threshold: Maximum allowed ratio of max weight to median weight
        
    Returns:
        Tuple of (is_stable, max_ratio)
    """
    if len(weights) == 0:
        return True, 0.0
    
    median_weight = weights.median()
    if median_weight == 0:
        return False, float('inf')
    
    max_weight = weights.max()
    ratio = max_weight / median_weight
    
    is_stable = ratio <= threshold
    return is_stable, ratio

def check_weight_stability_and_log(weights: pd.Series, threshold: float = 10.0, 
                                   logger_name: Optional[str] = None) -> Tuple[bool, float]:
    """
    Check weight stability and log methodological warnings if extreme weights detected.
    
    This function implements T024: detection of extreme weights and flagging 
    methodological changes in logs.
    
    Args:
        weights: Series of propensity weights
        threshold: Maximum allowed ratio of max weight to median weight (default 10.0)
        logger_name: Optional logger name, defaults to 'modeling'
        
    Returns:
        Tuple of (is_stable, max_ratio)
    """
    is_stable, ratio = check_weight_stability(weights, threshold)
    
    if logger_name:
        log_logger = logging.getLogger(logger_name)
    else:
        log_logger = logger
    
    if not is_stable:
        log_logger.warning(
            f"EXTREME WEIGHTS DETECTED: Max/median weight ratio is {ratio:.2f}, "
            f"exceeding threshold of {threshold}. "
            f"Methodological note: Results may be sensitive to model specification "
            f"and unmeasured confounding. Consider GLS fallback or trimming."
        )
    else:
        log_logger.info(f"Weight stability check passed: Max/median ratio = {ratio:.2f} <= {threshold}")
    
    return is_stable, ratio

def fit_weighted_regression(df: pd.DataFrame, outcome_col: str, treatment_col: str, 
                            weights: pd.Series) -> RegressionResult:
    """
    Fit weighted linear regression with diagnostics.
    
    Args:
        df: DataFrame with outcome, treatment, and covariates
        outcome_col: Name of outcome variable
        treatment_col: Name of treatment variable
        weights: Series of weights
        
    Returns:
        RegressionResult with coefficients and diagnostics
    """
    X = df[[treatment_col]]
    X = add_constant(X)
    y = df[outcome_col]
    
    model = WLS(y, X, weights=weights)
    result = model.fit()
    
    # Calculate VIF
    vif_values = {}
    for i, col in enumerate(X.columns):
        vif_values[col] = variance_inflation_factor(X.values, i)
    
    return RegressionResult(
        coefficient=result.params[1] if len(result.params) > 1 else 0,
        std_error=result.bse[1] if len(result.bse) > 1 else 0,
        p_value=result.pvalues[1] if len(result.pvalues) > 1 else 1.0,
        method="WLS",
        weights_stable=True,
        extreme_weights_detected=False,
        max_weight_ratio=1.0,
        vif_values=vif_values,
        diagnostics={'n_obs': len(df), 'r_squared': result.rsquared}
    )

def fit_gls_fallback(df: pd.DataFrame, outcome_col: str, treatment_col: str) -> RegressionResult:
    """
    Fallback to Generalized Least Squares with robust standard errors.
    
    Args:
        df: DataFrame with outcome and treatment
        outcome_col: Name of outcome variable
        treatment_col: Name of treatment variable
        
    Returns:
        RegressionResult with GLS coefficients
    """
    X = df[[treatment_col]]
    X = add_constant(X)
    y = df[outcome_col]
    
    # Fit GLS (simple version with robust SEs)
    model = GLS(y, X)
    result = model.fit(cov_type='HC3')
    
    vif_values = {}
    for i, col in enumerate(X.columns):
        vif_values[col] = variance_inflation_factor(X.values, i)
    
    logger.warning("Fallback to GLS triggered due to PSW instability or small N.")
    
    return RegressionResult(
        coefficient=result.params[1] if len(result.params) > 1 else 0,
        std_error=result.bse[1] if len(result.bse) > 1 else 0,
        p_value=result.pvalues[1] if len(result.pvalues) > 1 else 1.0,
        method="GLS",
        weights_stable=True,
        extreme_weights_detected=False,
        max_weight_ratio=1.0,
        vif_values=vif_values,
        diagnostics={'n_obs': len(df), 'r_squared': result.rsquared}
    )

def run_ps_analysis(df: pd.DataFrame, outcome_col: str = 'learner_diversity_score',
                    treatment_col: str = 'high_diversity_rec',
                    propensity_col: str = 'propensity_score',
                    weight_col: str = 'stabilized_weight') -> RegressionResult:
    """
    Run full propensity score analysis with weight stability checks.
    
    This function orchestrates PSW calculation, stability checking, and regression.
    It implements T024 by logging extreme weight detection.
    
    Args:
        df: Processed DataFrame
        outcome_col: Outcome variable name
        treatment_col: Treatment variable name
        propensity_col: Column name for propensity scores
        weight_col: Column name for stabilized weights
        
    Returns:
        RegressionResult with analysis output
    """
    # Calculate propensity scores if not present
    if propensity_col not in df.columns:
        logger.info(f"Calculating propensity scores for {treatment_col}")
        df[propensity_col] = calculate_propensity_scores(df, treatment_col)
    
    # Calculate weights if not present
    if weight_col not in df.columns:
        logger.info(f"Calculating stabilized weights")
        df[weight_col] = calculate_stabilized_weights(df, df[propensity_col], treatment_col)
    
    # Check weight stability (T024 implementation)
    weights = df[weight_col]
    is_stable, max_ratio = check_weight_stability_and_log(weights, threshold=10.0, logger_name='modeling')
    
    # Decide method based on stability and sample size
    if len(df) < 30 or not is_stable:
        logger.warning(f"PSW unstable or N={len(df)} < 30. Falling back to GLS.")
        result = fit_gls_fallback(df, outcome_col, treatment_col)
        result.weights_stable = is_stable
        result.extreme_weights_detected = not is_stable
        result.max_weight_ratio = max_ratio
    else:
        result = fit_weighted_regression(df, outcome_col, treatment_col, weights)
        result.weights_stable = is_stable
        result.extreme_weights_detected = not is_stable
        result.max_weight_ratio = max_ratio
    
    return result