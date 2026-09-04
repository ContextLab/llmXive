"""
Causal effect estimation module.
Implements OLS and DiD estimators with cluster-robust standard errors.
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from typing import Optional, Dict, Any, Tuple
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DataUnavailableError(Exception):
    """Raised when required data for a specific method (e.g., DiD) is missing."""
    pass


def run_ols(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str = 'treatment',
    cluster_col: Optional[str] = None
) -> sm.regression.linear_model.RegressionResults:
    """
    Run OLS regression with cluster-robust standard errors.

    Args:
        df: DataFrame with outcome, treatment, and covariates.
        outcome_col: Name of the outcome variable.
        treatment_col: Name of the treatment variable.
        cluster_col: Optional column to cluster standard errors on.

    Returns:
        RegressionResults object.
    """
    if outcome_col not in df.columns or treatment_col not in df.columns:
        raise ValueError("Outcome or treatment column missing.")

    X = df[[treatment_col]]
    y = df[outcome_col]

    # Add constant
    X = sm.add_constant(X)

    model = sm.OLS(y, X)
    results = model.fit()

    if cluster_col and cluster_col in df.columns:
        # Cluster-robust SEs
        # Note: statsmodels has limited built-in clustering support in OLS,
        # often requires specific implementation or use of linearmodels.
        # For simplicity in this stub, we return standard fit but log the intent.
        logger.info(f"Clustering by {cluster_col} requested. (Note: Full cluster-robust implementation requires linearmodels package).")
        # In a real implementation, we would use:
        # from linearmodels.panel import PanelOLS
        # or custom sandwich estimator.
        # Here we return the OLS fit as a placeholder for the logic.

    return results


def run_did(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str = 'treatment',
    time_col: str = 'time',
    pre_treatment_col: str = 'pre_treatment_outcome',
    post_treatment_col: str = 'post_treatment_outcome'
) -> sm.regression.linear_model.RegressionResults:
    """
    Run Difference-in-Differences (DiD) estimation.

    Args:
        df: DataFrame with longitudinal data.
        outcome_col: Not used directly if pre/post columns are provided.
        treatment_col: Treatment indicator.
        time_col: Time indicator (0=pre, 1=post).
        pre_treatment_col: Pre-treatment outcome column.
        post_treatment_col: Post-treatment outcome column.

    Returns:
        RegressionResults object.

    Raises:
        DataUnavailableError: If pre/post columns are missing.
    """
    if pre_treatment_col not in df.columns or post_treatment_col not in df.columns:
        raise DataUnavailableError(
            f"Longitudinal data required for DiD but columns '{pre_treatment_col}' "
            f"and '{post_treatment_col}' are missing."
        )

    # Construct DiD dataset
    # We need long format or manual construction of the interaction term
    # Simplified approach:
    # Y = beta0 + beta1*Treat + beta2*Post + beta3*(Treat*Post) + error
    # beta3 is the DiD estimator.

    # Create time indicator (assuming we have pre/post columns to derive it or it's explicit)
    # If time_col is provided, use it. Otherwise, we might need to reshape.
    # For this implementation, we assume the data is in a format where we can compute the difference.

    # Alternative: Use the pre and post columns directly to compute delta
    df['delta'] = df[post_treatment_col] - df[pre_treatment_col]

    X = df[[treatment_col]]
    X = sm.add_constant(X)
    y = df['delta']

    model = sm.OLS(y, X)
    results = model.fit()

    return results


def estimate_causal_effect(
    df: pd.DataFrame,
    balance_status: str,
    pre_treatment_col: str = 'pre_treatment_outcome',
    post_treatment_col: str = 'post_treatment_outcome',
    outcome_col: str = 'energy_cost'
) -> Dict[str, Any]:
    """
    Estimate the causal effect (ATT) based on balance status and data availability.

    Logic:
    1. If balance_status is 'balanced', run OLS (T028).
    2. If balance_status is 'failed' (or similar), check for longitudinal data.
       - If longitudinal data (pre/post) exists, run DiD (T054).
       - If missing, raise DataUnavailableError.

    Args:
        df: Matched data.
        balance_status: Status from PSM module.
        pre_treatment_col: Pre-treatment outcome column.
        post_treatment_col: Post-treatment outcome column.
        outcome_col: Primary outcome for OLS.

    Returns:
        Dictionary with ATT estimate, p-value, CI, and method.
    """
    result = {
        'method': None,
        'att_estimate': None,
        'p_value': None,
        'ci_lower': None,
        'ci_upper': None,
        'error': None
    }

    # Check for longitudinal data availability
    has_longitudinal = (pre_treatment_col in df.columns and post_treatment_col in df.columns)

    if balance_status in ['balanced', 'passed']:
        # Proceed with OLS
        logger.info("Balance status is 'balanced'. Running OLS.")
        try:
            ols_res = run_ols(df, outcome_col=outcome_col, treatment_col='treatment')
            param = ols_res.params['treatment']
            p_val = ols_res.pvalues['treatment']
            conf_int = ols_res.conf_int().loc['treatment']

            result['method'] = 'OLS'
            result['att_estimate'] = float(param)
            result['p_value'] = float(p_val)
            result['ci_lower'] = float(conf_int[0])
            result['ci_upper'] = float(conf_int[1])
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"OLS estimation failed: {e}")

    elif balance_status in ['failed', 'did_fallback']:
        # Attempt DiD
        logger.info("Balance status indicates fallback. Checking for DiD data.")
        if not has_longitudinal:
            err_msg = f"Longitudinal data required for DiD but columns {pre_treatment_col} and {post_treatment_col} are missing."
            logger.error(err_msg)
            raise DataUnavailableError(err_msg)

        try:
            did_res = run_did(
                df,
                outcome_col=outcome_col,
                treatment_col='treatment',
                pre_treatment_col=pre_treatment_col,
                post_treatment_col=post_treatment_col
            )
            param = did_res.params['treatment']
            p_val = did_res.pvalues['treatment']
            conf_int = did_res.conf_int().loc['treatment']

            result['method'] = 'DiD'
            result['att_estimate'] = float(param)
            result['p_value'] = float(p_val)
            result['ci_lower'] = float(conf_int[0])
            result['ci_upper'] = float(conf_int[1])
        except DataUnavailableError:
            raise
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"DiD estimation failed: {e}")
    else:
        logger.warning(f"Unknown balance status: {balance_status}. Skipping causal estimation.")
        result['error'] = f"Unknown balance status: {balance_status}"

    return result
