"""
Statistical analysis utilities for GateMem benchmarking.

This module provides functions for statistical testing, including
Linear Mixed-Effects Models (LMM), Fixed-Effects GLM, domain-stratified analysis,
and post-hoc tests.
"""

import logging
from typing import Dict, Any, List, Union, Tuple, Optional

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families

logger = logging.getLogger(__name__)


def fit_lmm(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    score_col: str = 'score',
    method_col: str = 'method',
    domain_col: str = 'domain',
    subject_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fit a Linear Mixed-Effects Model (LMM) as the primary statistical method.

    Formula: score ~ method + (1|Domain)

    Args:
        data: Input data as DataFrame or list of dicts.
        score_col: Name of the score column.
        method_col: Name of the method column (fixed effect).
        domain_col: Name of the domain column (random effect grouping).
        subject_col: Optional subject ID column if available.

    Returns:
        Dict with keys:
            - 'method_used': 'LMM'
            - 'p_value': float (p-value for method effect)
            - 'test_statistic': float (t-statistic for method effect)
            - 'coefficients': Dict of model coefficients
            - 'random_effects_variance': Variance of random effects
            - 'converged': bool
            - 'fallback_reason': None (primary method)

    Raises:
        ValueError: If data is insufficient or invalid.
        RuntimeError: If model fitting fails with unrecoverable error.
    """
    logger.info("Fitting Linear Mixed-Effects Model (LMM)...")

    # Convert to DataFrame if needed
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    # Validate required columns
    required_cols = [score_col, method_col, domain_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in LMM input: {missing}")

    # Ensure method is categorical
    df[method_col] = df[method_col].astype('category')

    # Check for sufficient data
    n_obs = len(df)
    n_groups = df[domain_col].nunique()
    n_methods = df[method_col].nunique()

    if n_obs < 10:
        raise ValueError(f"Insufficient observations for LMM: {n_obs}")
    if n_groups < 2:
        raise ValueError(f"Insufficient groups (domains) for LMM: {n_groups}")
    if n_methods < 2:
        raise ValueError(f"Insufficient methods for comparison: {n_methods}")

    try:
        # Prepare formula: score ~ method + (1|domain)
        # statsmodels MixedLM uses 'groups' for random effect grouping
        endog = df[score_col].values
        exog = sm.add_constant(pd.get_dummies(df[method_col], drop_first=True))
        groups = df[domain_col]

        # Fit the model
        model = MixedLM(endog=endog, exog=exog, groups=groups)
        result = model.fit(reml=False, full_output=True)

        # Check convergence
        converged = result.converged
        if not converged:
            logger.warning("LMM did not converge. Results may be unreliable.")

        # Extract results
        # Get p-values for fixed effects (method coefficients)
        # The first column after intercept is the method effect (drop_first=True)
        if len(result.pvalues) > 1:
            # Assuming first non-intercept is the method effect we care about
            method_pvalue = result.pvalues.iloc[1] if len(result.pvalues) > 1 else result.pvalues.iloc[0]
            method_tstat = result.tvalues.iloc[1] if len(result.tvalues) > 1 else result.tvalues.iloc[0]
        else:
            method_pvalue = result.pvalues.iloc[0]
            method_tstat = result.tvalues.iloc[0]

        # Extract coefficients
        coefficients = dict(zip(result.params.index, result.params.values))

        # Extract random effects variance
        random_var = result.cov_re.values[0][0] if result.cov_re is not None else 0.0

        logger.info(f"LMM fitted successfully. P-value: {method_pvalue:.4f}, T-stat: {method_tstat:.4f}")

        return {
            'method_used': 'LMM',
            'p_value': float(method_pvalue),
            'test_statistic': float(method_tstat),
            'coefficients': {k: float(v) for k, v in coefficients.items()},
            'random_effects_variance': float(random_var),
            'converged': bool(converged),
            'fallback_reason': None,
            'degrees_of_freedom': float(result.df_resid)
        }

    except np.linalg.LinAlgError as e:
        logger.error(f"Singular matrix error in LMM: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to fit LMM: {e}")
        raise RuntimeError(f"LMM fitting failed: {e}") from e


def fit_fixed_effects_glm(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    score_col: str = 'score',
    method_col: str = 'method',
    domain_col: str = 'domain'
) -> Dict[str, Any]:
    """
    Fit a Fixed-Effects Logistic Regression (GLM) as the tertiary statistical method.

    Formula: score ~ method + C(Domain)

    Args:
        data: Input data.
        score_col: Name of the score column.
        method_col: Name of the method column.
        domain_col: Name of the domain column (fixed effect covariate).

    Returns:
        Dict with GLM results.
    """
    logger.info("Fitting Fixed-Effects GLM (tertiary method)...")

    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    required_cols = [score_col, method_col, domain_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in GLM input: {missing}")

    # Create formula with domain as fixed effect
    formula = f"{score_col} ~ {method_col} + C({domain_col})"

    try:
        model = GLM.from_formula(
            formula,
            data=df,
            family=families.Gaussian()
        )
        result = model.fit()

        # Extract method coefficient (assuming it's the first non-intercept)
        params = result.params
        pvalues = result.pvalues

        # Find the method coefficient
        method_coeff_name = None
        for name in params.index:
            if method_col in name or name.startswith(method_col):
                method_coeff_name = name
                break

        if method_coeff_name is None:
            # Fallback: take first non-intercept
            non_intercept = [p for p in params.index if p != 'Intercept']
            if non_intercept:
                method_coeff_name = non_intercept[0]
            else:
                raise ValueError("Could not identify method coefficient in GLM")

        return {
            'method_used': 'GLM',
            'p_value': float(pvalues[method_coeff_name]),
            'test_statistic': float(result.tvalues[method_coeff_name]),
            'coefficients': {k: float(v) for k, v in params.items()},
            'converged': True,
            'fallback_reason': 'LMM and Stratified Analysis failed',
            'degrees_of_freedom': float(result.df_resid)
        }

    except Exception as e:
        logger.error(f"Failed to fit GLM: {e}")
        raise


def domain_stratified_analysis(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    score_col: str = 'score',
    method_col: str = 'method',
    domain_col: str = 'domain'
) -> Dict[str, Any]:
    """
    Implement domain-stratified analysis with aggregation (average p-values).

    This is the primary fallback if LMM is infeasible.

    Args:
        data: Input data.
        score_col: Name of the score column.
        method_col: Name of the method column.
        domain_col: Name of the domain column.

    Returns:
        Dict with stratified analysis results.
    """
    logger.info("Running domain-stratified analysis (primary fallback)...")

    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    required_cols = [score_col, method_col, domain_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in stratified analysis: {missing}")

    domains = df[domain_col].unique()
    p_values = []
    t_stats = []

    for domain in domains:
        domain_data = df[df[domain_col] == domain]
        if len(domain_data) < 4:
            logger.warning(f"Insufficient data for domain {domain}, skipping.")
            continue

        # Separate by method
        methods = domain_data[method_col].unique()
        if len(methods) < 2:
            continue

        # Assume two methods for paired test
        method1, method2 = methods[0], methods[1]
        scores1 = domain_data[domain_data[method_col] == method1][score_col]
        scores2 = domain_data[domain_data[method_col] == method2][score_col]

        if len(scores1) < 3 or len(scores2) < 3:
            continue

        # Perform t-test for this domain
        try:
            t_stat, p_val = stats.ttest_ind(scores1, scores2, equal_var=False)
            p_values.append(p_val)
            t_stats.append(t_stat)
        except Exception as e:
            logger.warning(f"Test failed for domain {domain}: {e}")
            continue

    if not p_values:
        raise ValueError("No valid domain tests could be performed.")

    # Aggregate: average p-values (Fisher's method could be used, but task specifies average)
    avg_p = float(np.mean(p_values))
    avg_t = float(np.mean(t_stats))

    logger.info(f"Stratified analysis complete. Average p-value: {avg_p:.4f}")

    return {
        'method_used': 'Stratified',
        'p_value': avg_p,
        'test_statistic': avg_t,
        'domain_p_values': p_values,
        'n_domains': len(p_values),
        'converged': True,
        'fallback_reason': 'LMM infeasible (singular matrix or insufficient data)',
        'degrees_of_freedom': float(sum(len(df[df[domain_col] == d][score_col]) - 2 for d in domains if len(df[df[domain_col] == d][score_col]) >= 2))
    }


def shapiro_wilk_test(differences: np.ndarray) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk normality test on paired score differences.

    Args:
        differences: Array of paired differences.

    Returns:
        Dict with normality test results.
    """
    if len(differences) < 3:
        raise ValueError("Insufficient data for Shapiro-Wilk test (need >= 3).")

    stat, p_value = stats.shapiro(differences)

    return {
        'test': 'Shapiro-Wilk',
        'statistic': float(stat),
        'p_value': float(p_value),
        'is_normal': bool(p_value > 0.05),
        'alpha': 0.05
    }


def run_post_hoc(differences: np.ndarray, is_normal: bool) -> Dict[str, Any]:
    """
    Run post-hoc test based on normality result.

    Args:
        differences: Array of paired differences.
        is_normal: Result from Shapiro-Wilk test.

    Returns:
        Dict with post-hoc test results.
    """
    if is_normal:
        # Paired t-test
        # Assuming differences are already calculated (method1 - method2)
        # We test if mean difference is significantly different from 0
        t_stat, p_value = stats.ttest_1samp(differences, 0.0)
        test_name = 'Paired t-test'
    else:
        # Wilcoxon signed-rank test
        stat, p_value = stats.wilcoxon(differences)
        test_name = 'Wilcoxon signed-rank'

    return {
        'test': test_name,
        'p_value': float(p_value),
        'test_statistic': float(stat),
        'assumption': 'normal' if is_normal else 'non-normal'
    }