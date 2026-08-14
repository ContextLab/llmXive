"""
Statistical testing module for significance analysis and multiple-comparison correction.

This module provides:
1. Paired t-test and Wilcoxon signed-rank test implementations
2. Cluster-robust standard errors calculation
3. Multiple-comparison corrections (Bonferroni, Holm-Bonferroni)
4. Significance classification logic
"""
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from scipy import stats
from scipy.stats import ttest_rel, wilcoxon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def paired_ttest(
    sample1: List[float], 
    sample2: List[float]
) -> Tuple[float, float]:
    """
    Perform a paired t-test on two related samples.
    
    Args:
        sample1: First sample (e.g., baseline log-probabilities)
        sample2: Second sample (e.g., Direct-OPD log-probabilities)
                
    Returns:
        Tuple of (t-statistic, p-value)
        
    Raises:
        ValueError: If samples have different lengths or insufficient data
    """
    if len(sample1) != len(sample2):
        raise ValueError(f"Samples must have same length: {len(sample1)} vs {len(sample2)}")
    
    if len(sample1) < 2:
        raise ValueError(f"Insufficient samples for t-test: {len(sample1)} (need >= 2)")
    
    t_stat, p_value = ttest_rel(sample2, sample1)
    return float(t_stat), float(p_value)


def wilcoxon_signed_rank(
    sample1: List[float], 
    sample2: List[float]
) -> Tuple[float, float]:
    """
    Perform a Wilcoxon signed-rank test on two related samples.
    
    Args:
        sample1: First sample
        sample2: Second sample
                
    Returns:
        Tuple of (W-statistic, p-value)
        
    Raises:
        ValueError: If samples have different lengths or insufficient data
    """
    if len(sample1) != len(sample2):
        raise ValueError(f"Samples must have same length: {len(sample1)} vs {len(sample2)}")
    
    if len(sample1) < 2:
        raise ValueError(f"Insufficient samples for Wilcoxon test: {len(sample1)} (need >= 2)")
    
    w_stat, p_value = wilcoxon(sample2, sample1)
    return float(w_stat), float(p_value)


def bonferroni_correction(
    p_values: List[float], 
    alpha: float = 0.05
) -> Tuple[List[float], bool]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level
                
    Returns:
        Tuple of (corrected p-values, whether any remain significant)
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return [], False
    
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    any_significant = any(p < alpha for p in corrected)
    return corrected, any_significant


def holm_bonferroni_correction(
    p_values: List[float], 
    alpha: float = 0.05
) -> Tuple[List[float], bool]:
    """
    Apply Holm-Bonferroni correction for multiple comparisons.
    
    This is a step-down procedure that is more powerful than Bonferroni.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level
                
    Returns:
        Tuple of (corrected p-values, whether any remain significant)
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return [], False
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_pvalues = [p_values[i] for i in sorted_indices]
    
    # Apply step-down correction
    corrected = [0.0] * n_tests
    for i, p in enumerate(sorted_pvalues):
        corrected_p = p * (n_tests - i)
        corrected[sorted_indices[i]] = min(corrected_p, 1.0)
    
    # Ensure monotonicity (corrected p-values should be non-decreasing)
    for i in range(1, n_tests):
        corrected[i] = max(corrected[i], corrected[i-1])
    
    any_significant = any(p < alpha for p in corrected)
    return corrected, any_significant


def cluster_robust_se(
    differences: List[float],
    n_clusters: int
) -> float:
    """
    Calculate cluster-robust standard errors.
    
    This accounts for potential correlation within clusters.
    
    Args:
        differences: List of differences (sample2 - sample1)
        n_clusters: Number of clusters
                
    Returns:
        Cluster-robust standard error
    """
    if len(differences) < 2:
        return 0.0
    
    differences = np.array(differences)
    mean_diff = np.mean(differences)
    
    # Simple cluster-robust SE calculation
    # In practice, this would need cluster assignments
    # Here we assume equal-sized clusters for demonstration
    cluster_size = len(differences) / n_clusters if n_clusters > 0 else 1
    
    # Calculate variance within clusters
    cluster_vars = []
    for i in range(n_clusters):
        start_idx = int(i * cluster_size)
        end_idx = int((i + 1) * cluster_size)
        if start_idx < len(differences):
            cluster_data = differences[start_idx:end_idx]
            if len(cluster_data) > 1:
                cluster_var = np.var(cluster_data, ddof=1)
                cluster_vars.append(cluster_var)
    
    if not cluster_vars:
        return np.std(differences, ddof=1) / np.sqrt(len(differences))
    
    avg_cluster_var = np.mean(cluster_vars)
    robust_se = np.sqrt(avg_cluster_var / len(differences) * n_clusters)
    
    return float(robust_se)


def classify_significance(
    p_value: float, 
    alpha: float = 0.05
) -> str:
    """
    Classify the significance level based on p-value.
    
    Args:
        p_value: The p-value to classify
        alpha: Significance threshold
                
    Returns:
        String classification: 'highly_significant', 'significant', 'marginally_significant', 'not_significant'
    """
    if p_value < 0.001:
        return "highly_significant"
    elif p_value < alpha:
        return "significant"
    elif p_value < 0.1:
        return "marginally_significant"
    else:
        return "not_significant"


def run_comprehensive_tests(
    baseline_values: List[float],
    direct_opd_values: List[float],
    alpha: float = 0.05,
    n_clusters: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run comprehensive statistical tests on model comparisons.
    
    Args:
        baseline_values: Baseline model log-probabilities
        direct_opd_values: Direct-OPD model log-probabilities
        alpha: Significance level
        n_clusters: Number of clusters for cluster-robust SE (optional)
                
    Returns:
        Dictionary containing all test results
    """
    if len(baseline_values) != len(direct_opd_values):
        raise ValueError("Baseline and Direct-OPD values must have same length")
    
    if len(baseline_values) < 2:
        return {
            "error": "Insufficient samples for statistical testing",
            "n_samples": len(baseline_values)
        }
    
    # Calculate differences
    differences = [opd - baseline for opd, baseline in zip(direct_opd_values, baseline_values)]
    
    # Run paired t-test
    try:
        t_stat, t_pvalue = paired_ttest(baseline_values, direct_opd_values)
        t_class = classify_significance(t_pvalue, alpha)
    except Exception as e:
        logger.warning(f"T-test failed: {e}")
        t_stat, t_pvalue, t_class = None, None, "error"
    
    # Run Wilcoxon test
    try:
        w_stat, w_pvalue = wilcoxon_signed_rank(baseline_values, direct_opd_values)
        w_class = classify_significance(w_pvalue, alpha)
    except Exception as e:
        logger.warning(f"Wilcoxon test failed: {e}")
        w_stat, w_pvalue, w_class = None, None, "error"
    
    # Apply multiple comparison corrections
    raw_pvalues = [t_pvalue, w_pvalue] if t_pvalue is not None and w_pvalue is not None else []
    
    bonf_corrected, bonf_any_sig = bonferroni_correction(raw_pvalues, alpha) if raw_pvalues else ([], False)
    holm_corrected, holm_any_sig = holm_bonferroni_correction(raw_pvalues, alpha) if raw_pvalues else ([], False)
    
    # Calculate cluster-robust SE if requested
    cluster_se = None
    if n_clusters is not None and n_clusters > 0:
        try:
            cluster_se = cluster_robust_se(differences, n_clusters)
        except Exception as e:
            logger.warning(f"Cluster-robust SE calculation failed: {e}")
    
    return {
        "n_samples": len(baseline_values),
        "mean_difference": float(np.mean(differences)),
        "std_difference": float(np.std(differences)),
        "paired_ttest": {
            "statistic": t_stat,
            "p_value": t_pvalue,
            "classification": t_class,
            "significant": t_pvalue < alpha if t_pvalue is not None else False
        },
        "wilcoxon": {
            "statistic": w_stat,
            "p_value": w_pvalue,
            "classification": w_class,
            "significant": w_pvalue < alpha if w_pvalue is not None else False
        },
        "multiple_comparison": {
            "bonferroni": {
                "corrected_pvalues": bonf_corrected,
                "any_significant": bonf_any_sig
            },
            "holm": {
                "corrected_pvalues": holm_corrected,
                "any_significant": holm_any_sig
            }
        },
        "cluster_robust_se": cluster_se,
        "alpha": alpha
    }


def main():
    """
    Main function to demonstrate statistical testing.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run statistical tests on model comparisons")
    parser.add_argument("--baseline", type=str, required=True, help="Path to baseline results JSON")
    parser.add_argument("--direct-opd", type=str, required=True, help="Path to Direct-OPD results JSON")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--clusters", type=int, default=None, help="Number of clusters")
    
    args = parser.parse_args()
    
    import json
    
    try:
        with open(args.baseline, 'r') as f:
            baseline_data = json.load(f)
        with open(args.direct_opd, 'r') as f:
            direct_opd_data = json.load(f)
        
        baseline_values = baseline_data.get("log_probabilities", [])
        direct_opd_values = direct_opd_data.get("log_probabilities", [])
        
        if not baseline_values or not direct_opd_values:
            print("Error: No log-probabilities found in result files")
            return 1
        
        results = run_comprehensive_tests(
            baseline_values,
            direct_opd_values,
            args.alpha,
            args.clusters
        )
        
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())