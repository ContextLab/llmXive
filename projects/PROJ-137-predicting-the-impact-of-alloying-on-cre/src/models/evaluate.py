"""
Model Evaluation Module (T024).

Implements:
1. Permutation Test (10,000 permutations) for 20 <= N < 100.
2. Bootstrap 95% CI for N < 20.
3. Sensitivity analysis on p-value cutoffs.
"""
import os
import json
import logging
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

def run_permutation_test(thermo_scores, comp_scores, n_permutations=10000, seed=42):
    """
    Permutation Test to compare two sets of CV scores.
    Null Hypothesis: The difference in mean scores is due to chance.
    """
    np.random.seed(seed)
    thermo = np.array(thermo_scores)
    comp = np.array(comp_scores)
    
    obs_diff = np.mean(thermo) - np.mean(comp)
    
    n = len(thermo)
    perm_diffs = []
    
    # Permutation loop
    for _ in range(n_permutations):
        # Randomly shuffle signs of the differences or permute labels
        # Since scores are paired by CV fold, we permute the assignment of which model got which score
        # But here we have two arrays. We combine them and randomly assign n to thermo, n to comp?
        # No, the scores are paired by fold. We should shuffle the pairing.
        # Correct approach: Shuffle the indices of one array relative to the other.
        perm_indices = np.random.permutation(len(thermo))
        perm_comp = comp[perm_indices]
        perm_diff = np.mean(thermo) - np.mean(perm_comp)
        perm_diffs.append(perm_diff)
    
    perm_diffs = np.array(perm_diffs)
    
    # Two-tailed p-value
    p_value = (np.sum(np.abs(perm_diffs) >= np.abs(obs_diff)) + 1) / (n_permutations + 1)
    
    return p_value

def run_bootstrap_ci(thermo_scores, n_bootstraps=1000, seed=42):
    """
    Bootstrap 95% Confidence Interval for the mean of thermodynamic scores.
    """
    np.random.seed(seed)
    data = np.array(thermo_scores)
    n = len(data)
    
    bootstrap_means = []
    for _ in range(n_bootstraps):
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))
    
    bootstrap_means = np.array(bootstrap_means)
    ci_lower = np.percentile(bootstrap_means, 2.5)
    ci_upper = np.percentile(bootstrap_means, 97.5)
    
    return [ci_lower, ci_upper]

def evaluate_models(metrics_path):
    """
    Load metrics and run statistical tests based on N.
    """
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    thermo_scores = metrics["thermodynamic_scores"]
    comp_scores = metrics["composition_scores"]
    n = metrics["thermodynamic_n"]
    
    results = {
        "n_samples": n,
        "method": None,
        "p_value": None,
        "ci_bounds": None,
        "sensitivity_analysis": {}
    }
    
    if n < 20:
        # Bootstrap CI
        logger.info(f"N={n} < 20. Using Bootstrap 95% CI.")
        results["method"] = "Bootstrap 95% CI"
        results["ci_bounds"] = run_bootstrap_ci(thermo_scores, n_bootstraps=2000) # Increased for accuracy
    elif 20 <= n < 100:
        # Permutation Test
        logger.info(f"20 <= N={n} < 100. Using Permutation Test (10,000 permutations).")
        results["method"] = "Permutation Test"
        p_val = run_permutation_test(thermo_scores, comp_scores, n_permutations=10000)
        results["p_value"] = p_val
        
        # Sensitivity Analysis on cutoffs {0.01, 0.05, 0.1}
        cutoffs = [0.01, 0.05, 0.1]
        sensitivity = {}
        for cut in cutoffs:
            sensitivity[str(cut)] = "significant" if p_val < cut else "not significant"
        results["sensitivity_analysis"] = sensitivity
    else:
        # N >= 100, usually Permutation or t-test is fine, but spec says Permutation for <100.
        # For >= 100, we can use Permutation or assume normality.
        # We'll stick to Permutation for robustness if requested, or fallback.
        logger.info(f"N={n} >= 100. Using Permutation Test.")
        results["method"] = "Permutation Test"
        results["p_value"] = run_permutation_test(thermo_scores, comp_scores, n_permutations=10000)
    
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python evaluate.py <metrics_json_path>")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    res = evaluate_models(sys.argv[1])
    print(json.dumps(res, indent=2))
