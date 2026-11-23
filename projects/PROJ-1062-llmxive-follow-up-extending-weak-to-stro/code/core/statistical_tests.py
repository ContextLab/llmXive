import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from scipy import stats
from scipy.stats import ttest_rel, wilcoxon
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def paired_ttest(
    baseline_scores: List[float],
    treatment_scores: List[float],
    alternative: str = "greater"
) -> Dict[str, float]:
    """
    Perform a paired t-test to compare baseline and treatment scores.

    Args:
        baseline_scores: List of performance scores from the baseline model.
        treatment_scores: List of performance scores from the treatment (Direct-OPD) model.
        alternative: Hypothesis alternative. 'greater' checks if treatment > baseline.
                   Options: 'two-sided', 'less', 'greater'.

    Returns:
        Dictionary containing 'statistic' (t-value) and 'pvalue'.

    Raises:
        ValueError: If input lists are empty or have different lengths.
    """
    if not baseline_scores or not treatment_scores:
        raise ValueError("Input lists cannot be empty.")
    if len(baseline_scores) != len(treatment_scores):
        raise ValueError("Input lists must have the same length.")

    x = np.array(baseline_scores)
    y = np.array(treatment_scores)

    # scipy.stats.ttest_rel returns (t_stat, p_value) for two-sided by default.
    # We need to handle the 'alternative' parameter manually for older scipy versions
    # or rely on the 'alternative' arg if available (scipy >= 1.6.0).
    try:
        t_stat, p_val = ttest_rel(x, y, alternative=alternative)
    except TypeError:
        # Fallback for older scipy versions without 'alternative' arg
        t_stat, p_val = ttest_rel(x, y)
        if alternative == 'greater':
            # If mean diff > 0, p_val is p_val/2, else 1 - p_val/2
            if np.mean(y - x) > 0:
                p_val = p_val / 2
            else:
                p_val = 1.0 - (p_val / 2)
        elif alternative == 'less':
            if np.mean(y - x) < 0:
                p_val = p_val / 2
            else:
                p_val = 1.0 - (p_val / 2)

    return {
        "statistic": float(t_stat),
        "pvalue": float(p_val)
    }


def wilcoxon_signed_rank(
    baseline_scores: List[float],
    treatment_scores: List[float],
    alternative: str = "greater"
) -> Dict[str, float]:
    """
    Perform a Wilcoxon signed-rank test for non-parametric paired data.
    Preferred for small sample sizes (n < 30) or non-normal distributions.

    Args:
        baseline_scores: List of performance scores from the baseline model.
        treatment_scores: List of performance scores from the treatment model.
        alternative: Hypothesis alternative ('two-sided', 'less', 'greater').

    Returns:
        Dictionary containing 'statistic' (W) and 'pvalue'.

    Raises:
        ValueError: If input lists are empty or have different lengths.
    """
    if not baseline_scores or not treatment_scores:
        raise ValueError("Input lists cannot be empty.")
    if len(baseline_scores) != len(treatment_scores):
        raise ValueError("Input lists must have the same length.")

    x = np.array(baseline_scores)
    y = np.array(treatment_scores)

    try:
        # scipy >= 1.6.0 supports 'alternative'
        stat, p_val = wilcoxon(x, y, alternative=alternative)
    except TypeError:
        # Fallback for older scipy versions
        stat, p_val = wilcoxon(x, y)
        # Manual adjustment for one-sided tests based on sum of ranks
        # Note: This is a simplified approximation; exact one-sided p-values
        # depend on the distribution of the rank sum.
        # For 'greater' (treatment > baseline), we check if the sum of positive ranks is significant.
        # scipy's wilcoxon returns the sum of ranks for the smaller of the two sums (T).
        # If we assume the direction, we halve the two-sided p-value if the direction matches.
        diff = y - x
        if alternative == 'greater':
            if np.sum(diff) > 0:
                p_val = p_val / 2
            else:
                p_val = 1.0 - (p_val / 2)
        elif alternative == 'less':
            if np.sum(diff) < 0:
                p_val = p_val / 2
            else:
                p_val = 1.0 - (p_val / 2)

    return {
        "statistic": float(stat),
        "pvalue": float(p_val)
    }


def bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Union[List[float], List[bool], float]]:
    """
    Apply Bonferroni correction for multiple comparisons.

    Args:
        p_values: List of raw p-values from independent tests.
        alpha: Significance level (default 0.05).

    Returns:
        Dictionary with 'adjusted_p_values' and 'significant' (boolean list).
    """
    n = len(p_values)
    if n == 0:
        return {"adjusted_p_values": [], "significant": []}

    adjusted = [min(p * n, 1.0) for p in p_values]
    significant = [p < alpha for p in adjusted]

    return {
        "adjusted_p_values": adjusted,
        "significant": significant
    }


def holm_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Union[List[float], List[bool]]]:
    """
    Apply Holm-Bonferroni step-down correction.
    More powerful than Bonferroni while controlling Family-Wise Error Rate.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level.

    Returns:
        Dictionary with 'adjusted_p_values' and 'significant'.
    """
    n = len(p_values)
    if n == 0:
        return {"adjusted_p_values": [], "significant": []}

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = [p_values[i] for i in sorted_indices]

    adjusted_sorted = []
    for i, p in enumerate(sorted_p):
        # Holm's method: compare p_i with alpha / (n - i)
        # Adjusted p-value is max( (n-j)*p_j for j <= i )
        # But simpler implementation:
        # adj_p = min(1, max( (n-i)*p for i in range(k) ))
        # Standard Holm calculation:
        adj = min(1.0, p * (n - i))
        adjusted_sorted.append(adj)

    # Ensure monotonicity (adjusted p-values must be non-decreasing)
    current_max = 0.0
    final_adjusted = []
    for val in adjusted_sorted:
        current_max = max(current_max, val)
        final_adjusted.append(current_max)

    # Restore original order
    result_adjusted = [0.0] * n
    for i, adj_val in zip(sorted_indices, final_adjusted):
        result_adjusted[i] = adj_val

    significant = [p < alpha for p in result_adjusted]

    return {
        "adjusted_p_values": result_adjusted,
        "significant": significant
    }


def cluster_robust_se(
    scores: List[List[float]],
    n_clusters: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate Cluster-Robust Standard Errors.
    This is a simplified implementation assuming the input 'scores' is a list of
    lists, where each inner list represents a cluster (e.g., different seeds or runs).
    If n_clusters is not provided, it is inferred from the length of scores.

    Note: The full Liang & Zeger (1986) implementation requires a model specification
    (e.g., linear regression). Here, we compute the robust variance of the mean
    across clusters, which is the standard approach for aggregating results from
    multiple independent experimental seeds.

    Formula: Var(μ) = (1 / (M*(M-1))) * Σ (x̄_i - μ)²
    where M is number of clusters, x̄_i is mean of cluster i, μ is overall mean.

    Args:
        scores: List of clusters, each cluster is a list of scores.
        n_clusters: Number of clusters (optional).

    Returns:
        Dictionary with 'standard_error' and 'degrees_of_freedom'.
    """
    if not scores:
        raise ValueError("Scores list cannot be empty.")

    cluster_means = []
    for cluster in scores:
        if not cluster:
            continue
        cluster_means.append(np.mean(cluster))

    if len(cluster_means) < 2:
        logger.warning("Less than 2 clusters found. Cannot compute cluster-robust SE reliably. Returning standard error of the mean within clusters.")
        # Fallback to standard error if only 1 cluster
        all_scores = [s for cluster in scores for s in cluster]
        if len(all_scores) < 2:
            return {"standard_error": 0.0, "degrees_of_freedom": 0}
        return {
            "standard_error": float(np.std(all_scores) / np.sqrt(len(all_scores))),
            "degrees_of_freedom": len(all_scores) - 1
        }

    M = len(cluster_means)
    overall_mean = np.mean(cluster_means)

    # Sum of squared deviations
    ss = sum((x - overall_mean) ** 2 for x in cluster_means)

    # Cluster-robust variance of the mean
    # Var = (1 / (M * (M - 1))) * Σ (x̄_i - μ)²
    variance = ss / (M * (M - 1))
    se = np.sqrt(variance)

    # Degrees of freedom approximated as M - 1
    dof = M - 1

    return {
        "standard_error": float(se),
        "degrees_of_freedom": int(dof)
    }


def classify_significance(
    p_value: float,
    alpha: float = 0.05
) -> str:
    """
    Classify the significance level based on p-value.

    Args:
        p_value: The calculated p-value.
        alpha: Significance threshold.

    Returns:
        String classification: 'significant', 'marginally_significant', or 'not_significant'.
    """
    if p_value < alpha:
        return "significant"
    elif p_value < alpha * 2: # Arbitrary margin for "marginally significant"
        return "marginally_significant"
    else:
        return "not_significant"


def run_comprehensive_tests(
    baseline_scores: List[float],
    treatment_scores: List[float],
    alpha: float = 0.05,
    method: str = "wilcoxon"
) -> Dict[str, Any]:
    """
    Run a comprehensive statistical analysis including paired tests and multiple comparison corrections.

    Args:
        baseline_scores: List of baseline scores.
        treatment_scores: List of treatment scores.
        alpha: Significance level.
        method: 'ttest' or 'wilcoxon'.

    Returns:
        Dictionary containing test statistics, p-values, and significance classification.
    """
    results = {
        "method": method,
        "n_samples": len(baseline_scores),
        "baseline_mean": float(np.mean(baseline_scores)),
        "treatment_mean": float(np.mean(treatment_scores)),
        "gain": float(np.mean(treatment_scores) - np.mean(baseline_scores))
    }

    if method == "ttest":
        test_res = paired_ttest(baseline_scores, treatment_scores, alternative="greater")
    elif method == "wilcoxon":
        test_res = wilcoxon_signed_rank(baseline_scores, treatment_scores, alternative="greater")
    else:
        raise ValueError(f"Unknown method: {method}")

    results["raw_p_value"] = test_res["pvalue"]
    results["statistic"] = test_res["statistic"]
    results["significance"] = classify_significance(test_res["pvalue"], alpha)

    # If we had multiple tests (e.g., MoE and SSM), we would apply correction here.
    # For a single test, correction is trivial (p * 1).
    results["adjusted_p_value"] = test_res["pvalue"]
    results["is_significant_after_correction"] = results["adjusted_p_value"] < alpha

    return results


def main():
    """
    Main entry point for standalone execution.
    Demonstrates the statistical tests with dummy data representing
    the expected output structure from MoE and SSM experiments.
    """
    logger.info("Running statistical tests demonstration...")

    # Simulated data: 5 seeds (n=5) as per project constraints
    # These are placeholder values to demonstrate the code flow.
    # In a real run, these would be loaded from data/results/*.json
    mock_baseline_moe = [0.45, 0.48, 0.42, 0.50, 0.47]
    mock_treatment_moe = [0.52, 0.55, 0.51, 0.58, 0.54]

    mock_baseline_ssm = [0.30, 0.32, 0.29, 0.35, 0.31]
    mock_treatment_ssm = [0.38, 0.40, 0.37, 0.42, 0.39]

    # Test MoE
    logger.info("Testing MoE results (Wilcoxon)...")
    moe_results = run_comprehensive_tests(mock_baseline_moe, mock_treatment_moe, method="wilcoxon")
    logger.info(f"MoE Results: {json.dumps(moe_results, indent=2)}")

    # Test SSM
    logger.info("Testing SSM results (Wilcoxon)...")
    ssm_results = run_comprehensive_tests(mock_baseline_ssm, mock_treatment_ssm, method="wilcoxon")
    logger.info(f"SSM Results: {json.dumps(ssm_results, indent=2)}")

    # Simulate multiple comparison correction across the two tests (MoE and SSM)
    raw_p_values = [moe_results["raw_p_value"], ssm_results["raw_p_value"]]
    
    bonf_result = bonferroni_correction(raw_p_values)
    holm_result = holm_bonferroni_correction(raw_p_values)

    logger.info("Bonferroni Correction Results:")
    logger.info(json.dumps(bonf_result, indent=2))

    logger.info("Holm-Bonferroni Correction Results:")
    logger.info(json.dumps(holm_result, indent=2))

    # Cluster Robust SE example (simulating multiple runs per seed if available)
    # Here we just use the single lists as "clusters" for demonstration
    cluster_data = [mock_baseline_moe, mock_treatment_moe]
    se_result = cluster_robust_se(cluster_data)
    logger.info(f"Cluster Robust SE (demo): {json.dumps(se_result, indent=2)}")

    logger.info("Statistical tests completed.")


if __name__ == "__main__":
    main()