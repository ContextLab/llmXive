"""
Statistical tests implementation for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.
Implements paired t-tests, Wilcoxon signed-rank tests, and bootstrap confidence intervals.
"""
import numpy as np
from scipy import stats
from typing import Tuple, List, Union, Optional, Dict, Any
import logging
import warnings
from src.utils.logging import get_logger

logger = get_logger(__name__)

def paired_ttest(condition_a: Union[List[float], np.ndarray], 
                condition_b: Union[List[float], np.ndarray],
                alternative: str = 'two-sided') -> Dict[str, Any]:
    """
    Perform a paired t-test between two conditions.
    
    Args:
        condition_a: First condition measurements (e.g., accuracy scores)
        condition_b: Second condition measurements (e.g., accuracy scores)
        alternative: 'two-sided', 'less', or 'greater'
        
    Returns:
        Dictionary with t-statistic, p-value, and confidence interval
    """
    a = np.array(condition_a)
    b = np.array(condition_b)
    
    if len(a) != len(b):
        raise ValueError("Condition arrays must have the same length for paired t-test")
    
    if len(a) < 2:
        raise ValueError("At least 2 samples required for t-test")
    
    # Compute differences
    diff = a - b
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    n = len(diff)
    
    # t-statistic
    if std_diff == 0:
        t_stat = 0.0
    else:
        t_stat = mean_diff / (std_diff / np.sqrt(n))
    
    # p-value using scipy
    t_stat_scipy, p_val = stats.ttest_rel(a, b, alternative=alternative)
    
    # 95% confidence interval for mean difference
    ci_lower, ci_upper = stats.t.interval(
        alpha=0.95,
        df=n-1,
        loc=mean_diff,
        scale=std_diff / np.sqrt(n)
    )
    
    result = {
        't_statistic': float(t_stat_scipy),
        'p_value': float(p_val),
        'mean_difference': float(mean_diff),
        'std_difference': float(std_diff),
        'n_samples': n,
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'alternative': alternative
    }
    
    logger.info(f"Paired t-test: t={t_stat_scipy:.4f}, p={p_val:.4f}, "
               f"mean_diff={mean_diff:.4f}, 95% CI=[{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return result

def wilcoxon_effect_size(condition_a: Union[List[float], np.ndarray], 
                        condition_b: Union[List[float], np.ndarray]) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test and calculate effect size (r).
    
    Args:
        condition_a: First condition measurements
        condition_b: Second condition measurements
        
    Returns:
        Dictionary with statistic, p-value, and effect size r
        
    Note:
        Effect size r = Z / sqrt(N) where Z is the standardized test statistic
        and N is the number of non-zero differences.
        Interpretation: 0.1=small, 0.3=medium, 0.5=large
    """
    a = np.array(condition_a)
    b = np.array(condition_b)
    
    if len(a) != len(b):
        raise ValueError("Condition arrays must have the same length")
    
    if len(a) < 2:
        raise ValueError("At least 2 samples required for Wilcoxon test")
    
    # Wilcoxon signed-rank test
    stat, p_val = stats.wilcoxon(a, b)
    
    # Calculate effect size r
    # Z approximation for Wilcoxon
    n = len(a)
    n_nonzero = np.sum(a != b)
    
    if n_nonzero < 2:
        r_effect_size = 0.0
        z_stat = 0.0
    else:
        # Use scipy's wilcoxon with correction
        # For effect size, we need the Z statistic
        # scipy doesn't directly return Z, so we compute it
        mean_r = n_nonzero * (n_nonzero + 1) / 4
        std_r = np.sqrt(n_nonzero * (n_nonzero + 1) * (2 * n_nonzero + 1) / 24)
        
        if std_r == 0:
            z_stat = 0.0
        else:
            # Calculate rank sum
            diff = a - b
            nonzero_mask = diff != 0
            ranks = stats.rankdata(np.abs(diff[nonzero_mask]))
            rank_sum = np.sum(ranks[diff[nonzero_mask] > 0])
            z_stat = (rank_sum - mean_r) / std_r
        
        r_effect_size = abs(z_stat) / np.sqrt(n_nonzero)
    
    result = {
        'statistic': float(stat),
        'p_value': float(p_val),
        'effect_size_r': float(r_effect_size),
        'z_statistic': float(z_stat),
        'n_samples': n,
        'n_nonzero_differences': int(n_nonzero),
        'interpretation': get_effect_size_interpretation(r_effect_size)
    }
    
    logger.info(f"Wilcoxon test: W={stat:.4f}, p={p_val:.4f}, "
               f"effect_size_r={r_effect_size:.4f} ({result['interpretation']})")
    
    return result

def bootstrap_ci(values: Union[List[float], np.ndarray], 
                ci_level: float = 0.95,
                n_bootstrap: int = 1000,
                random_seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate bootstrap confidence interval for the mean.
    
    Args:
        values: Sample values
        ci_level: Confidence level (default 0.95 for 95% CI)
        n_bootstrap: Number of bootstrap resamples
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with mean, CI bounds, and bootstrap distribution stats
        
    Reference:
        Bootstrap method as described in Efron & Tibshirani (1993)
        Also referenced in arxiv.org/abs/1710.08708
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    values = np.array(values)
    
    if len(values) < 2:
        raise ValueError("At least 2 samples required for bootstrap CI")
    
    n = len(values)
    sample_mean = np.mean(values)
    
    # Bootstrap resampling
    bootstrap_means = []
    for _ in range(n_bootstrap):
        resample = np.random.choice(values, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    bootstrap_means = np.array(bootstrap_means)
    
    # Calculate percentile CI
    alpha = 1 - ci_level
    ci_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    
    result = {
        'sample_mean': float(sample_mean),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'ci_level': ci_level,
        'n_bootstrap': n_bootstrap,
        'bootstrap_std': float(np.std(bootstrap_means)),
        'bootstrap_skewness': float(stats.skew(bootstrap_means))
    }
    
    logger.info(f"Bootstrap CI ({ci_level*100:.0f}%): mean={sample_mean:.4f}, "
               f"CI=[{ci_lower:.4f}, {ci_upper:.4f}], n_resamples={n_bootstrap}")
    
    return result

def get_effect_size_interpretation(r: float) -> str:
    """
    Interpret effect size r according to Cohen's conventions.
    
    Args:
        r: Effect size value
        
    Returns:
        String interpretation
    """
    if r < 0.1:
        return "negligible"
    elif r < 0.3:
        return "small"
    elif r < 0.5:
        return "medium"
    else:
        return "large"

def run_full_statistical_analysis(condition_a: Union[List[float], np.ndarray],
                                 condition_b: Union[List[float], np.ndarray],
                                 alpha: float = 0.05,
                                 random_seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Run comprehensive statistical analysis comparing two conditions.
    
    Args:
        condition_a: First condition measurements
        condition_b: Second condition measurements
        alpha: Significance threshold (default 0.05)
        random_seed: Random seed for bootstrap reproducibility
        
    Returns:
        Dictionary containing all statistical test results
        
    Includes:
        - Paired t-test (t-statistic, p-value, 95% CI)
        - Wilcoxon signed-rank test (W statistic, p-value, effect size r)
        - Bootstrap confidence interval for mean difference
    """
    logger.info(f"Running full statistical analysis (n_a={len(condition_a)}, "
               f"n_b={len(condition_b)}, alpha={alpha})")
    
    results = {
        'paired_ttest': paired_ttest(condition_a, condition_b),
        'wilcoxon': wilcoxon_effect_size(condition_a, condition_b),
        'bootstrap_ci': bootstrap_ci(
            np.array(condition_a) - np.array(condition_b),
            ci_level=0.95,
            n_bootstrap=1000,
            random_seed=random_seed
        ),
        'significance_threshold': alpha,
        'significant_at_alpha': None  # Will be filled below
    }
    
    # Determine significance
    p_ttest = results['paired_ttest']['p_value']
    p_wilcoxon = results['wilcoxon']['p_value']
    
    results['significant_at_alpha'] = {
        'ttest': p_ttest < alpha,
        'wilcoxon': p_wilcoxon < alpha
    }
    
    # Overall conclusion
    if results['significant_at_alpha']['ttest'] or results['significant_at_alpha']['wilcoxon']:
        results['conclusion'] = "Significant difference detected between conditions"
    else:
        results['conclusion'] = "No significant difference detected between conditions"
    
    logger.info(f"Statistical analysis complete. Conclusion: {results['conclusion']}")
    
    return results

def main():
    """
    Main function for standalone testing of statistical functions.
    """
    # Example usage with sample data
    np.random.seed(42)
    condition_a = np.random.normal(loc=0.8, scale=0.1, size=30)
    condition_b = np.random.normal(loc=0.75, scale=0.1, size=30)
    
    print("=== Paired t-test ===")
    ttest_result = paired_ttest(condition_a, condition_b)
    print(f"T-statistic: {ttest_result['t_statistic']:.4f}")
    print(f"P-value: {ttest_result['p_value']:.4f}")
    print(f"95% CI: [{ttest_result['ci_lower']:.4f}, {ttest_result['ci_upper']:.4f}]")
    
    print("\n=== Wilcoxon Signed-Rank Test ===")
    wilcoxon_result = wilcoxon_effect_size(condition_a, condition_b)
    print(f"W-statistic: {wilcoxon_result['statistic']:.4f}")
    print(f"P-value: {wilcoxon_result['p_value']:.4f}")
    print(f"Effect size r: {wilcoxon_result['effect_size_r']:.4f} ({wilcoxon_result['interpretation']})")
    
    print("\n=== Bootstrap Confidence Interval ===")
    diff = condition_a - condition_b
    boot_result = bootstrap_ci(diff, ci_level=0.95, n_bootstrap=1000, random_seed=42)
    print(f"Mean difference: {boot_result['sample_mean']:.4f}")
    print(f"95% CI: [{boot_result['ci_lower']:.4f}, {boot_result['ci_upper']:.4f}]")
    
    print("\n=== Full Statistical Analysis ===")
    full_result = run_full_statistical_analysis(condition_a, condition_b, alpha=0.05, random_seed=42)
    print(f"Conclusion: {full_result['conclusion']}")
    print(f"Significant (t-test): {full_result['significant_at_alpha']['ttest']}")
    print(f"Significant (Wilcoxon): {full_result['significant_at_alpha']['wilcoxon']}")

if __name__ == "__main__":
    main()
