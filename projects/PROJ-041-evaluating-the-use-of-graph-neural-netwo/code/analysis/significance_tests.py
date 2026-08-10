import os
import json
import numpy as np
from typing import List, Dict, Tuple, Any

def run_permutation_test(
    observed_diff: float,
    model_a_scores: List[float],
    model_b_scores: List[float],
    n_permutations: int = 10000,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a permutation test to assess statistical significance of model difference.
    
    Args:
        observed_diff: Observed difference in performance metrics.
        model_a_scores: Performance scores for model A.
        model_b_scores: Performance scores for model B.
        n_permutations: Number of permutations to run.
        alpha: Significance level.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary with p-value, significance, and test statistics.
    """
    if seed is not None:
        np.random.seed(seed)
        
    all_scores = np.array(model_a_scores + model_b_scores)
    n_a = len(model_a_scores)
    n_b = len(model_b_scores)
    n_total = n_a + n_b
    
    count_extreme = 0
    
    for _ in range(n_permutations):
        # Randomly permute labels
        perm_indices = np.random.permutation(n_total)
        perm_a = all_scores[perm_indices[:n_a]]
        perm_b = all_scores[perm_indices[n_a:]]
        
        perm_diff = np.mean(perm_a) - np.mean(perm_b)
        
        if abs(perm_diff) >= abs(observed_diff):
            count_extreme += 1
            
    p_value = count_extreme / n_permutations
    is_significant = p_value < alpha
    
    return {
        'observed_difference': float(observed_diff),
        'p_value': float(p_value),
        'is_significant': is_significant,
        'alpha': alpha,
        'n_permutations': n_permutations,
        'model_a_mean': float(np.mean(model_a_scores)),
        'model_b_mean': float(np.mean(model_b_scores)),
        'model_a_std': float(np.std(model_a_scores)),
        'model_b_std': float(np.std(model_b_scores))
    }

def benjamini_hochberg_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level.
        
    Returns:
        Dictionary with adjusted p-values and significance decisions.
    """
    n = len(p_values)
    if n == 0:
        return {
            'adjusted_p_values': [],
            'is_significant': [],
            'alpha': alpha,
            'n_tests': 0
        }
        
    # Sort p-values and track original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p_values = []
    for i, p in enumerate(sorted_p_values):
        # BH adjustment: p * n / (i + 1)
        adjusted = p * n / (i + 1)
        # Ensure monotonicity (cumulative min from right)
        adjusted_p_values.append(adjusted)
        
    # Enforce monotonicity from right to left
    for i in range(n - 2, -1, -1):
        adjusted_p_values[i] = min(adjusted_p_values[i], adjusted_p_values[i + 1])
        
    # Clip to [0, 1]
    adjusted_p_values = [min(max(p, 0.0), 1.0) for p in adjusted_p_values]
    
    # Restore original order
    final_adjusted = [0.0] * n
    final_significant = [False] * n
    
    for idx, adj_p in zip(sorted_indices, adjusted_p_values):
        final_adjusted[idx] = adj_p
        final_significant[idx] = adj_p < alpha
        
    return {
        'raw_p_values': p_values,
        'adjusted_p_values': final_adjusted,
        'is_significant': final_significant,
        'alpha': alpha,
        'n_tests': n,
        'significant_count': sum(final_significant)
    }

def compare_model_pairs(
    gcn_scores: List[float],
    rf_scores: List[float],
    xgb_scores: List[float],
    n_permutations: int = 10000,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compare all pairs of models using permutation tests.
    
    Args:
        gcn_scores: GCN performance scores.
        rf_scores: Random Forest performance scores.
        xgb_scores: XGBoost performance scores.
        n_permutations: Number of permutations per test.
        alpha: Significance level.
        seed: Random seed.
        
    Returns:
        Dictionary with pairwise comparison results.
    """
    results = {}
    
    # GCN vs RF
    gcn_vs_rf = run_permutation_test(
        observed_diff=np.mean(gcn_scores) - np.mean(rf_scores),
        model_a_scores=gcn_scores,
        model_b_scores=rf_scores,
        n_permutations=n_permutations,
        alpha=alpha,
        seed=seed
    )
    results['gcn_vs_rf'] = gcn_vs_rf
    
    # GCN vs XGB
    gcn_vs_xgb = run_permutation_test(
        observed_diff=np.mean(gcn_scores) - np.mean(xgb_scores),
        model_a_scores=gcn_scores,
        model_b_scores=xgb_scores,
        n_permutations=n_permutations,
        alpha=alpha,
        seed=seed + 1 if seed else None
    )
    results['gcn_vs_xgb'] = gcn_vs_xgb
    
    # RF vs XGB
    rf_vs_xgb = run_permutation_test(
        observed_diff=np.mean(rf_scores) - np.mean(xgb_scores),
        model_a_scores=rf_scores,
        model_b_scores=xgb_scores,
        n_permutations=n_permutations,
        alpha=alpha,
        seed=seed + 2 if seed else None
    )
    results['rf_vs_xgb'] = rf_vs_xgb
    
    # Collect all p-values for BH correction
    all_p_values = [
        gcn_vs_rf['p_value'],
        gcn_vs_xgb['p_value'],
        rf_vs_xgb['p_value']
    ]
    
    bh_results = benjamini_hochberg_correction(all_p_values, alpha)
    results['bh_correction'] = bh_results
    
    return results

def save_significance_report(
    results: Dict[str, Any],
    output_path: str = 'data/results/significance_report.json'
) -> None:
    """
    Save significance test results to JSON.
    
    Args:
        results: Dictionary containing all test results.
        output_path: Path to output file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logging = __import__('logging')
    logging.info(f"Significance report saved to {output_path}")
