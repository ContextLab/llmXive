"""
Estimators module for hypothesis testing methods.
"""

import warnings
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.contrast import ContrastResults
from statsmodels.regression.linear_model import OLS

def run_naive_ttest(data: pd.DataFrame, treatment_col: str, outcome_col: str) -> float:
    """
    Run naive independent samples t-test.

    WARNING: This method assumes independence between observations and
    is NOT appropriate for clustered data. Use only for baseline comparison.

    Args:
        data: DataFrame with treatment and outcome columns
        treatment_col: Name of treatment column
        outcome_col: Name of outcome column

    Returns:
        float: Two-sided p-value from t-test
    """
    treatment_groups = data.groupby(treatment_col)[outcome_col]
    group_0 = treatment_groups.get_group(0)
    group_1 = treatment_groups.get_group(1)

    _, p_value = stats.ttest_ind(group_0, group_1)
    return p_value

def run_naive_ttest_with_warning(data: pd.DataFrame, treatment_col: str, outcome_col: str) -> float:
    """
    Run naive t-test with explicit warning about independence assumption.

    This wrapper ensures users are aware that this method violates
    cluster-aware inference principles and is intended only for baseline comparison.

    Args:
        data: DataFrame with treatment and outcome columns
        treatment_col: Name of treatment column
        outcome_col: Name of outcome column

    Returns:
        float: Two-sided p-value from t-test
    """
    warnings.warn(
        "Using naive t-test which assumes independence between observations. "
        "This method is intended only for baseline comparison and will likely "
        "produce inflated Type I error rates for clustered data.",
        UserWarning,
        stacklevel=2
    )
    return run_naive_ttest(data, treatment_col, outcome_col)

def run_cluster_robust_ttest(
    data: pd.DataFrame,
    treatment_col: str,
    outcome_col: str,
    cluster_id_col: str
) -> float:
    """
    Run t-test with cluster-robust standard errors (CR2 adjustment).

    This is the constitutionally compliant method that properly accounts
    for intra-cluster correlation.

    Args:
        data: DataFrame with treatment, outcome, and cluster_id columns
        treatment_col: Name of treatment column
        outcome_col: Name of outcome column
        cluster_id_col: Name of cluster_id column

    Returns:
        float: Two-sided p-value from cluster-robust t-test
    """
    # Prepare design matrix
    # Create treatment dummy variable (1 if treated, 0 otherwise)
    X = pd.get_dummies(data[treatment_col], drop_first=True)
    # Ensure column name is consistent (usually '1' after get_dummies)
    treatment_col_name = X.columns[0]
    
    # Add intercept
    X = pd.concat([pd.Series([1] * len(data), name='intercept'), X], axis=1)
    y = data[outcome_col]

    # Fit OLS model with cluster-robust covariance (CR2 adjustment)
    # statsmodels 0.14.1 supports 'cluster' with 'use_t=True' for small sample correction
    # We use the 'HC1' style for robustness but grouped by cluster
    model = OLS(y, X).fit(
        cov_type='cluster',
        cov_kwds={'groups': data[cluster_id_col]}
    )

    # Get the t-statistic for the treatment coefficient
    # The treatment coefficient is at index 1 (after intercept)
    t_stat = model.tvalues[1]
    
    # Degrees of freedom for cluster-robust inference
    # Use the number of clusters - 1 as the df for the t-distribution
    n_clusters = data[cluster_id_col].nunique()
    df = n_clusters - 1

    # Calculate two-sided p-value
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))

    return p_value

def run_block_permutation(
    data: pd.DataFrame,
    treatment_col: str,
    outcome_col: str,
    cluster_id_col: str,
    n_permutations: int = 1000
) -> float:
    """
    Run block permutation test at the cluster level.

    This method permutes treatment assignments at the cluster level,
    preserving the correlation structure within clusters.

    Args:
        data: DataFrame with treatment, outcome, and cluster_id columns
        treatment_col: Name of treatment column
        outcome_col: Name of outcome column
        cluster_id_col: Name of cluster_id column
        n_permutations: Number of permutations to perform

    Returns:
        float: Two-sided p-value from permutation test
    """
    # Calculate observed test statistic
    treatment_groups = data.groupby(treatment_col)[outcome_col]
    group_0 = treatment_groups.get_group(0)
    group_1 = treatment_groups.get_group(1)
    observed_stat = np.mean(group_1) - np.mean(group_0)

    # Get unique clusters and their treatment assignments
    clusters = data[cluster_id_col].unique()
    cluster_treatments = data.groupby(cluster_id_col)[treatment_col].first().values

    # Perform permutations
    permuted_stats = []
    for _ in range(n_permutations):
        # Permute treatment assignments at cluster level
        permuted_treatments = np.random.permutation(cluster_treatments)

        # Create permuted dataset
        perm_data = data.copy()
        perm_data[treatment_col + '_perm'] = 0
        for i, cluster in enumerate(clusters):
            mask = perm_data[cluster_id_col] == cluster
            perm_data.loc[mask, treatment_col + '_perm'] = permuted_treatments[i]

        # Calculate test statistic for permuted data
        perm_groups = perm_data.groupby(treatment_col + '_perm')[outcome_col]
        if 0 in perm_groups.groups and 1 in perm_groups.groups:
            g0 = perm_groups.get_group(0)
            g1 = perm_groups.get_group(1)
            perm_stat = np.mean(g1) - np.mean(g0)
            permuted_stats.append(perm_stat)

    # Calculate p-value
    permuted_stats = np.array(permuted_stats)
    extreme_count = np.sum(np.abs(permuted_stats) >= abs(observed_stat))
    p_value = (extreme_count + 1) / (n_permutations + 1)

    return p_value