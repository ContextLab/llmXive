"""
Causal effect estimation module.
Implements OLS regression with cluster-robust standard errors and Difference-in-Differences (DiD).
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from typing import Optional, Dict, Any, Tuple
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DataUnavailableError(Exception):
    """Raised when required data for DiD is missing."""
    pass


def run_ols(df: pd.DataFrame, cluster_col: str = "pair_id") -> sm.regression.linear_model.RegressionResults:
    """
    Run OLS regression with cluster-robust standard errors.
    
    Primary outcome: log(energy_cost)
    Treatment variable: 'treatment' (binary)
    Covariates: income, housing_type, location (if present)
    
    Args:
        df: Preprocessed DataFrame with treatment, outcome, and covariates.
            Must contain 'treatment', 'energy_cost', and 'pair_id' columns.
        cluster_col: Column name for clustering standard errors (default: 'pair_id').
                    
    Returns:
        statsmodels RegressionResults object with cluster-robust standard errors.
                    
    Raises:
        ValueError: If required columns are missing or data is insufficient.
    """
    logger.info("Starting OLS regression with cluster-robust standard errors")
    
    # Validate required columns
    required_cols = ['treatment', 'energy_cost', cluster_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for OLS: {missing_cols}")
    
    # Filter out rows with missing outcome or treatment
    clean_df = df.dropna(subset=['treatment', 'energy_cost', cluster_col])
    
    if len(clean_df) < 10:
        raise ValueError(f"Insufficient data for OLS: only {len(clean_df)} rows after cleaning")
    
    # Log-transform outcome
    clean_df = clean_df.copy()
    clean_df['log_energy_cost'] = np.log(clean_df['energy_cost'])
    
    # Define covariates (include common ones if present)
    covariate_candidates = ['income', 'housing_type', 'location', 'home_value', 'household_size']
    covariates = [col for col in covariate_candidates if col in clean_df.columns]
    
    # Build feature matrix
    X = clean_df[['treatment'] + covariates]
    y = clean_df['log_energy_cost']
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit OLS model
    model = sm.OLS(y, X)
    results = model.fit(cov_type='cluster', cov_kwds={'groups': clean_df[cluster_col]})
    
    logger.info(f"OLS regression complete. Treatment coefficient: {results.params['treatment']:.4f}")
    logger.info(f"p-value: {results.pvalues['treatment']:.4f}")
    
    return results


def run_did(df: pd.DataFrame) -> sm.regression.linear_model.RegressionResults:
    """
    Run Difference-in-Differences (DiD) regression.
    
    Requires longitudinal data with pre/post treatment outcomes.
    
    Args:
        df: DataFrame with columns:
            - 'treatment': binary treatment indicator
            - 'time': binary time indicator (0=pre, 1=post)
            - 'outcome': outcome variable
            - 'id': unique identifier for clustering
                    
    Returns:
        statsmodels RegressionResults object.
                    
    Raises:
        DataUnavailableError: If required longitudinal columns are missing.
        ValueError: If data is insufficient.
    """
    logger.info("Starting DiD regression")
    
    # Validate required columns for DiD
    required_cols = ['treatment', 'time', 'outcome', 'id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise DataUnavailableError(
            f"Longitudinal data required for DiD but columns missing: {missing_cols}"
        )
    
    # Filter out rows with missing data
    clean_df = df.dropna(subset=['treatment', 'time', 'outcome', 'id'])
    
    if len(clean_df) < 20:
        raise ValueError(f"Insufficient data for DiD: only {len(clean_df)} rows after cleaning")
    
    # Create interaction term (treatment * time)
    clean_df = clean_df.copy()
    clean_df['did_interaction'] = clean_df['treatment'] * clean_df['time']
    
    # Build feature matrix
    X = clean_df[['treatment', 'time', 'did_interaction']]
    y = clean_df['outcome']
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit OLS model with clustering
    model = sm.OLS(y, X)
    results = model.fit(cov_type='cluster', cov_kwds={'groups': clean_df['id']})
    
    logger.info(f"DiD regression complete. Interaction coefficient: {results.params['did_interaction']:.4f}")
    logger.info(f"p-value: {results.pvalues['did_interaction']:.4f}")
    
    return results


def estimate_causal_effect(
    df: pd.DataFrame,
    method: str = "ols",
    cluster_col: str = "pair_id"
) -> Dict[str, Any]:
    """
    Estimate causal effect using specified method.
    
    Args:
        df: Preprocessed DataFrame with treatment and outcome variables.
        method: Estimation method ('ols' or 'did').
        cluster_col: Column name for clustering standard errors (for OLS).
                    
    Returns:
        Dictionary containing:
            - 'estimate': causal effect estimate
            - 'std_error': standard error
            - 'p_value': p-value for the treatment effect
            - 'ci_lower': lower bound of 95% confidence interval
            - 'ci_upper': upper bound of 95% confidence interval
            - 'method': estimation method used
            - 'n_observations': number of observations used
    """
    if method == "ols":
        results = run_ols(df, cluster_col=cluster_col)
        treatment_idx = results.params.index.get_loc('treatment')
        estimate = results.params['treatment']
        std_error = results.bse['treatment']
        p_value = results.pvalues['treatment']
        ci = results.conf_int(alpha=0.05).iloc[treatment_idx]
        
    elif method == "did":
        results = run_did(df)
        treatment_idx = results.params.index.get_loc('did_interaction')
        estimate = results.params['did_interaction']
        std_error = results.bse['did_interaction']
        p_value = results.pvalues['did_interaction']
        ci = results.conf_int(alpha=0.05).iloc[treatment_idx]
        
    else:
        raise ValueError(f"Unknown method: {method}. Use 'ols' or 'did'.")
    
    return {
        'estimate': float(estimate),
        'std_error': float(std_error),
        'p_value': float(p_value),
        'ci_lower': float(ci[0]),
        'ci_upper': float(ci[1]),
        'method': method,
        'n_observations': len(df)
    }