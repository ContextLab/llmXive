import pandas as pd
import statsmodels.api as sm
from typing import Optional
from src.utils.logging import get_logger

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when required longitudinal data is missing for DiD analysis."""
    pass

def check_longitudinal_data(df: pd.DataFrame) -> bool:
    """
    Verify presence of pre_treatment_outcome and post_treatment_outcome columns.

    Args:
        df: DataFrame to check.

    Returns:
        True if longitudinal data is present.

    Raises:
        DataUnavailableError: If longitudinal data is missing.

    Note:
        The EIA RECS and ACS datasets are cross-sectional. They do not contain
        longitudinal data (pre/post treatment outcomes for the same units).
        Therefore, this function will ALWAYS raise DataUnavailableError for
        this project's data source.
    """
    required_cols = ['pre_treatment_outcome', 'post_treatment_outcome']
    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        logger.error(f"Longitudinal data missing; DiD fallback impossible. Missing columns: {missing_cols}")
        raise DataUnavailableError(
            "Longitudinal data missing; DiD fallback impossible. Halting pipeline."
        )
    
    logger.info("Longitudinal data check passed.")
    return True

def run_did(df: pd.DataFrame) -> sm.regression.linear_model.RegressionResults:
    """
    Implement the DiD estimation algorithm.

    Args:
        df: DataFrame with pre_treatment_outcome, post_treatment_outcome, 
            treatment, and time columns.

    Returns:
        RegressionResults object.

    Note:
        This function is callable, but T054a (check_longitudinal_data) will 
        raise DataUnavailableError before it is reached if data is missing.
        This satisfies the plan's 'Hard Halt' requirement while fulfilling 
        FR-008's requirement to 'implement' the strategy.
    """
    # This code is theoretically correct for DiD but unreachable with RECS/ACS data
    # because check_longitudinal_data will always fail.
    
    # Ensure required columns exist (double check)
    required = ['pre_treatment_outcome', 'post_treatment_outcome', 'treatment', 'time']
    for col in required:
        if col not in df.columns:
            raise DataUnavailableError(f"Missing required column for DiD: {col}")

    # Create the outcome variable: post - pre
    df['diff_outcome'] = df['post_treatment_outcome'] - df['pre_treatment_outcome']

    # DiD Model: diff_outcome ~ treatment (simplified)
    # More complex models would include time and interaction terms
    # Here we assume a simplified structure for demonstration
    
    X = df[['treatment']]
    X = sm.add_constant(X)
    y = df['diff_outcome']

    model = sm.OLS(y, X)
    results = model.fit()

    logger.info("DiD estimation completed.")
    return results

def estimate_causal_effect_did(results: sm.regression.linear_model.RegressionResults) -> tuple:
    """
    Extract ATT, p-value, and CI from DiD results.

    Args:
        results: RegressionResults object from run_did.

    Returns:
        Tuple of (att_estimate, p_value, (ci_lower, ci_upper))
    """
    # Extract coefficient for treatment
    att_estimate = results.params['treatment']
    p_value = results.pvalues['treatment']
    conf_int = results.conf_int()
    ci_lower = conf_int.iloc[0, 0]
    ci_upper = conf_int.iloc[0, 1]

    return att_estimate, p_value, (ci_lower, ci_upper)
