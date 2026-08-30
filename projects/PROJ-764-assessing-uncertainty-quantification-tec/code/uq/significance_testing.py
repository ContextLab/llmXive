"""
Significance testing utilities for UQ methods.

Implements Bootstrap Paired T-Test and Holm-Bonferroni correction for multiple comparisons.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np
from typing import Dict, List, Tuple, Any

# Ensure code directory is in path for imports
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

logger = logging.getLogger(__name__)


def load_ece_scores_by_seed(input_path: str = "results/ece_scores_by_seed.json") -> Dict[str, List[float]]:
    """
    Load ECE scores organized by method and seed.
    
    Expected format:
    {
        "method_name": {
            "42": 0.0123,
            "43": 0.0145,
            "44": 0.0110
        },
        ...
    }
    
    Returns:
        Dict[str, List[float]]: {method_name: [score_seed_42, score_seed_43, score_seed_44]}
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Convert string keys to float lists in consistent order
    result = {}
    for method, scores in data.items():
        # Sort by seed to ensure consistent ordering
        sorted_items = sorted(scores.items(), key=lambda x: int(x[0]))
        result[method] = [float(v) for _, v in sorted_items]
    
    return result


def bootstrap_paired_ttest(
    scores_method_a: List[float],
    scores_method_b: List[float],
    n_resamples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform Bootstrap Paired T-Test to compare two methods.
    
    This test assesses whether the mean difference between paired samples
    (ECE scores across seeds) is statistically significant.
    
    Args:
        scores_method_a: List of ECE scores for method A (ordered by seed)
        scores_method_b: List of ECE scores for method B (same order)
        n_resamples: Number of bootstrap resamples
        alpha: Significance level
        seed: Random seed for reproducibility
        
    Returns:
        Dict with test statistics and p-value
    """
    if len(scores_method_a) != len(scores_method_b):
        raise ValueError("Both methods must have the same number of samples (seeds)")
    
    if len(scores_method_a) < 2:
        raise ValueError("Need at least 2 samples to perform statistical test")
    
    np.random.seed(seed)
    n_samples = len(scores_method_a)
    
    # Calculate observed mean difference
    diff = np.array(scores_method_a) - np.array(scores_method_b)
    observed_diff = np.mean(diff)
    
    # Bootstrap resampling
    bootstrap_diffs = []
    for _ in range(n_resamples):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        resampled_diff = diff[indices]
        bootstrap_diffs.append(np.mean(resampled_diff))
    
    bootstrap_diffs = np.array(bootstrap_diffs)
    
    # Calculate p-value (two-tailed test)
    # p-value = proportion of bootstrap samples where |diff| >= |observed_diff|
    p_value = np.mean(np.abs(bootstrap_diffs) >= np.abs(observed_diff))
    
    # Calculate confidence interval (95%)
    ci_lower = np.percentile(bootstrap_diffs, 2.5)
    ci_upper = np.percentile(bootstrap_diffs, 97.5)
    
    return {
        "observed_mean_difference": float(observed_diff),
        "bootstrap_mean": float(np.mean(bootstrap_diffs)),
        "bootstrap_std": float(np.std(bootstrap_diffs)),
        "p_value": float(p_value),
        "ci_95_lower": float(ci_lower),
        "ci_95_upper": float(ci_upper),
        "n_resamples": n_resamples,
        "n_samples": n_samples
    }


def holm_bonferroni_correction(
    p_values: Dict[str, float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Holm-Bonferroni correction for multiple comparisons.
    
    This is a step-down procedure that controls the family-wise error rate
    while being more powerful than the standard Bonferroni correction.
    
    Steps:
    1. Sort p-values in ascending order
    2. For each p-value at position i (0-indexed), compare to alpha / (m - i)
    3. Reject null hypothesis for all hypotheses up to the first non-rejection
    
    Args:
        p_values: Dict mapping comparison name to raw p-value
        alpha: Family-wise error rate (default 0.05)
        
    Returns:
        Dict with corrected results including adjusted p-values and rejection decisions
    """
    if not p_values:
        return {
            "corrected": False,
            "reason": "No p-values provided",
            "results": []
        }
    
    m = len(p_values)  # Total number of comparisons
    
    # Sort p-values by value, keeping track of original comparison names
    sorted_items = sorted(p_values.items(), key=lambda x: x[1])
    
    results = []
    rejected = []
    adjusted_p_values = {}
    
    for i, (comparison, p_val) in enumerate(sorted_items):
        # Holm-Bonferroni threshold: alpha / (m - i)
        threshold = alpha / (m - i)
        is_significant = p_val < threshold
        
        # Calculate adjusted p-value for reporting
        # Adjusted p-value = max(p * (m - i), previous_adjusted)
        adjusted = p_val * (m - i)
        
        results.append({
            "comparison": comparison,
            "raw_p_value": float(p_val),
            "holm_threshold": float(threshold),
            "adjusted_p_value": float(adjusted),
            "rejected": bool(is_significant),
            "step": i + 1
        })
        
        adjusted_p_values[comparison] = adjusted
        
        if is_significant:
            rejected.append(comparison)
        else:
            # Stop here - no further hypotheses can be rejected
            break
    
    return {
        "method": "Holm-Bonferroni",
        "family_wise_error_rate": float(alpha),
        "total_comparisons": m,
        "significant_comparisons": len(rejected),
        "rejected_hypotheses": rejected,
        "adjusted_p_values": adjusted_p_values,
        "results": results
    }


def run_significance_tests(
    ece_scores_path: str = "results/ece_scores_by_seed.json",
    output_path: str = "results/significance_test_results.json",
    n_resamples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run full significance testing pipeline:
    1. Load ECE scores by seed
    2. Perform pairwise Bootstrap Paired T-Tests between all methods
    3. Apply Holm-Bonferroni correction for multiple comparisons
    4. Save results to JSON
    
    Args:
        ece_scores_path: Path to ECE scores file
        output_path: Path for output results
        n_resamples: Number of bootstrap resamples
        alpha: Significance level
        seed: Random seed
        
    Returns:
        Complete results dictionary
    """
    logger.info(f"Loading ECE scores from {ece_scores_path}")
    ece_data = load_ece_scores_by_seed(ece_scores_path)
    
    methods = list(ece_data.keys())
    if len(methods) < 2:
        raise ValueError(f"Need at least 2 methods to compare, found {len(methods)}")
    
    logger.info(f"Comparing methods: {methods}")
    
    # Perform all pairwise comparisons
    pairwise_results = {}
    p_values = {}
    
    for i, method_a in enumerate(methods):
        for method_b in methods[i+1:]:
            comparison_name = f"{method_a}_vs_{method_b}"
            logger.info(f"Running test: {comparison_name}")
            
            test_result = bootstrap_paired_ttest(
                ece_data[method_a],
                ece_data[method_b],
                n_resamples=n_resamples,
                alpha=alpha,
                seed=seed
            )
            
            pairwise_results[comparison_name] = test_result
            p_values[comparison_name] = test_result["p_value"]
    
    # Apply Holm-Bonferroni correction
    logger.info(f"Applying Holm-Bonferroni correction with alpha={alpha}")
    correction_result = holm_bonferroni_correction(p_values, alpha=alpha)
    
    # Compile final results
    final_results = {
        "test_type": "Bootstrap Paired T-Test with Holm-Bonferroni Correction",
        "parameters": {
            "n_resamples": n_resamples,
            "alpha": alpha,
            "seed": seed,
            "seeds_used": [42, 43, 44]
        },
        "methods_compared": methods,
        "pairwise_tests": pairwise_results,
        "holm_bonferroni_correction": correction_result,
        "summary": {
            "total_comparisons": len(pairwise_results),
            "significant_after_correction": len(correction_result["rejected_hypotheses"]),
            "significant_methods": correction_result["rejected_hypotheses"]
        }
    }
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return final_results


def main():
    """CLI entry point for significance testing."""
    parser = argparse.ArgumentParser(
        description="Run significance tests on UQ method ECE scores"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="results/ece_scores_by_seed.json",
        help="Path to ECE scores by seed JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/significance_test_results.json",
        help="Path for output results JSON"
    )
    parser.add_argument(
        "--n-resamples",
        type=int,
        default=1000,
        help="Number of bootstrap resamples"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_significance_tests(
            ece_scores_path=args.input,
            output_path=args.output,
            n_resamples=args.n_resamples,
            alpha=args.alpha,
            seed=args.seed
        )
        
        print(f"\nSignificance Testing Complete")
        print(f"Total comparisons: {results['summary']['total_comparisons']}")
        print(f"Significant after correction: {results['summary']['significant_after_correction']}")
        if results['summary']['significant_methods']:
            print(f"Significant comparisons: {', '.join(results['summary']['significant_methods'])}")
        else:
            print("No significant differences found after correction.")
        
    except Exception as e:
        logger.error(f"Significance testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()