"""
Statistical analysis module for llmXive follow-up project.

Implements the one-tailed Mann-Whitney U test as required by FR-005.
This module compares the memory gap scores of the Text Agent against
the Baseline Agent to determine if the Text Agent significantly outperforms
the Baseline (lower memory gap scores).
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional
import json
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

def mann_whitney_u_test(
    sample_a: List[float], 
    sample_b: List[float], 
    alternative: str = 'less'
) -> Dict[str, Any]:
    """
    Perform a one-tailed Mann-Whitney U test.
    
    This test evaluates whether the distribution of sample_a is stochastically
    smaller than sample_b (i.e., Text Agent has lower memory gap scores than Baseline).
    
    Args:
        sample_a: List of scores from the Text Agent (lower is better).
        sample_b: List of scores from the Baseline Agent.
        alternative: Direction of the test. 
            'less' = sample_a is stochastically smaller than sample_b (Text Agent better).
            'greater' = sample_a is stochastically larger than sample_b.
            'two-sided' = distributions are different.
            
    Returns:
        Dictionary containing:
            - 'statistic': The Mann-Whitney U statistic.
            - 'p_value': The p-value for the test.
            - 'alternative': The alternative hypothesis tested.
            - 'conclusion': String interpretation of the result.
            - 'n_a': Number of samples in group A.
            - 'n_b': Number of samples in group B.
            
    Raises:
        ValueError: If input lists are empty or have fewer than 2 samples.
        RuntimeError: If the statistical test fails.
    """
    if len(sample_a) < 2 or len(sample_b) < 2:
        raise ValueError(
            f"Both samples must have at least 2 elements. "
            f"Got len(sample_a)={len(sample_a)}, len(sample_b)={len(sample_b)}."
        )
    
    if not sample_a or not sample_b:
        raise ValueError("Input samples cannot be empty.")
    
    try:
        # Convert to numpy arrays for robustness
        arr_a = np.array(sample_a, dtype=float)
        arr_b = np.array(sample_b, dtype=float)
        
        # Check for NaN or Inf values
        if np.any(np.isnan(arr_a)) or np.any(np.isnan(arr_b)):
            raise ValueError("Input samples contain NaN values.")
        if np.any(np.isinf(arr_a)) or np.any(np.isinf(arr_b)):
            raise ValueError("Input samples contain Inf values.")
        
        # Perform the test
        # Note: scipy.stats.mannwhitneyu uses 'alternative' parameter in newer versions
        # For older versions, we might need to handle 'less' vs 'greater' manually
        u_stat, p_val = stats.mannwhitneyu(
            arr_a, 
            arr_b, 
            alternative=alternative,
            use_continuity=True
        )
        
        # Determine conclusion
        alpha = 0.05
        is_significant = p_val < alpha
        
        if alternative == 'less':
            if is_significant:
                conclusion = (
                    f"Significant evidence (p={p_val:.6f}) that Text Agent memory gap "
                    f"scores are lower than Baseline scores (one-tailed test). "
                    f"Text Agent outperforms Baseline."
                )
            else:
                conclusion = (
                    f"No significant evidence (p={p_val:.6f}) that Text Agent memory gap "
                    f"scores are lower than Baseline scores (one-tailed test)."
                )
        elif alternative == 'greater':
            if is_significant:
                conclusion = (
                    f"Significant evidence (p={p_val:.6f}) that Text Agent memory gap "
                    f"scores are higher than Baseline scores (one-tailed test)."
                )
            else:
                conclusion = (
                    f"No significant evidence (p={p_val:.6f}) that Text Agent memory gap "
                    f"scores are higher than Baseline scores (one-tailed test)."
                )
        else:
            if is_significant:
                conclusion = (
                    f"Significant difference (p={p_val:.6f}) between Text Agent and Baseline "
                    f"memory gap scores (two-tailed test)."
                )
            else:
                conclusion = (
                    f"No significant difference (p={p_val:.6f}) between Text Agent and Baseline "
                    f"memory gap scores (two-tailed test)."
                )
        
        return {
            'statistic': float(u_stat),
            'p_value': float(p_val),
            'alternative': alternative,
            'conclusion': conclusion,
            'n_a': int(len(arr_a)),
            'n_b': int(len(arr_b)),
            'alpha': alpha,
            'is_significant': bool(is_significant)
        }
        
    except Exception as e:
        logger.error(f"Mann-Whitney U test failed: {str(e)}")
        raise RuntimeError(f"Statistical test execution failed: {str(e)}") from e


def calculate_confidence_interval(
    sample_a: List[float], 
    sample_b: List[float], 
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Calculate the confidence interval for the difference in medians between two samples.
    
    Uses bootstrap resampling to estimate the confidence interval.
    
    Args:
        sample_a: List of scores from the Text Agent.
        sample_b: List of scores from the Baseline Agent.
        confidence_level: Confidence level (e.g., 0.95 for 95% CI).
        
    Returns:
        Dictionary containing:
            - 'median_a': Median of sample A.
            - 'median_b': Median of sample B.
            - 'median_diff': Median of (A - B).
            - 'ci_lower': Lower bound of the confidence interval.
            - 'ci_upper': Upper bound of the confidence interval.
    """
    if len(sample_a) < 2 or len(sample_b) < 2:
        raise ValueError("Both samples must have at least 2 elements for CI calculation.")
    
    arr_a = np.array(sample_a)
    arr_b = np.array(sample_b)
    
    n_bootstrap = 10000
    rng = np.random.default_rng(42)  # Fixed seed for reproducibility
    
    diff_means = []
    for _ in range(n_bootstrap):
        # Bootstrap resample
        boot_a = rng.choice(arr_a, size=len(arr_a), replace=True)
        boot_b = rng.choice(arr_b, size=len(arr_b), replace=True)
        
        # Calculate difference in medians
        diff = np.median(boot_a) - np.median(boot_b)
        diff_means.append(diff)
    
    alpha = 1 - confidence_level
    ci_lower = np.percentile(diff_means, 100 * alpha / 2)
    ci_upper = np.percentile(diff_means, 100 * (1 - alpha / 2))
    
    return {
        'median_a': float(np.median(arr_a)),
        'median_b': float(np.median(arr_b)),
        'median_diff': float(np.median(arr_a) - np.median(arr_b)),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'confidence_level': confidence_level
    }


def aggregate_results(
    text_scores: List[float], 
    baseline_scores: List[float],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Aggregate statistical results for the Memory Gap metric.
    
    Performs Mann-Whitney U test and calculates confidence intervals,
    then returns a comprehensive summary.
    
    Args:
        text_scores: List of memory gap scores from the Text Agent.
        baseline_scores: List of memory gap scores from the Baseline Agent.
        output_path: Optional path to save results as JSON.
        
    Returns:
        Dictionary containing all statistical results.
    """
    logger.info(f"Aggregating results: {len(text_scores)} text scores, {len(baseline_scores)} baseline scores")
    
    # Calculate descriptive statistics
    text_mean = float(np.mean(text_scores))
    text_std = float(np.std(text_scores))
    baseline_mean = float(np.mean(baseline_scores))
    baseline_std = float(np.std(baseline_scores))
    
    # Perform Mann-Whitney U test (one-tailed, expecting Text Agent < Baseline)
    mw_result = mann_whitney_u_test(text_scores, baseline_scores, alternative='less')
    
    # Calculate confidence interval
    ci_result = calculate_confidence_interval(text_scores, baseline_scores)
    
    summary = {
        'text_agent': {
            'mean': text_mean,
            'std': text_std,
            'n': len(text_scores),
            'median': float(np.median(text_scores))
        },
        'baseline_agent': {
            'mean': baseline_mean,
            'std': baseline_std,
            'n': len(baseline_scores),
            'median': float(np.median(baseline_scores))
        },
        'mann_whitney_u': mw_result,
        'confidence_interval': ci_result,
        'conclusion': mw_result['conclusion']
    }
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Results saved to {output_path}")
    
    return summary


def run_stats_test() -> bool:
    """
    Run unit tests for the stats module.
    
    Returns:
        True if all tests pass, False otherwise.
    """
    logger.info("Running stats module unit tests...")
    
    # Test 1: Basic functionality with known values
    try:
        # Create samples where A is clearly smaller than B
        sample_a = [1.0, 1.5, 2.0, 2.5, 3.0]
        sample_b = [4.0, 4.5, 5.0, 5.5, 6.0]
        
        result = mann_whitney_u_test(sample_a, sample_b, alternative='less')
        
        assert result['p_value'] < 0.05, "Expected significant result for clearly different samples"
        assert result['is_significant'] is True
        assert 'Text Agent outperforms Baseline' in result['conclusion']
        
        logger.info("Test 1 passed: Basic functionality with known values")
    except Exception as e:
        logger.error(f"Test 1 failed: {e}")
        return False
    
    # Test 2: Edge case - identical values
    try:
        sample_a = [3.0, 3.0, 3.0, 3.0]
        sample_b = [3.0, 3.0, 3.0, 3.0]
        
        result = mann_whitney_u_test(sample_a, sample_b, alternative='less')
        
        # With identical values, p-value should be high (not significant)
        assert result['p_value'] > 0.05, "Expected non-significant result for identical samples"
        assert result['is_significant'] is False
        
        logger.info("Test 2 passed: Identical values edge case")
    except Exception as e:
        logger.error(f"Test 2 failed: {e}")
        return False
    
    # Test 3: Error handling - empty input
    try:
        mann_whitney_u_test([], [1.0, 2.0, 3.0])
        logger.error("Test 3 failed: Should have raised ValueError for empty input")
        return False
    except ValueError:
        logger.info("Test 3 passed: Empty input raises ValueError")
    except Exception as e:
        logger.error(f"Test 3 failed with unexpected error: {e}")
        return False
    
    # Test 4: Error handling - single sample
    try:
        mann_whitney_u_test([1.0], [2.0, 3.0, 4.0])
        logger.error("Test 4 failed: Should have raised ValueError for single sample")
        return False
    except ValueError:
        logger.info("Test 4 passed: Single sample raises ValueError")
    except Exception as e:
        logger.error(f"Test 4 failed with unexpected error: {e}")
        return False
    
    # Test 5: Confidence interval calculation
    try:
        sample_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        sample_b = [6.0, 7.0, 8.0, 9.0, 10.0]
        
        ci_result = calculate_confidence_interval(sample_a, sample_b)
        
        assert 'ci_lower' in ci_result
        assert 'ci_upper' in ci_result
        assert ci_result['median_a'] < ci_result['median_b']
        
        logger.info("Test 5 passed: Confidence interval calculation")
    except Exception as e:
        logger.error(f"Test 5 failed: {e}")
        return False
    
    logger.info("All stats module tests passed!")
    return True


def main():
    """
    Main entry point for running statistical analysis.
    
    This function can be called directly to:
    1. Run unit tests if no arguments are provided.
    2. Aggregate results from JSON files if arguments are provided.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Statistical analysis for llmXive project')
    parser.add_argument('--test', action='store_true', help='Run unit tests')
    parser.add_argument('--text-input', type=str, help='Path to JSON file with text agent scores')
    parser.add_argument('--baseline-input', type=str, help='Path to JSON file with baseline agent scores')
    parser.add_argument('--output', type=str, help='Path to save results JSON')
    
    args = parser.parse_args()
    
    if args.test:
        success = run_stats_test()
        if success:
            print("All tests passed.")
            exit(0)
        else:
            print("Some tests failed.")
            exit(1)
    
    if args.text_input and args.baseline_input:
        # Load scores from JSON files
        try:
            with open(args.text_input, 'r') as f:
                text_data = json.load(f)
                text_scores = [item['memory_gap_score'] for item in text_data]
            
            with open(args.baseline_input, 'r') as f:
                baseline_data = json.load(f)
                baseline_scores = [item['memory_gap_score'] for item in baseline_data]
            
            # Aggregate results
            summary = aggregate_results(text_scores, baseline_scores, args.output)
            
            print(json.dumps(summary, indent=2))
            
        except Exception as e:
            logger.error(f"Failed to process input files: {e}")
            exit(1)
    else:
        parser.print_help()
        exit(1)


if __name__ == '__main__':
    main()