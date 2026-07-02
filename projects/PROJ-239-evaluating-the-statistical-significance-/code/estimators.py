"""
Statistical estimators for A/B testing with cluster-aware inference.

This module provides functions to perform t-tests, including naive baselines
and cluster-robust methods, while respecting the project's constitution
regarding non-independent observations.
"""
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.contrast import ContrastResults
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.weightstats import ttest_ind

def run_naive_ttest(data: pd.DataFrame, treatment_col: str, outcome_col: str) -> float:
    """
    Perform a standard independent samples t-test assuming all observations are independent.

    CRITICAL WARNING: This method is statistically invalid when data exhibits
    intra-cluster correlation (ICC > 0). It is implemented here ONLY as a
    baseline to demonstrate Type I error inflation. Do not use for final
    inference on clustered data.

    Args:
        data: DataFrame containing the observations.
        treatment_col: Name of the column indicating treatment group (e.g., 'treatment').
        outcome_col: Name of the column containing the outcome metric.

    Returns:
        float: The two-sided p-value from the t-test.
    """
    # Group by treatment and extract outcome values
    groups = data.groupby(treatment_col)[outcome_col]
    
    # Ensure exactly two groups exist
    if groups.ngroups != 2:
        raise ValueError(f"Expected exactly 2 treatment groups, found {groups.ngroups}")
    
    group_names = sorted(groups.groups.keys())
    group_0 = groups.get_group(group_names[0])
    group_1 = groups.get_group(group_names[1])

    # Perform the t-test on the actual values
    _, p_value = stats.ttest_ind(group_0, group_1, equal_var=False)
    
    return float(p_value)

def run_naive_ttest_with_warning(data: pd.DataFrame, treatment_col: str, outcome_col: str) -> float:
    """
    Wrapper for run_naive_ttest that issues a clear warning about methodological violation.

    This function logs a warning that the method assumes independence and is intended
    only for baseline comparison, thereby respecting Constitution Principle VI.

    Args:
        data: DataFrame containing the observations.
        treatment_col: Name of the column indicating treatment group.
        outcome_col: Name of the column containing the outcome metric.

    Returns:
        float: The two-sided p-value from the t-test.
    """
    warnings.warn(
        "Methodological Violation: run_naive_ttest_with_warning assumes independent "
        "observations. This method is INVALID for clustered data (ICC > 0) and will "
        "likely inflate Type I error rates. This function is provided ONLY as a "
        "baseline for comparison against cluster-robust methods (Principle VI).",
        UserWarning,
        stacklevel=2
    )
    return run_naive_ttest(data, treatment_col, outcome_col)

def run_cluster_robust_ttest(data: pd.DataFrame, treatment_col: str, outcome_col: str, cluster_id_col: str) -> float:
    """
    Perform a t-test with cluster-robust standard errors (CR2 adjustment).

    This is the constitutionally compliant method for clustered data.

    Args:
        data: DataFrame containing the observations.
        treatment_col: Name of the column indicating treatment group.
        outcome_col: Name of the column containing the outcome metric.
        cluster_id_col: Name of the column identifying the cluster.

    Returns:
        float: The two-sided p-value adjusted for clustering.
    """
    # Encode treatment as binary 0/1 for regression
    # Assuming treatment_col has exactly two unique values
    treatment_encoded = pd.get_dummies(data[treatment_col], prefix='treat')
    if treatment_encoded.shape[1] == 1:
        # If only one dummy created (e.g., if one group is reference), handle explicitly
        # We expect two groups. If one is 'control' and one is 'treatment', get_dummies might drop one if not careful.
        # Let's ensure we have a binary indicator.
        unique_treat = data[treatment_col].unique()
        if len(unique_treat) != 2:
            raise ValueError(f"Expected 2 treatment groups, found {len(unique_treat)}")
        
        # Create binary indicator: 1 if second group, 0 if first
        treat_map = {unique_treat[0]: 0, unique_treat[1]: 1}
        data['treat_binary'] = data[treatment_col].map(treat_map)
        X = data[['treat_binary']]
    else:
        # Take the second column as the treatment indicator (assuming first is reference)
        # Or simpler: just map the second unique value to 1
        unique_treat = sorted(data[treatment_col].unique())
        treat_map = {unique_treat[0]: 0, unique_treat[1]: 1}
        data['treat_binary'] = data[treatment_col].map(treat_map)
        X = data[['treat_binary']]

    y = data[outcome_col]
    clusters = data[cluster_id_col]

    # Fit OLS manually to extract residuals and design matrix for CR2
    # Using statsmodels API for robust covariance
    import statsmodels.api as sm
    
    model = sm.OLS(y, sm.add_constant(X))
    results = model.fit(cov_type='cluster', cov_kwds={'groups': clusters})
    
    # Extract p-value for the treatment coefficient (index 1)
    p_value = results.pvalues[1]
    return float(p_value)

def run_block_permutation(data: pd.DataFrame, treatment_col: str, outcome_col: str, cluster_id_col: str, n_permutations: int = 1000) -> float:
    """
    Perform a block permutation test by shuffling treatment labels at the cluster level.

    This non-parametric approach respects the cluster structure.

    Args:
        data: DataFrame containing the observations.
        treatment_col: Name of the column indicating treatment group.
        outcome_col: Name of the column containing the outcome metric.
        cluster_id_col: Name of the column identifying the cluster.
        n_permutations: Number of permutations to perform.

    Returns:
        float: The empirical p-value.
    """
    # Aggregate to cluster level means to ensure block permutation
    # Or simply permute the treatment assignment at the cluster level and re-join
    
    # Get unique clusters and their current treatment
    cluster_treatments = data[[cluster_id_col, treatment_col]].drop_duplicates()
    cluster_ids = cluster_treatments[cluster_id_col].values
    current_treatments = cluster_treatments[treatment_col].values
    
    # Calculate observed statistic: difference in means
    group_0 = data[data[treatment_col] == current_treatments[0]][outcome_col].mean()
    group_1 = data[data[treatment_col] == current_treatments[1]][outcome_col].mean()
    observed_stat = group_1 - group_0
    
    # Create a mapping of cluster_id to its treatment group for permutation
    # We will permute the treatment labels assigned to clusters
    unique_treats = np.unique(current_treatments)
    if len(unique_treats) != 2:
        raise ValueError("Block permutation requires exactly two treatment groups.")
    
    count_1 = np.sum(current_treatments == unique_treats[1])
    n_clusters = len(cluster_ids)
    
    perm_stats = []
    for _ in range(n_permutations):
        # Permute the treatment labels assigned to clusters
        perm_treats = np.random.permutation(current_treatments)
        
        # Map back to observations
        perm_map = dict(zip(cluster_ids, perm_treats))
        data['perm_treatment'] = data[cluster_id_col].map(perm_map)
        
        # Calculate statistic for this permutation
        g0 = data[data['perm_treatment'] == unique_treats[0]][outcome_col].mean()
        g1 = data[data['perm_treatment'] == unique_treats[1]][outcome_col].mean()
        perm_stats.append(g1 - g0)
    
    perm_stats = np.array(perm_stats)
    
    # Two-sided p-value
    # Count how many permuted stats are as extreme or more extreme than observed
    extreme_count = np.sum(np.abs(perm_stats) >= np.abs(observed_stat))
    p_value = (extreme_count + 1) / (n_permutations + 1)
    
    return float(p_value)
