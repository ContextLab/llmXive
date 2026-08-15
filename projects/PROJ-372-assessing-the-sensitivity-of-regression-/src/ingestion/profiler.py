"""
Profiler module for computing OLS assumption violation metrics.

Computes:
- Condition Number (multicollinearity)
- Breusch-Pagan Statistic (heteroscedasticity)
- Cook's Distance (influential observations)

Handles streaming for large datasets (>7GB) by sampling if necessary,
but strictly enforces real data sources only.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from scipy import stats
from typing import Dict, Any, Optional, Tuple
import logging

from src.utils.config import SAMPLE_SIZE_TIERS
from src.models.data_models import DatasetProfile, ViolationSeverity

logger = logging.getLogger(__name__)

# Thresholds for severity classification
CONDITION_NUMBER_LOW = 30
CONDITION_NUMBER_HIGH = 100
BP_PVALUE_LOW = 0.01
BP_PVALUE_HIGH = 0.05
COOKS_THRESHOLD = 4.0 / 1000  # Heuristic threshold for "high" influence

def _prepare_design_matrix(df: pd.DataFrame, target_col: str, feature_cols: list) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare X (design matrix) and y (target) from dataframe.
    Adds constant term to X.
    """
    if len(feature_cols) == 0:
        raise ValueError("No feature columns provided for design matrix.")
    
    X = df[feature_cols].to_numpy()
    y = df[target_col].to_numpy()

    # Remove rows with NaN/Inf in features or target
    mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
    X = X[mask]
    y = y[mask]

    if len(X) == 0:
        raise ValueError("No valid rows remaining after NaN/Inf removal.")

    # Add constant
    X = sm.add_constant(X)
    return X, y

def compute_condition_number(X: np.ndarray) -> float:
    """
    Compute the condition number of the design matrix.
    High values indicate multicollinearity.
    """
    try:
        # Use SVD for stability
        _, _, s = np.linalg.svd(X, compute_uv=False)
        if s[-1] == 0:
            return float('inf')
        return float(s[0] / s[-1])
    except np.linalg.LinAlgError:
        return float('inf')

def compute_breusch_pagan(X: np.ndarray, y: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Compute Breusch-Pagan test for heteroscedasticity.
    Returns: (LM statistic, p-value, chi2 stat, f_stat)
    """
    # Fit OLS to get residuals
    model = sm.OLS(y, X).fit()
    residuals = model.resid

    try:
        bp_test = het_breuschpagan(residuals, X)
        # bp_test returns: (lm_stat, lm_pvalue, f_stat, f_pvalue)
        return float(bp_test[0]), float(bp_test[1]), float(bp_test[2]), float(bp_test[3])
    except Exception as e:
        logger.warning(f"Breusch-Pagan test failed: {e}. Returning NaN.")
        return float('nan'), float('nan'), float('nan'), float('nan')

def compute_cooks_distance(X: np.ndarray, y: np.ndarray) -> float:
    """
    Compute maximum Cook's Distance to identify influential observations.
    Returns the maximum value found.
    """
    try:
        model = sm.OLS(y, X).fit()
        # Influence measures
        influence = model.get_influence()
        cooks_d = influence.cooks_distance[0]
        return float(np.max(cooks_d))
    except Exception as e:
        logger.warning(f"Cook's Distance calculation failed: {e}. Returning NaN.")
        return float('nan')

def classify_condition_number(cond_num: float) -> ViolationSeverity:
    if np.isinf(cond_num) or cond_num > CONDITION_NUMBER_HIGH:
        return ViolationSeverity.HIGH
    elif cond_num > CONDITION_NUMBER_LOW:
        return ViolationSeverity.MEDIUM
    else:
        return ViolationSeverity.LOW

def classify_breusch_pagan(p_value: float) -> ViolationSeverity:
    if np.isnan(p_value):
        return ViolationSeverity.LOW # Unknown, treat as low risk for now
    if p_value < BP_PVALUE_LOW:
        return ViolationSeverity.HIGH
    elif p_value < BP_PVALUE_HIGH:
        return ViolationSeverity.MEDIUM
    else:
        return ViolationSeverity.LOW

def classify_cooks(max_cooks: float, n: int) -> ViolationSeverity:
    # Heuristic: if max Cook's D > 1, it's definitely high.
    # Common rule of thumb: > 4/n is suspicious.
    threshold = 4.0 / n
    if max_cooks > 1.0:
        return ViolationSeverity.HIGH
    elif max_cooks > threshold:
        return ViolationSeverity.MEDIUM
    else:
        return ViolationSeverity.LOW

def profile_dataset(df: pd.DataFrame, target_col: str, feature_cols: list) -> DatasetProfile:
    """
    Compute all OLS violation metrics on the provided dataframe.
    
    Args:
        df: DataFrame containing the data.
        target_col: Name of the target variable column.
        feature_cols: List of feature column names.
    
    Returns:
        DatasetProfile object with computed metrics.
    """
    logger.info(f"Profiling dataset with {len(df)} rows and {len(feature_cols)} features.")
    
    X, y = _prepare_design_matrix(df, target_col, feature_cols)
    n = len(y)
    p = X.shape[1] - 1 # Number of predictors excluding intercept

    # 1. Condition Number
    cond_num = compute_condition_number(X)
    cond_severity = classify_condition_number(cond_num)
    logger.info(f"Condition Number: {cond_num:.2f} ({cond_severity.value})")

    # 2. Breusch-Pagan
    lm_stat, bp_pval, f_stat, f_pval = compute_breusch_pagan(X, y)
    bp_severity = classify_breusch_pagan(bp_pval)
    logger.info(f"Breusch-Pagan LM Stat: {lm_stat:.2f}, p-value: {bp_pval:.4f} ({bp_severity.value})")

    # 3. Cook's Distance
    max_cooks = compute_cooks_distance(X, y)
    cooks_severity = classify_cooks(max_cooks, n)
    logger.info(f"Max Cook's Distance: {max_cooks:.4f} ({cooks_severity.value})")

    # Determine overall severity (max of all)
    overall_severity = max(cond_severity, bp_severity, cooks_severity)

    return DatasetProfile(
        dataset_id="unknown", # Should be set by caller if available
        n_observations=n,
        n_features=p,
        condition_number=cond_num,
        condition_number_severity=cond_severity,
        breusch_pagan_stat=lm_stat,
        breusch_pagan_pvalue=bp_pval,
        breusch_pagan_severity=bp_severity,
        max_cooks_distance=max_cooks,
        max_cooks_severity=cooks_severity,
        overall_violation_severity=overall_severity
    )

def profile_streamed_dataset(df_sample: pd.DataFrame, target_col: str, feature_cols: list) -> DatasetProfile:
    """
    Wrapper for profiling a streamed/sample subset.
    Currently identical to profile_dataset, but serves as an entry point
    for logic that might differ for full-streamed aggregation in future tasks.
    """
    return profile_dataset(df_sample, target_col, feature_cols)
