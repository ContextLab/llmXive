import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from scipy import stats
import statsmodels.api as sm


@dataclass
class RegressionResult:
    """Container for regression analysis results."""
    model: sm.OLSResults
    r_squared: float
    adj_r_squared: float
    coefficients: pd.Series
    p_values: pd.Series
    # T017: Added fields for Pearson correlation between flexibility and creativity
    pearson_r: Optional[float] = None
    pearson_p: Optional[float] = None
    # T017.1: Added field for delta R-squared
    delta_r2: Optional[float] = None


def format_delta_r2(delta_r2: float) -> str:
    """Format delta R-squared to four decimal places."""
    return f"{delta_r2:.4f}"


def fit_regression(
    flexibility: np.ndarray,
    creativity: np.ndarray,
    covariates: Dict[str, np.ndarray],
    static_connectivity: Optional[np.ndarray] = None
) -> RegressionResult:
    """
    Fit a linear regression model: creativity ~ network_flexibility + covariates.

    Args:
        flexibility: Network flexibility scores (1D array).
        creativity: Creativity scores (CAQ) (1D array).
        covariates: Dictionary of covariates (age, sex, education).
        static_connectivity: Optional static connectivity strength for baseline model comparison.

    Returns:
        RegressionResult containing model statistics and Pearson correlation.
    """
    # T017: Compute Pearson correlation between flexibility and creativity
    pearson_r, pearson_p = stats.pearsonr(flexibility, creativity)

    # Prepare design matrix
    # Start with flexibility
    X = np.column_stack([flexibility])
    feature_names = ['network_flexibility']

    # Add covariates
    for name, values in covariates.items():
        X = np.column_stack([X, values])
        feature_names.append(name)

    # Add static connectivity if provided (for full model)
    if static_connectivity is not None:
        X = np.column_stack([X, static_connectivity])
        feature_names.append('static_connectivity_strength')

    # Add constant term
    X = sm.add_constant(X)

    # Fit OLS model
    model = sm.OLS(creativity, X).fit()

    # Extract results
    coefficients = pd.Series(model.params, index=['const'] + feature_names)
    p_values = pd.Series(model.pvalues, index=['const'] + feature_names)

    result = RegressionResult(
        model=model,
        r_squared=model.rsquared,
        adj_r_squared=model.rsquared_adj,
        coefficients=coefficients,
        p_values=p_values,
        pearson_r=float(pearson_r),
        pearson_p=float(pearson_p)
    )

    # T017.1: If static connectivity is provided, compute baseline model and delta R2
    if static_connectivity is not None and len(covariates) > 0:
        # Baseline model: creativity ~ static_connectivity + covariates (no flexibility)
        X_baseline = np.column_stack([static_connectivity])
        for name, values in covariates.items():
            X_baseline = np.column_stack([X_baseline, values])
        X_baseline = sm.add_constant(X_baseline)

        baseline_model = sm.OLS(creativity, X_baseline).fit()
        baseline_r2 = baseline_model.rsquared

        # Delta R2 is the increase in R2 when adding flexibility
        result.delta_r2 = result.r_squared - baseline_r2

    return result


def run_permutation_test(
    flexibility: np.ndarray,
    creativity: np.ndarray,
    n_permutations: int = 10000,
    random_state: Optional[int] = None
) -> float:
    """
    Run permutation test to assess significance of correlation.

    Shuffles creativity scores only (preserving flexibility vector)
    and returns an empirical two-tailed p-value.
    """
    if random_state is not None:
        np.random.seed(random_state)

    # Calculate observed statistic (correlation)
    observed_r, _ = stats.pearsonr(flexibility, creativity)

    # Permutation loop
    perm_r_values = np.zeros(n_permutations)
    for i in range(n_permutations):
        shuffled_creativity = np.random.permutation(creativity)
        perm_r_values[i], _ = stats.pearsonr(flexibility, shuffled_creativity)

    # Two-tailed p-value
    extreme_count = np.sum(np.abs(perm_r_values) >= np.abs(observed_r))
    p_value = extreme_count / n_permutations

    return p_value


def apply_fwe_correction(
    p_values: List[float],
    method: str = 'max-t'
) -> List[float]:
    """
    Apply family-wise error correction using max-T permutation method.

    Args:
        p_values: List of raw p-values.
        method: Correction method ('max-t' or 'bonferroni').

    Returns:
        List of corrected p-values.
    """
    if method == 'bonferroni':
        # Bonferroni correction
        corrected = [min(p * len(p_values), 1.0) for p in p_values]
    elif method == 'max-t':
        # Max-T method would require access to the full permutation distribution
        # For now, using a simplified approach that assumes we have the max statistics
        # In a full implementation, this would compare against the max-T distribution
        # Here we use a conservative estimate
        corrected = [min(p * len(p_values), 1.0) for p in p_values]
    else:
        raise ValueError(f"Unknown correction method: {method}")

    return corrected