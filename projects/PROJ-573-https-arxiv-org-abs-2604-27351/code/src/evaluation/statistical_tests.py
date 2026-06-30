import numpy as np
from scipy import stats
from typing import Tuple, List, Union, Optional, Dict, Any
import logging
import warnings
from src.utils.logging import get_logger

logger = get_logger(__name__)

def paired_ttest(condition_a: Union[List[float], np.ndarray],
                 condition_b: Union[List[float], np.ndarray],
                 alternative: str = 'two-sided') -> Dict[str, float]:
    """
    Perform a paired t-test between two conditions.
    
    Args:
        condition_a: First condition measurements (e.g., accuracy scores)
        condition_b: Second condition measurements
        alternative: 'two-sided', 'less', or 'more'
        
    Returns:
        Dictionary with t-statistic and p-value
    """
    if len(condition_a) != len(condition_b):
        raise ValueError("Conditions must have equal length for paired t-test")
    if len(condition_a) < 2:
        raise ValueError("Need at least 2 samples for t-test")
        
    t_stat, p_val = stats.ttest_rel(condition_a, condition_b, alternative=alternative)
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val)
    }

def wilcoxon_effect_size(condition_a: Union[List[float], np.ndarray],
                         condition_b: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Perform Wilcoxon signed-rank test and calculate effect size (r).
    
    Effect size r = Z / sqrt(N)
    
    Args:
        condition_a: First condition measurements
        condition_b: Second condition measurements
        
    Returns:
        Dictionary with Z-statistic, p-value, and effect size r
    """
    if len(condition_a) != len(condition_b):
        raise ValueError("Conditions must have equal length for Wilcoxon test")
    if len(condition_a) < 2:
        raise ValueError("Need at least 2 samples for Wilcoxon test")
        
    # Wilcoxon signed-rank test
    stat, p_val = stats.wilcoxon(condition_a, condition_b)
    
    # Calculate effect size r = Z / sqrt(N)
    # scipy doesn't directly return Z, but we can approximate or use the statistic
    # For large samples, Wilcoxon statistic approximates normal distribution
    n = len(condition_a)
    # Z approximation: Z = (stat - n*(n+1)/4) / sqrt(n*(n+1)*(2*n+1)/24)
    if n > 10:
        mean_stat = n * (n + 1) / 4
        std_stat = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        z_stat = (stat - mean_stat) / std_stat
    else:
        # For small samples, use the statistic directly as a proxy
        # This is less precise but avoids division by zero issues
        z_stat = stat / np.sqrt(n) if n > 0 else 0
        
    effect_size = abs(z_stat) / np.sqrt(n) if n > 0 else 0.0
    
    return {
        'z_statistic': float(z_stat),
        'p_value': float(p_val),
        'effect_size_r': float(effect_size)
    }

def bootstrap_ci(values: Union[List[float], np.ndarray],
                 confidence_level: float = 0.95,
                 n_iterations: int = 10000,
                 random_seed: Optional[int] = None) -> Dict[str, float]:
    """
    Calculate bootstrap confidence interval for the mean.
    
    Args:
        values: Sample values
        confidence_level: Confidence level (e.g., 0.95 for 95% CI)
        n_iterations: Number of bootstrap iterations
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with mean, ci_lower, ci_upper
    """
    if len(values) < 2:
        raise ValueError("Need at least 2 samples for bootstrap CI")
        
    if random_seed is not None:
        np.random.seed(random_seed)
        
    n = len(values)
    bootstrap_means = []
    
    for _ in range(n_iterations):
        # Resample with replacement
        sample = np.random.choice(values, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))
        
    bootstrap_means = np.array(bootstrap_means)
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    mean_val = np.mean(values)
    
    return {
        'mean': float(mean_val),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper)
    }

def get_effect_size_interpretation(effect_size: float) -> str:
    """
    Interpret effect size magnitude (Cohen's d or r).
    
    Args:
        effect_size: Effect size value
        
    Returns:
        String interpretation
    """
    if effect_size < 0.1:
        return "negligible"
    elif effect_size < 0.3:
        return "small"
    elif effect_size < 0.5:
        return "medium"
    else:
        return "large"

def run_full_statistical_analysis(condition_a: Union[List[float], np.ndarray],
                                  condition_b: Union[List[float], np.ndarray],
                                  alpha: float = 0.05,
                                  confidence_level: float = 0.95,
                                  random_seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Run complete statistical analysis comparing two conditions.
    
    Includes:
    - Paired t-test (t-statistic, p-value)
    - Wilcoxon signed-rank test with effect size
    - Bootstrap confidence interval for mean difference
    
    Args:
        condition_a: First condition measurements
        condition_b: Second condition measurements
        alpha: Significance threshold (default 0.05)
        confidence_level: Confidence level for CI (default 0.95)
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with all statistical results
    """
    # Validate inputs
    if len(condition_a) != len(condition_b):
        raise ValueError("Conditions must have equal length")
    if len(condition_a) < 2:
        raise ValueError("Need at least 2 samples for statistical analysis")
        
    # Calculate mean difference for bootstrap
    differences = np.array(condition_a) - np.array(condition_b)
    
    # Run analyses
    ttest_result = paired_ttest(condition_a, condition_b)
    wilcoxon_result = wilcoxon_effect_size(condition_a, condition_b)
    bootstrap_result = bootstrap_ci(differences, confidence_level, 10000, random_seed)
    
    # Determine significance
    sig_ttest = ttest_result['p_value'] < alpha
    sig_wilcoxon = wilcoxon_result['p_value'] < alpha
    
    # Interpret effect size
    effect_interpretation = get_effect_size_interpretation(wilcoxon_result['effect_size_r'])
    
    return {
        'n_samples': len(condition_a),
        'mean_a': float(np.mean(condition_a)),
        'mean_b': float(np.mean(condition_b)),
        'mean_difference': float(np.mean(differences)),
        't_test': {
            't_statistic': ttest_result['t_statistic'],
            'p_value': ttest_result['p_value'],
            'significant': sig_ttest
        },
        'wilcoxon': {
            'z_statistic': wilcoxon_result['z_statistic'],
            'p_value': wilcoxon_result['p_value'],
            'effect_size': wilcoxon_result['effect_size_r'],
            'effect_size_interpretation': effect_interpretation,
            'significant': sig_wilcoxon
        },
        'bootstrap_ci': {
            'mean_difference': bootstrap_result['mean'],
            'ci_lower': bootstrap_result['ci_lower'],
            'ci_upper': bootstrap_result['ci_upper'],
            'confidence_level': confidence_level
        },
        'alpha': alpha,
        'conclusion': {
            'significant_diff': sig_ttest or sig_wilcoxon,
            'primary_outcome': 'wilcoxon_effect_size',
            'effect_size': wilcoxon_result['effect_size_r'],
            'ci_95': [bootstrap_result['ci_lower'], bootstrap_result['ci_upper']]
        }
    }

def main():
    """Example usage of statistical analysis functions."""
    # Example: Compare two conditions with small sample
    cond_a = [0.85, 0.87, 0.82, 0.89, 0.84]
    cond_b = [0.80, 0.82, 0.79, 0.83, 0.81]
    
    results = run_full_statistical_analysis(cond_a, cond_b, alpha=0.05, random_seed=42)
    
    logger.info("Statistical Analysis Results:")
    logger.info(f"  N samples: {results['n_samples']}")
    logger.info(f"  Mean A: {results['mean_a']:.4f}")
    logger.info(f"  Mean B: {results['mean_b']:.4f}")
    logger.info(f"  Mean Difference: {results['mean_difference']:.4f}")
    logger.info(f"  T-test p-value: {results['t_test']['p_value']:.4f}")
    logger.info(f"  Wilcoxon p-value: {results['wilcoxon']['p_value']:.4f}")
    logger.info(f"  Wilcoxon Effect Size (r): {results['wilcoxon']['effect_size']:.4f}")
    logger.info(f"  Effect Size Interpretation: {results['wilcoxon']['effect_size_interpretation']}")
    logger.info(f"  95% CI: [{results['bootstrap_ci']['ci_lower']:.4f}, {results['bootstrap_ci']['ci_upper']:.4f}]")
    logger.info(f"  Significant: {results['conclusion']['significant_diff']}")
    
    return results

if __name__ == "__main__":
    main()
