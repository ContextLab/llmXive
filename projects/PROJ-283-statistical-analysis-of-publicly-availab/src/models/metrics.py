"""
Model metrics and statistical tests module.
"""
import numpy as np
from typing import List, Dict, Any
import pandas as pd

def calculate_fdr_corrected_pvalues(pvalues: List[float], 
                                   alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        pvalues: List of raw p-values
        alpha: Significance level
    
    Returns:
        Dictionary with corrected p-values and significance flags
    """
    n = len(pvalues)
    if n == 0:
        return {'corrected_pvalues': [], 'significant': []}
    
    # Sort p-values
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = np.array(pvalues)[sorted_indices]
    
    # Calculate BH critical values
    critical_values = (np.arange(1, n + 1) / n) * alpha
    
    # Find the largest k where p(k) <= critical(k)
    significant_mask = sorted_pvalues <= critical_values
    if not significant_mask.any():
        corrected_pvalues = np.ones(n)
        significant = np.zeros(n, dtype=bool)
    else:
        k = np.where(significant_mask)[0][-1]
        threshold = sorted_pvalues[k]
        
        # Calculate corrected p-values
        corrected_pvalues = np.minimum(1, sorted_pvalues * n / (np.arange(1, n + 1) + 1e-10))
        
        # Ensure monotonicity
        for i in range(n - 2, -1, -1):
            corrected_pvalues[i] = min(corrected_pvalues[i], corrected_pvalues[i + 1])
        
        significant = corrected_pvalues <= alpha
    
    # Restore original order
    original_order = np.argsort(sorted_indices)
    corrected_pvalues = corrected_pvalues[original_order]
    significant = significant[original_order]
    
    return {
        'corrected_pvalues': corrected_pvalues.tolist(),
        'significant': significant.tolist(),
        'alpha': alpha
    }

def calculate_wald_ztest(coefficient: float, standard_error: float) -> float:
    """
    Calculate Wald Z-statistic.
    
    Args:
        coefficient: Estimated coefficient
        standard_error: Standard error of the coefficient
    
    Returns:
        Z-statistic value
    """
    if standard_error == 0:
        return np.inf
    return coefficient / standard_error

def calculate_f_statistic(r_squared: float, n: int, p: int) -> float:
    """
    Calculate F-statistic for overall model significance.
    
    Args:
        r_squared: R-squared value
        n: Number of observations
        p: Number of predictors (excluding intercept)
    
    Returns:
        F-statistic value
    """
    if p == 0 or n <= p + 1:
        return np.nan
    
    numerator = r_squared / p
    denominator = (1 - r_squared) / (n - p - 1)
    return numerator / denominator

def main():
    """Main entry point for CLI metrics calculation."""
    # Example usage
    pvalues = [0.01, 0.03, 0.05, 0.10, 0.20]
    result = calculate_fdr_corrected_pvalues(pvalues)
    print(f"Original p-values: {pvalues}")
    print(f"Corrected p-values: {result['corrected_pvalues']}")
    print(f"Significant: {result['significant']}")

if __name__ == "__main__":
    main()
