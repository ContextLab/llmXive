"""
Statistical testing utilities for model comparison.
Implements Wilcoxon signed-rank test for paired comparisons of model performance.
"""
import numpy as np
from scipy import stats
import logging
from typing import List, Tuple, Dict, Any

from code.utils.logger import get_logger

logger = get_logger("stats")

def wilcoxon_test(
    sample_a: List[float],
    sample_b: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test to compare two paired samples.
    
    This test is non-parametric and does not assume normality of the data,
    making it suitable for comparing model performance across different seeds.
    
    Args:
        sample_a: First sample (e.g., CNN MAEs).
        sample_b: Second sample (e.g., Linear Regression MAEs).
        alpha: Significance level (default 0.05).
        
    Returns:
        Dictionary containing:
            - 'p_value': p-value from the test
            - 'statistic': test statistic
            - 'significant': boolean indicating if p < alpha
    """
    if len(sample_a) != len(sample_b):
        raise ValueError("Samples must be of equal length for paired Wilcoxon test")
    
    if len(sample_a) < 2:
        raise ValueError("Need at least 2 samples for Wilcoxon test")
    
    # Convert to numpy arrays
    a = np.array(sample_a)
    b = np.array(sample_b)
    
    # Perform Wilcoxon signed-rank test
    # zero_method='wilcox' is the default behavior
    statistic, p_value = stats.wilcoxon(a, b)
    
    significant = p_value < alpha
    
    logger.info(f"Wilcoxon test results: statistic={statistic:.4f}, p_value={p_value:.4f}, significant={significant}")
    
    return {
        'p_value': float(p_value),
        'statistic': float(statistic),
        'significant': significant
    }

def aggregate_mae_distributions(
    mae_dict: Dict[str, List[float]]
) -> Dict[str, Dict[str, float]]:
    """
    Compute summary statistics for MAE distributions.
    
    Args:
        mae_dict: Dictionary mapping model names to lists of MAE values.
        
    Returns:
        Dictionary with mean, std, min, max for each model.
    """
    summary = {}
    for model, maes in mae_dict.items():
        if len(maes) > 0:
            summary[model] = {
                'mean': float(np.mean(maes)),
                'std': float(np.std(maes)),
                'min': float(np.min(maes)),
                'max': float(np.max(maes))
            }
        else:
            summary[model] = {
                'mean': None,
                'std': None,
                'min': None,
                'max': None
            }
    return summary

def main():
    """Test the statistical functions."""
    # Example usage
    cnn_maes = [0.15, 0.14, 0.16, 0.13, 0.15]
    linear_maes = [0.25, 0.24, 0.26, 0.23, 0.25]
    
    result = wilcoxon_test(cnn_maes, linear_maes)
    print(f"Wilcoxon test result: {result}")
    
    summary = aggregate_mae_distributions({
        'cnn': cnn_maes,
        'linear': linear_maes
    })
    print(f"Summary statistics: {summary}")

if __name__ == '__main__':
    main()
