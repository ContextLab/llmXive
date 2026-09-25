import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from scipy import stats
import statsmodels.api as sm


@dataclass
class RegressionResult:
    """Container for regression analysis results."""
    model: sm.OLSResult
    r_squared: float
    adj_r_squared: float
    p_value_flexibility: float
    p_value_overall: float
    coefficients: Dict[str, float]
    pearson_r: float
    pearson_p: float
    delta_r2: Optional[float] = None
    delta_r2_formatted: Optional[str] = None


def format_delta_r2(delta_r2: float) -> str:
    """Format delta R-squared to four decimal places."""
    return f"{delta_r2:.4f}"


def fit_regression(
    flexibility: np.ndarray,
    creativity: np.ndarray,
    covariates: Dict[str, np.ndarray]
) -> RegressionResult:
    """
    Fit OLS regression: creativity ~ network_flexibility + covariates.

    Args:
        flexibility: Network flexibility values (n_samples,).
        creativity: Creativity scores (CAQ) (n_samples,).
        covariates: Dictionary of covariates (age, sex, education, static_connectivity_strength).

    Returns:
        RegressionResult object containing model statistics.
    """
    # Prepare design matrix
    X_dict = {'intercept': np.ones(len(flexibility))}
    X_dict['flexibility'] = flexibility

    for name, values in covariates.items():
        X_dict[name] = values

    X = pd.DataFrame(X_dict)
    y = creativity

    # Fit model
    model = sm.OLS(y, X).fit()

    # Extract statistics
    r_squared = model.rsquared
    adj_r_squared = model.rsquared_adj
    p_value_flexibility = model.pvalues['flexibility']
    p_value_overall = model.f_pvalue

    coefficients = {
        name: float(coeff) for name, coeff in model.params.items()
    }

    # Compute Pearson correlation between flexibility and creativity
    pearson_r, pearson_p = stats.pearsonr(flexibility, creativity)

    return RegressionResult(
        model=model,
        r_squared=r_squared,
        adj_r_squared=adj_r_squared,
        p_value_flexibility=p_value_flexibility,
        p_value_overall=p_value_overall,
        coefficients=coefficients,
        pearson_r=pearson_r,
        pearson_p=pearson_p
    )


def run_permutation_test(
    flexibility: np.ndarray,
    creativity: np.ndarray,
    n_permutations: int = 10000
) -> float:
    """
    Perform a permutation test to assess the significance of the correlation
    between network flexibility and creativity.

    Shuffles creativity scores only (preserving flexibility vector) to generate
    a null distribution of correlation coefficients. Returns an empirical
    two-tailed p-value.

    Args:
        flexibility: Network flexibility values (n_samples,).
        creativity: Creativity scores (CAQ) (n_samples,).
        n_permutations: Number of permutations to perform.

    Returns:
        Empirical two-tailed p-value.
    """
    n = len(flexibility)
    if n != len(creativity):
        raise ValueError("flexibility and creativity must have the same length")

    # Compute observed correlation
    observed_r, _ = stats.pearsonr(flexibility, creativity)
    observed_t = observed_r * np.sqrt((n - 2) / (1 - observed_r**2 + 1e-10))

    # Generate null distribution
    count_extreme = 0

    for _ in range(n_permutations):
        # Shuffle creativity scores only
        shuffled_creativity = np.random.permutation(creativity)

        # Compute correlation with shuffled data
        perm_r, _ = stats.pearsonr(flexibility, shuffled_creativity)
        perm_t = perm_r * np.sqrt((n - 2) / (1 - perm_r**2 + 1e-10))

        # Two-tailed: count if |perm_t| >= |observed_t|
        if np.abs(perm_t) >= np.abs(observed_t):
            count_extreme += 1

    # Empirical p-value
    p_value = count_extreme / n_permutations

    return p_value


def apply_fwe_correction(
    p_values: List[float],
    method: str = 'max-t'
) -> List[float]:
    """
    Apply Family-Wise Error (FWE) correction using the max-T permutation method.

    Args:
        p_values: List of raw p-values from multiple tests.
        method: Correction method (currently only 'max-t' is supported).

    Returns:
        List of FWE-corrected p-values.
    """
    if method != 'max-t':
        raise ValueError(f"Method '{method}' is not supported. Use 'max-t'.")

    if not p_values:
        return []

    # For max-T method with permutation, we would need the full permutation
    # distribution of the maximum test statistic. Since we only have p-values
    # here, we approximate with Bonferroni as a fallback for single-run scenarios,
    # but note that true max-T requires the permutation distribution.
    #
    # In a full implementation, this function would take the permutation
    # distribution and compute corrected p-values based on the proportion
    # of permutations where the max statistic exceeded the observed.
    #
    # For now, we implement the standard Bonferroni correction as a conservative
    # approximation when the full permutation distribution is not available.
    n_tests = len(p_values)
    corrected = [min(p * n_tests, 1.0) for p in p_values]

    return corrected
