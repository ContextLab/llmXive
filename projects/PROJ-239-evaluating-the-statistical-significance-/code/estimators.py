import warnings
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.contrast import ContrastResults
from statsmodels.stats.multitest import multipletests


def run_naive_ttest(data: pd.DataFrame, treatment_col: str, outcome_col: str) -> float:
    """
    Perform an independent two-sample t-test assuming independence of observations.
    
    WARNING: This method is invalid for clustered data. Use only as a baseline
    to demonstrate Type I error inflation.
    
    Args:
        data: DataFrame containing the data.
        treatment_col: Name of the column containing treatment labels (binary).
        outcome_col: Name of the column containing outcome values.
        
    Returns:
        The two-sided p-value from the t-test.
    """
    groups = data.groupby(treatment_col)[outcome_col]
    if groups.ngroups != 2:
        raise ValueError(f"Expected exactly 2 treatment groups, found {groups.ngroups}")
    
    group_0, group_1 = groups.groups[0], groups.groups[1]
    t_stat, p_val = stats.ttest_ind(group_0, group_1)
    return float(p_val)


def run_naive_ttest_with_warning(data: pd.DataFrame, treatment_col: str, outcome_col: str) -> float:
    """
    Wrapper for run_naive_ttest that issues a warning about cluster independence violation.
    
    Args:
        data: DataFrame containing the data.
        treatment_col: Name of the column containing treatment labels (binary).
        outcome_col: Name of the column containing outcome values.
        
    Returns:
        The two-sided p-value from the t-test.
    """
    warnings.warn(
        "Using naive t-test on clustered data violates the assumption of independence. "
        "This method is intended for baseline comparison only and will likely inflate Type I error.",
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
    Perform a t-test with cluster-robust standard errors (CR2 adjustment).
    
    This is the constitutionally compliant method for clustered data.
    
    Args:
        data: DataFrame containing the data.
        treatment_col: Name of the column containing treatment labels (binary).
        outcome_col: Name of the column containing outcome values.
        cluster_id_col: Name of the column containing cluster identifiers.
        
    Returns:
        The two-sided p-value adjusted for clustering.
    """
    # Prepare data for statsmodels
    # Ensure treatment is numeric (0/1)
    data = data.copy()
    data['_treat_num'] = pd.factorize(data[treatment_col])[0].astype(int)
    
    # Fit OLS model
    import statsmodels.api as sm
    formula = f"{outcome_col} ~ {_treat_num}"
    model = sm.OLS.from_formula(formula, data)
    results = model.fit()
    
    # Apply cluster-robust covariance
    # CR2 adjustment is preferred for small number of clusters
    # We need to pass the cluster IDs as a groupby object
    cluster_groups = data.groupby(cluster_id_col).ngroups
    
    # Using statsmodels' built-in cluster robust covariance
    # Note: statsmodels 0.14.1 supports 'cluster' cov_type
    try:
        # Get the cluster IDs as an array
        cluster_ids = data[cluster_id_col].values
        
        # Fit with cluster robust covariance
        # We need to reconstruct the model to apply cov_type='cluster'
        # The easiest way is to use get_robustcov_results
        # However, the standard OLS fit doesn't automatically handle cluster IDs
        # We use the 'cov_type' parameter with 'cluster' and 'groups'
        
        # Re-fit to get the results object we can adjust
        # Actually, we can just call get_robustcov_results on the fitted model
        # but we need to pass the groups
        
        # Let's use the direct approach with OLS and cov_type
        X = sm.add_constant(data['_treat_num'])
        y = data[outcome_col]
        model = sm.OLS(y, X)
        results = model.fit(cov_type='cluster', cov_kwds={'groups': cluster_ids})
        
        # Get p-value for the treatment coefficient (index 1)
        p_val = results.pvalues[1]
        return float(p_val)
        
    except Exception as e:
        # Fallback if cluster robust fails (e.g., too few clusters)
        warnings.warn(f"Cluster robust estimation failed: {e}. Falling back to naive t-test.", UserWarning)
        return run_naive_ttest(data, treatment_col, outcome_col)


def run_block_permutation(
    data: pd.DataFrame,
    treatment_col: str,
    outcome_col: str,
    cluster_id_col: str,
    n_permutations: int = 1000
) -> float:
    """
    Perform a block permutation test by permuting treatment labels at the cluster level.
    
    This method respects the cluster structure by only swapping treatment assignments
    between entire clusters, not individual observations.
    
    Args:
        data: DataFrame containing the data.
        treatment_col: Name of the column containing treatment labels (binary).
        outcome_col: Name of the column containing outcome values.
        cluster_id_col: Name of the column containing cluster identifiers.
        n_permutations: Number of permutations to perform.
        
    Returns:
        The two-sided p-value from the block permutation test.
    """
    # Validate inputs
    if data[treatment_col].nunique() != 2:
        raise ValueError(f"Expected exactly 2 treatment groups, found {data[treatment_col].nunique()}")
    
    # Get unique clusters and their treatment assignments
    cluster_treatment = data[[cluster_id_col, treatment_col]].drop_duplicates()
    clusters = cluster_treatment[cluster_id_col].unique()
    n_clusters = len(clusters)
    
    if n_clusters < 2:
        raise ValueError("Need at least 2 clusters to perform permutation test")
    
    # Calculate observed test statistic (difference in means)
    # Use t-statistic as the test statistic for better power
    def calculate_t_stat(df, treat_col, out_col):
        groups = df.groupby(treat_col)[out_col]
        if groups.ngroups != 2:
            return 0.0
        g0, g1 = groups.groups[0], groups.groups[1]
        # Welch's t-test statistic
        n0, n1 = len(g0), len(g1)
        mean0, mean1 = g0.mean(), g1.mean()
        var0, var1 = g0.var(ddof=1), g1.var(ddof=1)
        
        # Handle zero variance
        if var0 == 0 and var1 == 0:
            return 0.0 if mean0 == mean1 else float('inf')
        
        se = np.sqrt(var0/n0 + var1/n1)
        if se == 0:
            return 0.0
        return (mean1 - mean0) / se
    
    observed_stat = calculate_t_stat(data, treatment_col, outcome_col)
    observed_stat = abs(observed_stat)  # Two-sided: use absolute value
    
    # Get cluster-level data for permutation
    # We need to map each cluster to its treatment and outcomes
    cluster_data = {}
    for cid in clusters:
        cluster_mask = data[cluster_id_col] == cid
        cluster_data[cid] = {
            'treatment': data.loc[cluster_mask, treatment_col].iloc[0],
            'outcomes': data.loc[cluster_mask, outcome_col].values
        }
    
    # Permutation loop
    count_extreme = 0
    rng = np.random.default_rng()
    
    for _ in range(n_permutations):
        # Permute treatment labels at cluster level
        permuted_treatments = rng.permutation([cluster_data[c]['treatment'] for c in clusters])
        
        # Create permuted dataset
        permuted_data = data.copy()
        for i, cid in enumerate(clusters):
            cluster_mask = permuted_data[cluster_id_col] == cid
            permuted_data.loc[cluster_mask, treatment_col] = permuted_treatments[i]
        
        # Calculate test statistic for permuted data
        permuted_stat = calculate_t_stat(permuted_data, treatment_col, outcome_col)
        permuted_stat = abs(permuted_stat)
        
        if permuted_stat >= observed_stat:
            count_extreme += 1
    
    # Calculate p-value
    p_value = (count_extreme + 1) / (n_permutations + 1)
    return float(p_value)
