"""
Balance validation and placebo testing module.
Implements SMD calculation, love plots, and placebo tests for causal inference.
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple
import warnings

from src.utils.logging import get_logger

logger = get_logger(__name__)


def calculate_smd(df: pd.DataFrame, treatment_col: str = 'treatment') -> Dict[str, float]:
    """
    Calculate the Standardized Mean Difference (SMD) for all covariates.

    Args:
        df: DataFrame with treatment indicator and covariates.
        treatment_col: Name of the treatment column.

    Returns:
        Dictionary mapping column names to their SMD values.
    """
    if treatment_col not in df.columns:
        raise ValueError(f"Column '{treatment_col}' not found in data.")

    treat_mask = df[treatment_col] == 1
    ctrl_mask = df[treatment_col] == 0

    if treat_mask.sum() == 0 or ctrl_mask.sum() == 0:
        raise ValueError("Both treatment and control groups must be present.")

    smd_results = {}

    for col in df.columns:
        if col == treatment_col:
            continue

        if not np.issubdtype(df[col].dtype, np.number):
            # Skip non-numeric columns for SMD
            continue

        mean_t = df.loc[treat_mask, col].mean()
        mean_c = df.loc[ctrl_mask, col].mean()
        std_t = df.loc[treat_mask, col].std()
        std_c = df.loc[ctrl_mask, col].std()

        # Pooled standard deviation
        n_t = treat_mask.sum()
        n_c = ctrl_mask.sum()
        pooled_std = np.sqrt(((n_t - 1) * std_t**2 + (n_c - 1) * std_c**2) / (n_t + n_c - 2))

        if pooled_std == 0:
            smd = 0.0
        else:
            smd = (mean_t - mean_c) / pooled_std

        smd_results[col] = smd

    return smd_results


def plot_balance(smd_data: Dict[str, float], threshold: float = 0.1) -> plt.Figure:
    """
    Generate a 'Love Plot' visualizing SMD before and after matching.

    Args:
        smd_data: Dictionary of SMD values.
        threshold: Balance threshold (default 0.1).

    Returns:
        Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    variables = list(smd_data.keys())
    smd_values = [smd_data[v] for v in variables]

    ax.scatter(smd_values, range(len(variables)), label='SMD', alpha=0.7)
    ax.axvline(x=threshold, color='red', linestyle='--', label=f'Threshold ({threshold})')
    ax.axvline(x=-threshold, color='red', linestyle='--')
    ax.axvline(x=0, color='black', linestyle='-')

    ax.set_yticks(range(len(variables)))
    ax.set_yticklabels(variables)
    ax.set_xlabel('Standardized Mean Difference (SMD)')
    ax.set_title('Covariate Balance Plot')
    ax.legend()
    ax.grid(axis='x', alpha=0.3)

    return fig


def run_placebo_test(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str = 'treatment',
    alpha: float = 0.05
) -> Dict[str, any]:
    """
    Perform a placebo test on a pre-treatment outcome.

    This tests whether the treatment and control groups differ significantly
    on an outcome that should NOT be affected by the treatment (pre-treatment).
    A significant result suggests violation of the parallel trends assumption.

    Args:
        df: DataFrame with treatment, outcome, and covariates.
        outcome_col: Name of the pre-treatment outcome column.
        treatment_col: Name of the treatment column.
        alpha: Significance level.

    Returns:
        Dictionary with test statistics, p-value, and significance flag.
    """
    if outcome_col not in df.columns:
        raise ValueError(f"Outcome column '{outcome_col}' not found.")
    if treatment_col not in df.columns:
        raise ValueError(f"Treatment column '{treatment_col}' not found.")

    treat_mask = df[treatment_col] == 1
    ctrl_mask = df[treatment_col] == 0

    y_t = df.loc[treat_mask, outcome_col]
    y_c = df.loc[ctrl_mask, outcome_col]

    if len(y_t) < 2 or len(y_c) < 2:
        return {
            'valid': False,
            'error': 'Insufficient sample size for t-test',
            'p_value': None,
            'is_significant': None
        }

    # Perform Welch's t-test (unequal variances)
    stat, p_value = sm.stats.ttest_ind(y_t, y_c, equal_var=False)

    is_significant = p_value < alpha

    return {
        'valid': True,
        'p_value': float(p_value),
        'statistic': float(stat),
        'is_significant': bool(is_significant),
        'n_treatment': len(y_t),
        'n_control': len(y_c)
    }


def validate_placebo_results(results: Dict[str, any]) -> bool:
    """
    Validate that placebo test results are well-formed.

    Args:
        results: Output from run_placebo_test.

    Returns:
        True if results are valid, False otherwise.
    """
    if not results.get('valid', False):
        return False
    if results.get('p_value') is None:
        return False
    return True


def generate_placebo_report(results: Dict[str, any], alpha: float = 0.05) -> str:
    """
    Generate a human-readable report for the placebo test.

    Args:
        results: Output from run_placebo_test.
        alpha: Significance level used.

    Returns:
        String report.
    """
    if not results.get('valid'):
        return f"Placebo test failed to execute: {results.get('error', 'Unknown error')}"

    p_val = results['p_value']
    sig = results['is_significant']

    status = "FAILED" if sig else "PASSED"
    interpretation = (
        "Significant difference detected in pre-treatment outcome. "
        "Parallel trends assumption may be violated."
    ) if sig else (
        "No significant difference in pre-treatment outcome. "
        "Parallel trends assumption holds."
    )

    return (
        f"Placebo Test Report\n"
        f"-------------------\n"
        f"Status: {status}\n"
        f"P-value: {p_val:.4f}\n"
        f"Alpha: {alpha}\n"
        f"Interpretation: {interpretation}\n"
        f"N Treatment: {results.get('n_treatment')}\n"
        f"N Control: {results.get('n_control')}"
    )


def check_placebo_significance(
    df: pd.DataFrame,
    outcome_col: str,
    alpha: float = 0.05
) -> bool:
    """
    Check if the placebo test is significant (i.e., fails the assumption).

    Args:
        df: Data.
        outcome_col: Pre-treatment outcome.
        alpha: Significance level.

    Returns:
        True if significant (FAIL), False if not significant (PASS).
    """
    results = run_placebo_test(df, outcome_col, alpha=alpha)
    if not results.get('valid'):
        raise ValueError("Placebo test could not be executed.")
    return results['is_significant']


def iterative_matching_with_placebo(
    df: pd.DataFrame,
    covariates: List[str],
    outcome_col: str,
    caliper_start: float = 0.2,
    max_iter: int = 10,
    alpha: float = 0.05
) -> Tuple[pd.DataFrame, Dict[str, any]]:
    """
    Perform iterative matching and placebo testing until balance is achieved.

    This function attempts to find a caliper that balances covariates AND
    passes the placebo test.

    Args:
        df: Input data.
        covariates: List of covariates for matching.
        outcome_col: Pre-treatment outcome for placebo test.
        caliper_start: Starting caliper width.
        max_iter: Maximum iterations.
        alpha: Significance level for placebo test.

    Returns:
        Tuple of (matched_data, report_dict)
    """
    from src.analysis.psm import iterative_matching

    current_caliper = caliper_start
    report = {
        'iterations': 0,
        'final_caliper': None,
        'placebo_passed': False,
        'smd_results': {}
    }

    for i in range(max_iter):
        report['iterations'] = i + 1

        # Run matching
        matched = iterative_matching(df, covariates, caliper=current_caliper)

        if matched is None or matched.empty:
            logger.warning(f"Iteration {i+1}: No matches found with caliper {current_caliper}.")
            current_caliper *= 0.9
            continue

        # Run placebo test
        try:
            sig = check_placebo_significance(matched, outcome_col, alpha=alpha)
            if not sig:
                # Passed!
                report['placebo_passed'] = True
                report['final_caliper'] = current_caliper
                report['smd_results'] = calculate_smd(matched)
                return matched, report
            else:
                logger.info(f"Iteration {i+1}: Placebo test failed (p < {alpha}). Reducing caliper.")
                current_caliper *= 0.9
        except ValueError as e:
            logger.warning(f"Iteration {i+1}: Placebo test error: {e}. Adjusting caliper.")
            current_caliper *= 0.9

    report['placebo_passed'] = False
    report['final_caliper'] = current_caliper
    logger.error("Max iterations reached without passing placebo test.")
    return matched, report
