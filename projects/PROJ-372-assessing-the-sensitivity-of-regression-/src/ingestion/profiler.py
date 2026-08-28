"""
Profiler module to compute OLS assumption violation metrics.

Computes:
- Condition Number (Multicollinearity)
- Breusch-Pagan Statistic (Heteroscedasticity)
- Cook's Distance (Influential Observations)

Handles large datasets (>7GB) via streaming aggregation or subsampling.
"""
import logging
import os
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.utils.logger import get_logger
from src.utils.config import SAMPLE_SIZE_TIERS

# Constants
CONDITION_NUMBER_THRESHOLD = 30.0
SUBSAMPLE_LIMIT = 100_000  # Max rows for CPU-feasible profiling
LARGE_DATASET_THRESHOLD = 7 * 1024 * 1024 * 1024  # 7GB

logger = get_logger(__name__)


def _prepare_design_matrix(df: pd.DataFrame, target_col: str, feature_cols: list) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare design matrix X and target vector y.
    Adds a constant term to X.
    """
    if not all(col in df.columns for col in feature_cols):
        missing = set(feature_cols) - set(df.columns)
        raise ValueError(f"Missing feature columns: {missing}")
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe")

    y = df[target_col].values.astype(float)
    X = df[feature_cols].values.astype(float)

    # Handle missing values by dropping rows where X or y is NaN
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]

    if len(y) == 0:
        raise ValueError("No valid data points remaining after NaN removal")

    X = sm.add_constant(X)
    return X, y


def compute_condition_number(X: np.ndarray) -> float:
    """
    Compute the condition number of the design matrix X.
    High values indicate multicollinearity.
    """
    try:
        # Use 2-norm condition number
        cond_num = np.linalg.cond(X, p=2)
        return float(cond_num)
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix encountered during condition number computation.")
        return float('inf')


def compute_breusch_pagan(X: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Compute the Breusch-Pagan test statistic and p-value for heteroscedasticity.

    Returns:
        Tuple of (statistic, p_value)
    """
    # Fit OLS first to get residuals
    model = sm.OLS(y, X)
    try:
        results = model.fit()
    except Exception as e:
        logger.warning(f"OLS fit failed for BP test: {e}")
        return 0.0, 1.0  # Return neutral values if fit fails

    residuals = results.resid
    n = len(residuals)

    if n <= len(X[0]):
        # Not enough degrees of freedom
        return 0.0, 1.0

    # BP Test: Regress squared residuals on X
    # h = residuals^2
    h = residuals ** 2
    h_mean = h.mean()
    # Avoid division by zero
    if h_mean == 0:
        return 0.0, 1.0

    # Scale squared residuals
    scaled_h = h / h_mean

    # Add constant if not present (X already has constant from _prepare_design_matrix)
    # But we need to be careful: BP test usually regresses on original X or a subset
    # Here we regress on X (including constant)
    try:
        bp_model = sm.OLS(scaled_h, X).fit()
        explained_var = bp_model.ess
        n_obs = len(scaled_h)
        
        # BP Statistic = n * R^2 of auxiliary regression
        # R^2 = ESS / TSS
        # TSS = sum((scaled_h - mean(scaled_h))^2)
        tss = np.sum((scaled_h - scaled_h.mean()) ** 2)
        if tss == 0:
            return 0.0, 1.0
        
        r_squared = explained_var / tss
        bp_stat = n_obs * r_squared
        
        # Degrees of freedom = k - 1 (excluding constant)
        k = X.shape[1]
        df = k - 1
        
        if df <= 0:
            return 0.0, 1.0
            
        p_value = 1.0 - stats.chi2.cdf(bp_stat, df)
        return float(bp_stat), float(p_value)
    except Exception as e:
        logger.warning(f"BP auxiliary regression failed: {e}")
        return 0.0, 1.0


def compute_cooks_distance(X: np.ndarray, y: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Compute Cook's Distance for each observation.

    Returns:
        Tuple of (max_cooks_distance, array_of_distances)
    """
    model = sm.OLS(y, X)
    try:
        results = model.fit()
    except Exception as e:
        logger.warning(f"OLS fit failed for Cook's Distance: {e}")
        return 0.0, np.array([])

    # Cook's Distance formula:
    # D_i = sum_j ( (y_hat_j(i) - y_hat_j)^2 ) / (p * MSE)
    # Where y_hat_j(i) is the prediction for obs j when obs i is removed
    # statsmodels provides this directly
    
    try:
        influence = results.get_influence()
        cooks_d = influence.cooks_distance[0]
        max_cooks = float(np.max(cooks_d))
        return max_cooks, cooks_d
    except Exception as e:
        logger.warning(f"Could not compute Cook's Distance: {e}")
        return 0.0, np.array([])


def classify_violation_severity(stat_value: float, threshold_low: float, threshold_high: float) -> str:
    """
    Classify severity based on statistic value.
    """
    if stat_value <= threshold_low:
        return "Low"
    elif stat_value <= threshold_high:
        return "Medium"
    else:
        return "High"


def compute_profile_metrics(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list,
    is_streaming_sample: bool = False
) -> Dict[str, Any]:
    """
    Compute all OLS violation metrics on the provided dataframe.

    Args:
        df: DataFrame containing the data (full or subsampled)
        target_col: Name of the target variable
        feature_cols: List of feature column names
        is_streaming_sample: Flag indicating if this is a streamed sample

    Returns:
        Dictionary containing computed metrics and classifications
    """
    logger.info(f"Computing profile metrics for {len(df)} rows...")

    # Prepare data
    X, y = _prepare_design_matrix(df, target_col, feature_cols)

    # 1. Condition Number
    condition_number = compute_condition_number(X)
    cond_severity = classify_violation_severity(
        condition_number,
        threshold_low=30.0,
        threshold_high=100.0
    )
    logger.info(f"Condition Number: {condition_number:.4f} ({cond_severity})")

    # 2. Breusch-Pagan
    bp_stat, bp_pvalue = compute_breusch_pagan(X, y)
    # Heteroscedasticity is significant if p-value is low
    # We classify based on the statistic magnitude relative to degrees of freedom
    # Rough heuristic: stat > df implies significance
    k = X.shape[1]
    bp_severity = classify_violation_severity(
        bp_stat,
        threshold_low=k - 1, # Approx df
        threshold_high=2 * (k - 1)
    )
    logger.info(f"Breusch-Pagan Stat: {bp_stat:.4f}, p-value: {bp_pvalue:.4f} ({bp_severity})")

    # 3. Cook's Distance
    max_cooks, _ = compute_cooks_distance(X, y)
    # Thresholds for Cook's D are often 4/n or 1
    n = len(y)
    cook_threshold = 4 / n
    cook_severity = classify_violation_severity(
        max_cooks,
        threshold_low=cook_threshold,
        threshold_high=1.0
    )
    logger.info(f"Max Cook's Distance: {max_cooks:.4f} ({cook_severity})")

    return {
        "n_observations": int(n),
        "n_features": int(len(feature_cols)),
        "condition_number": condition_number,
        "condition_severity": cond_severity,
        "breusch_pagan_stat": bp_stat,
        "breusch_pagan_pvalue": bp_pvalue,
        "bp_severity": bp_severity,
        "max_cooks_distance": max_cooks,
        "cook_severity": cook_severity,
        "is_streaming_sample": is_streaming_sample
    }


def ingest_and_profile(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list,
    output_path: str
) -> Dict[str, Any]:
    """
    Main entry point for profiling a dataset.
    Handles subsampling for large datasets and writes results to JSON.

    Args:
        df: Input DataFrame
        target_col: Target variable name
        feature_cols: Feature variable names
        output_path: Path to save the profile JSON

    Returns:
        The profile dictionary
    """
    # Check size for subsampling logic (T016, T019)
    # If dataset > 100k rows, subsample to 100k for CPU feasibility (T016)
    # If dataset > 7GB, we assume streaming was already handled by downloader
    # Here we just enforce the 100k row limit for the profiler step if needed
    
    working_df = df
    is_streaming_sample = False

    if len(df) > SUBSAMPLE_LIMIT:
        logger.warning(f"Dataset size ({len(df)}) exceeds limit ({SUBSAMPLE_LIMIT}). Subsampling.")
        # Deterministic subsample for reproducibility
        working_df = df.sample(n=SUBSAMPLE_LIMIT, random_state=42)
        is_streaming_sample = True
        logger.info(f"Subsampled to {len(working_df)} rows.")

    # Compute metrics
    profile = compute_profile_metrics(working_df, target_col, feature_cols, is_streaming_sample)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to JSON
    import json
    with open(output_path, 'w') as f:
        json.dump(profile, f, indent=2)

    logger.info(f"Profile saved to {output_path}")
    return profile