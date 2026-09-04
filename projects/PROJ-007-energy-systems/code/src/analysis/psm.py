"""
Propensity Score Matching module.
Implements logistic regression for propensity scores and nearest neighbor matching.
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, List
import warnings
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.utils.logging import get_logger

logger = get_logger(__name__)


def estimate_propensity(df: pd.DataFrame, treatment_col: str = 'treatment', covariates: List[str] = None) -> pd.DataFrame:
    """
    Estimate propensity scores using logistic regression.

    Args:
        df: Input DataFrame.
        treatment_col: Name of the treatment column.
        covariates: List of covariates to use for matching.

    Returns:
        DataFrame with added 'propensity' column.
    """
    if covariates is None:
        # Default to common covariates if not specified
        covariates = [col for col in df.columns if col not in [treatment_col, 'id']]

    X = df[covariates]
    y = df[treatment_col]

    # Handle missing values in covariates
    if X.isnull().any().any():
        logger.warning("Missing values in covariates. Imputing with mean.")
        X = X.fillna(X.mean())

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)

    propensity = model.predict_proba(X_scaled)[:, 1]

    df_out = df.copy()
    df_out['propensity'] = propensity

    return df_out


def match_pairs(
    df: pd.DataFrame,
    caliper: float = 0.2,
    treatment_col: str = 'treatment'
) -> pd.DataFrame:
    """
    Perform nearest neighbor matching with caliper.

    Args:
        df: DataFrame with propensity scores.
        caliper: Maximum difference in propensity scores for a match.
        treatment_col: Name of treatment column.

    Returns:
        DataFrame with matched pairs (only matched rows).
    """
    treat = df[df[treatment_col] == 1].copy()
    ctrl = df[df[treatment_col] == 0].copy()

    if treat.empty or ctrl.empty:
        logger.warning("One of the groups is empty.")
        return pd.DataFrame()

    # Sort controls by propensity for efficient matching
    ctrl = ctrl.sort_values('propensity')

    matched_indices = []

    for _, t_row in treat.iterrows():
        t_prop = t_row['propensity']
        # Find controls within caliper
        valid_ctrl = ctrl[
            (ctrl['propensity'] >= t_prop - caliper) &
            (ctrl['propensity'] <= t_prop + caliper)
        ]

        if not valid_ctrl.empty:
            # Pick nearest neighbor
            nearest = valid_ctrl.loc[
                (valid_ctrl['propensity'] - t_prop).abs().idxmin()
            ]
            matched_indices.append(nearest.name)
            # Remove matched control to avoid replacement (optional, but common)
            ctrl = ctrl.drop(nearest.name)

    if not matched_indices:
        logger.warning("No matches found.")
        return pd.DataFrame()

    matched_ctrl = df.loc[matched_indices]
    matched_treat = treat

    # Combine and add match ID
    matched_ctrl['match_id'] = matched_ctrl.index
    matched_treat['match_id'] = matched_treat.index

    result = pd.concat([matched_treat, matched_ctrl])
    result = result.sort_values('match_id')

    return result


def check_common_support(df: pd.DataFrame, treatment_col: str = 'treatment') -> pd.DataFrame:
    """
    Flag/exclude observations with extreme propensity scores.

    Args:
        df: DataFrame with propensity scores.
        treatment_col: Treatment column name.

    Returns:
        Filtered DataFrame within common support.
    """
    # Define common support region (e.g., min prop of control to max prop of treatment)
    ctrl_min = df[df[treatment_col] == 0]['propensity'].min()
    treat_max = df[df[treatment_col] == 1]['propensity'].max()

    # Keep observations within the overlap
    # Usually: max(ctrl_min, treat_min) < prop < min(ctrl_max, treat_max)
    # Simplified: keep if prop is within the range of the other group's support
    mask = (
        (df['propensity'] >= ctrl_min) &
        (df['propensity'] <= treat_max)
    )
    # Actually, common support is usually the intersection of the supports.
    # Let's use the intersection of [min_ctrl, max_ctrl] and [min_treat, max_treat]
    min_overall = max(df[df[treatment_col]==0]['propensity'].min(), df[df[treatment_col]==1]['propensity'].min())
    max_overall = min(df[df[treatment_col]==0]['propensity'].max(), df[df[treatment_col]==1]['propensity'].max())

    mask = (df['propensity'] >= min_overall) & (df['propensity'] <= max_overall)
    logger.info(f"Common support check: {mask.sum()} rows retained out of {len(df)}.")

    return df[mask]


def iterative_matching(
    df: pd.DataFrame,
    covariates: List[str],
    caliper: float = 0.2,
    max_iter: int = 10
) -> Optional[pd.DataFrame]:
    """
    Perform iterative matching with caliper adjustment.

    Args:
        df: Input data.
        covariates: Covariates for propensity score.
        caliper: Initial caliper.
        max_iter: Maximum iterations.

    Returns:
        Matched DataFrame or None.
    """
    current_caliper = caliper

    for i in range(max_iter):
        # Estimate propensity
        df_prop = estimate_propensity(df, covariates=covariates)

        # Check common support
        df_support = check_common_support(df_prop)

        if df_support.empty:
            logger.warning("No common support found.")
            return None

        # Match
        matched = match_pairs(df_support, caliper=current_caliper)

        if not matched.empty:
            return matched

        # Reduce caliper if no matches
        current_caliper *= 0.8
        logger.info(f"Iteration {i+1}: No matches with caliper {current_caliper:.3f}. Reducing...")

    logger.error("Max iterations reached without finding matches.")
    return None
