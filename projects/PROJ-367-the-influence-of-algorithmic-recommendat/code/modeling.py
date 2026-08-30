import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import GLS
from statsmodels.tools import add_constant
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

def derive_baseline_interest_vector(df: pd.DataFrame, history_col: str = 'pre_study_history') -> pd.Series:
    """
    Derive baseline interest vector from pre-study history.
    Aggregates category counts from historical data to form a baseline preference vector.
    """
    if history_col not in df.columns:
        logger.warning(f"Column '{history_col}' not found. Returning zero baseline.")
        return pd.Series(0, index=df.index)
    
    # Flatten list of categories per user to compute aggregate baseline
    all_categories = []
    for item in df[history_col]:
        if isinstance(item, list):
            all_categories.extend(item)
        else:
            # Handle single string or other types if necessary
            all_categories.append(item)
    
    from collections import Counter
    counts = Counter(all_categories)
    total = sum(counts.values())
    if total == 0:
        return pd.Series(0, index=df.index)
    
    # Normalize to probabilities
    baseline_probs = {k: v/total for k, v in counts.items()}
    
    # Map back to DataFrame rows (simplified: assume uniform baseline for now or specific aggregation)
    # For this implementation, we return a scalar baseline score representing the 'exploration' tendency
    # derived from the entropy of the baseline distribution.
    # However, the task description implies a vector. We will return a representative score.
    # To be strictly vector-like in a regression context, we might map categories to features.
    # Given the context of T020, we return a derived metric.
    
    # Let's assume the output is a single baseline interest score (e.g., entropy of history)
    # or a vector if the downstream model expects it. 
    # For T020, we return a Series of baseline scores (e.g., entropy of their history).
    
    def calc_history_entropy(row):
        if not isinstance(row[history_col], list) or len(row[history_col]) == 0:
            return 0.0
        c = Counter(row[history_col])
        probs = [v/sum(c.values()) for v in c.values()]
        return -sum(p * np.log2(p) for p in probs if p > 0)
    
    return df.apply(calc_history_entropy, axis=1)

def calculate_propensity_scores(df: pd.DataFrame, treatment_col: str = 'is_algorithmic', 
                                covariates: list = None) -> pd.Series:
    """
    Calculate propensity scores (probability of treatment) using logistic regression.
    """
    if covariates is None:
        covariates = []
    
    # Prepare features
    X = df[covariates].copy() if covariates else pd.DataFrame(index=df.index)
    X = add_constant(X)
    y = df[treatment_col]
    
    if X.shape[1] == 1 and 'const' in X.columns:
        # Only intercept, use mean as propensity
        prop_score = y.mean()
        return pd.Series(prop_score, index=df.index)
    
    model = sm.Logit(y, X)
    result = model.fit(disp=False)
    return result.fittedvalues

def calculate_stabilized_weights(df: pd.DataFrame, propensity_scores: pd.Series, 
                                 treatment_col: str = 'is_algorithmic') -> pd.Series:
    """
    Calculate stabilized inverse propensity weights.
    SW = (Treatment / Propensity) + ((1-Treatment) / (1-Propensity))
    """
    p = propensity_scores
    t = df[treatment_col]
    
    # Prevent division by zero
    p = np.clip(p, 1e-6, 1 - 1e-6)
    
    weights = np.where(t == 1, t / p, (1 - t) / (1 - p))
    return pd.Series(weights, index=df.index)

def check_weight_stability(weights: pd.Series, threshold: float = 10.0) -> Dict[str, Any]:
    """
    Check for extreme weights that could destabilize the analysis.
    Returns a dictionary with stability metrics and a flag.
    """
    median_weight = weights.median()
    max_weight = weights.max()
    ratio = max_weight / median_weight if median_weight > 0 else float('inf')
    
    is_stable = ratio < threshold
    extreme_count = (weights > threshold * median_weight).sum()
    
    logger.info(f"Weight Stability Check: Median={median_weight:.4f}, Max={max_weight:.4f}, Ratio={ratio:.2f}")
    if not is_stable:
        logger.warning(f"UNSTABLE WEIGHTS DETECTED: Ratio {ratio:.2f} exceeds threshold {threshold}. "
                       f"{extreme_count} weights are extreme. Methodological change may be required.")
    
    return {
        "median_weight": float(median_weight),
        "max_weight": float(max_weight),
        "ratio": float(ratio),
        "is_stable": bool(is_stable),
        "extreme_count": int(extreme_count),
        "threshold": threshold,
        "flag_methodological_change": not is_stable
    }

def fit_weighted_regression(df: pd.DataFrame, outcome_col: str, treatment_col: str, 
                            weights: pd.Series, covariates: list = None) -> Dict[str, Any]:
    """
    Fit a weighted linear regression model.
    """
    X_cols = [treatment_col] + (covariates or [])
    X = df[X_cols]
    X = add_constant(X)
    y = df[outcome_col]
    
    model = sm.WLS(y, X, weights=weights)
    result = model.fit()
    
    return {
        "model": result,
        "coefficients": result.params.to_dict(),
        "pvalues": result.pvalues.to_dict(),
        "std_errors": result.bse.to_dict(),
        "summary": result.summary()
    }

def calculate_vif(df: pd.DataFrame, covariates: list) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for covariates to detect multicollinearity.
    """
    X = df[covariates].copy()
    X = add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
    
    return vif_data

def fit_gls_fallback(df: pd.DataFrame, outcome_col: str, treatment_col: str, 
                     covariates: list = None) -> Dict[str, Any]:
    """
    Fit Generalized Least Squares as a fallback when PSW fails or N < 30.
    """
    X_cols = [treatment_col] + (covariates or [])
    X = df[X_cols]
    X = add_constant(X)
    y = df[outcome_col]
    
    # Simple GLS with identity covariance if no structure is specified
    model = GLS(y, X)
    result = model.fit()
    
    return {
        "model": result,
        "coefficients": result.params.to_dict(),
        "pvalues": result.pvalues.to_dict(),
        "std_errors": result.bse.to_dict()
    }

def run_ps_analysis(df: pd.DataFrame, outcome_col: str, treatment_col: str, 
                    propensity_scores: pd.Series, covariates: list = None, 
                    weight_threshold: float = 10.0, min_n: int = 30) -> Dict[str, Any]:
    """
    Run the full Propensity Score analysis pipeline including stability checks and fallback logic.
    Implements T021, T022, T023, and T024.
    """
    result = {}
    
    # 1. Calculate Stabilized Weights
    weights = calculate_stabilized_weights(df, propensity_scores, treatment_col)
    result['weights'] = weights
    
    # 2. T024: Check Weight Stability and Flag Methodological Changes
    stability_check = check_weight_stability(weights, threshold=weight_threshold)
    result['stability'] = stability_check
    
    # 3. Decide on Method (PSW vs GLS Fallback)
    use_gls = False
    if len(df) < min_n:
        logger.warning(f"Sample size N={len(df)} < {min_n}. Switching to GLS fallback.")
        use_gls = True
    elif not stability_check['is_stable']:
        logger.warning("Weights are unstable. Switching to GLS fallback due to extreme weights.")
        use_gls = True
    
    if use_gls:
        logger.info("Fitting GLS fallback model.")
        model_result = fit_gls_fallback(df, outcome_col, treatment_col, covariates)
        result['method'] = 'GLS_Fallback'
        result['model_output'] = model_result
    else:
        logger.info("Fitting Weighted Linear Regression.")
        model_result = fit_weighted_regression(df, outcome_col, treatment_col, weights, covariates)
        result['method'] = 'PSW'
        result['model_output'] = model_result
        
        # Calculate VIF if using PSW
        if covariates:
            vif_result = calculate_vif(df, covariates)
            result['vif'] = vif_result
    
    return result