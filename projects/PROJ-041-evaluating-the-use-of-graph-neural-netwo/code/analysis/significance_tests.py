"""
Significance testing module for comparing GNN performance against baselines.
Implements Permutation Tests and Benjamini-Hochberg correction as per project plan.
"""
import os
import json
import numpy as np
from typing import List, Dict, Tuple, Any

def run_permutation_test(
    gcn_scores: List[float],
    baseline_scores: List[float],
    n_permutations: int = 10000,
    alpha: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform a permutation test to determine if GCN scores are significantly
    different from baseline scores.

    Args:
        gcn_scores: List of performance scores (e.g., AUC) from GCN model.
        baseline_scores: List of performance scores from baseline model (RF or XGB).
        n_permutations: Number of permutations to run.
        alpha: Significance level for p-value threshold.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing p-value, observed difference, and significance status.
    """
    np.random.seed(seed)

    # Combine scores
    combined = np.array(gcn_scores + baseline_scores)
    n_gcn = len(gcn_scores)
    n_baseline = len(baseline_scores)
    n_total = n_gcn + n_baseline

    # Observed difference (GCN mean - Baseline mean)
    observed_diff = np.mean(gcn_scores) - np.mean(baseline_scores)

    # Permutation distribution
    count_extreme = 0
    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_gcn = combined[:n_gcn]
        perm_baseline = combined[n_gcn:]
        perm_diff = np.mean(perm_gcn) - np.mean(perm_baseline)
        if abs(perm_diff) >= abs(observed_diff):
            count_extreme += 1

    p_value = count_extreme / n_permutations
    is_significant = p_value < alpha

    return {
        "observed_difference": float(observed_diff),
        "p_value": float(p_value),
        "is_significant": bool(is_significant),
        "alpha": alpha,
        "n_permutations": n_permutations,
        "n_gcn_samples": n_gcn,
        "n_baseline_samples": n_baseline
    }

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg correction to control False Discovery Rate (FDR).

    Args:
        p_values: List of raw p-values from multiple hypothesis tests.
        alpha: Target FDR threshold.

    Returns:
        Dictionary containing adjusted p-values, significance decisions, and FDR status.
    """
    n = len(p_values)
    if n == 0:
        return {
            "adjusted_p_values": [],
            "is_significant": [],
            "fdr_threshold": alpha,
            "num_significant": 0
        }

    # Sort p-values with original indices
    indexed_pvals = list(enumerate(p_values))
    sorted_indices = sorted(indexed_pvals, key=lambda x: x[1])

    adjusted_pvals = [0.0] * n
    rank_multiplier = n

    # Calculate adjusted p-values (step-up procedure)
    for rank, (orig_idx, p_val) in enumerate(sorted_indices, 1):
        # BH adjusted p-value: p * n / rank
        adj_p = p_val * n / rank
        # Ensure monotonicity: adjusted p-values should be non-decreasing
        if rank > 1:
            prev_adj = adjusted_pvals[sorted_indices[rank - 2][0]]
            adj_p = max(adj_p, prev_adj)
        # Cap at 1.0
        adj_p = min(adj_p, 1.0)
        adjusted_pvals[orig_idx] = adj_p

    # Determine significance
    is_significant = [p < alpha for p in adjusted_pvals]
    num_significant = sum(is_significant)

    return {
        "raw_p_values": p_values,
        "adjusted_p_values": adjusted_pvals,
        "is_significant": is_significant,
        "fdr_threshold": alpha,
        "num_significant": num_significant
    }

def compare_model_pairs(
    gcn_results: List[float],
    rf_results: List[float],
    xgb_results: List[float],
    n_permutations: int = 10000,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Compare GCN against RF and XGB baselines using permutation tests.

    Args:
        gcn_results: List of GCN performance scores.
        rf_results: List of Random Forest performance scores.
        xgb_results: List of XGBoost performance scores.
        n_permutations: Number of permutations for tests.
        alpha: Significance threshold.

    Returns:
        Dictionary with test results for both comparisons.
    """
    gcn_vs_rf = run_permutation_test(gcn_results, rf_results, n_permutations, alpha)
    gcn_vs_xgb = run_permutation_test(gcn_results, xgb_results, n_permutations, alpha)

    # Apply BH correction to the two p-values
    p_values = [gcn_vs_rf["p_value"], gcn_vs_xgb["p_value"]]
    bh_results = benjamini_hochberg_correction(p_values, alpha)

    return {
        "gcn_vs_rf": gcn_vs_rf,
        "gcn_vs_xgb": gcn_vs_xgb,
        "bh_correction": bh_results,
        "summary": {
            "gcn_vs_rf_significant": gcn_vs_rf["is_significant"],
            "gcn_vs_xgb_significant": gcn_vs_xgb["is_significant"],
            "fdr_controlled": bh_results["num_significant"] == sum([gcn_vs_rf["is_significant"], gcn_vs_xgb["is_significant"]])
        }
    }

def save_significance_report(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save significance test results to a JSON file.

    Args:
        results: Dictionary containing test results.
        output_path: Path to output file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
