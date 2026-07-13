"""
Statistical analysis module for comparing agent performance.
Implements Fisher's Exact Test (n < 30) or Two-Proportion Z-Test (n >= 30).
"""
import scipy.stats
from typing import Dict, Tuple, Any

from utils.config import get_path
from analysis.log_parser import get_aggregated_counts

def calculate_statistical_significance(baseline_counts: Tuple[int, int], 
                                       augmented_counts: Tuple[int, int]) -> Dict[str, Any]:
    """
    Calculate statistical significance between baseline and augmented success rates.
    
    Args:
        baseline_counts: Tuple of (success, failure) for baseline.
        augmented_counts: Tuple of (success, failure) for augmented.
        
    Returns:
        Dictionary with 'p_value', 'test_type', and 'conclusion'.
    """
    b_success, b_failure = baseline_counts
    a_success, a_failure = augmented_counts
    
    total_baseline = b_success + b_failure
    total_augmented = a_success + a_failure
    
    if total_baseline == 0 or total_augmented == 0:
        return {
            "p_value": None,
            "test_type": "none",
            "conclusion": "Insufficient data to perform statistical test."
        }
    
    total_n = total_baseline + total_augmented
    
    # Construct contingency table for Fisher's Exact
    # [[b_success, b_failure], [a_success, a_failure]]
    table = [[b_success, b_failure], [a_success, a_failure]]
    
    if total_n < 30:
        # Use Fisher's Exact Test
        # two-sided by default
        _, p_value = scipy.stats.fisher_exact(table)
        test_type = "Fisher's Exact Test"
    else:
        # Use Two-Proportion Z-Test
        # proportions: [b_success/total_baseline, a_success/total_augmented]
        # counts: [b_success, a_success]
        # nobs: [total_baseline, total_augmented]
        count = [b_success, a_success]
        nobs = [total_baseline, total_augmented]
        
        # returns (z_statistic, p_value)
        _, p_value = scipy.stats.proportions_ztest(count, nobs)
        test_type = "Two-Proportion Z-Test"
    
    # Determine conclusion based on standard alpha=0.05
    alpha = 0.05
    is_significant = p_value < alpha
    
    if is_significant:
        if a_success / total_augmented > b_success / total_baseline:
            conclusion = f"Augmented agent performed significantly better (p={p_value:.4f})."
        else:
            conclusion = f"Baseline agent performed significantly better (p={p_value:.4f})."
    else:
        conclusion = f"No statistically significant difference detected (p={p_value:.4f})."
    
    return {
        "p_value": float(p_value),
        "test_type": test_type,
        "conclusion": conclusion,
        "is_significant": is_significant
    }

def main():
    """
    Main entry point for statistical analysis.
    Reads logs, computes stats, and prints results.
    """
    try:
        counts = get_aggregated_counts()
        baseline = counts['baseline']
        augmented = counts['augmented']
        
        result = calculate_statistical_significance(baseline, augmented)
        
        print("Statistical Analysis Results:")
        print(f"  Test Type: {result['test_type']}")
        print(f"  P-Value: {result['p_value']}")
        print(f"  Conclusion: {result['conclusion']}")
        
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
