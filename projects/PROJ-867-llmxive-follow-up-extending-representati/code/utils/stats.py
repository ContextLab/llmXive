"""
Statistical analysis utilities for llmXive pipeline.

Implements McNemar's test and Wilcoxon signed-rank test using scipy.stats
for comparing model performance metrics.
"""
import numpy as np
from scipy.stats import wilcoxon, chi2_contingency
from typing import List, Tuple, Dict, Any, Optional
import json
from pathlib import Path


def run_mcnemar_test(
    rf_correct: int,
    rf_incorrect_but_baseline_correct: int,
    baseline_correct_but_rf_incorrect: int,
    both_incorrect: int
) -> Dict[str, Any]:
    """
    Perform McNemar's test for paired nominal data.
    
    This test determines if there is a significant difference between two
    classification models on the same dataset.
    
    Args:
        rf_correct: Count where both RF and Baseline are correct
        rf_incorrect_but_baseline_correct: Count where RF is wrong, Baseline is right
        baseline_correct_but_rf_incorrect: Count where RF is right, Baseline is wrong
        both_incorrect: Count where both models are wrong
        
    Returns:
        Dictionary containing chi-squared statistic, p-value, and significance decision
    """
    # Construct the 2x2 contingency table
    # Rows: RF (Correct, Incorrect)
    # Cols: Baseline (Correct, Incorrect)
    contingency_table = np.array([
        [rf_correct, rf_incorrect_but_baseline_correct],
        [baseline_correct_but_rf_incorrect, both_incorrect]
    ])
    
    # Perform McNemar's test using chi2_contingency with correction
    # Note: scipy doesn't have a direct mcnemar function, so we use chi2 with correction
    # For McNemar, we focus on the discordant pairs (off-diagonal elements)
    discordant_sum = rf_incorrect_but_baseline_correct + baseline_correct_but_rf_incorrect
    
    if discordant_sum == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "message": "No discordant pairs found, cannot compute test"
        }
    
    # McNemar's chi-squared statistic with continuity correction
    # Formula: (|b - c| - 1)^2 / (b + c)
    b = rf_incorrect_but_baseline_correct
    c = baseline_correct_but_rf_incorrect
    chi2_stat = (abs(b - c) - 1) ** 2 / discordant_sum
    
    # Calculate p-value using chi-squared distribution with 1 degree of freedom
    # Using the survival function (1 - cdf)
    from scipy.stats import chi2
    p_value = chi2.sf(chi2_stat, df=1)
    
    return {
        "statistic": float(chi2_stat),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "discordant_pairs": discordant_sum,
        "method": "McNemar's test with continuity correction"
    }


def run_wilcoxon_signed_rank_test(
    rf_scores: List[float],
    baseline_scores: List[float]
) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test for paired samples.
    
    This non-parametric test determines if there is a significant difference
    between two related samples (e.g., performance of two models on the same data).
    
    Args:
        rf_scores: List of performance scores for the RF model
        baseline_scores: List of performance scores for the baseline model
        
    Returns:
        Dictionary containing test statistic, p-value, and significance decision
    """
    if len(rf_scores) != len(baseline_scores):
        raise ValueError("RF scores and baseline scores must have the same length")
    
    if len(rf_scores) < 2:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "message": "Insufficient data for Wilcoxon test (need at least 2 pairs)"
        }
    
    # Perform Wilcoxon signed-rank test
    statistic, p_value = wilcoxon(rf_scores, baseline_scores)
    
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "n_pairs": len(rf_scores),
        "method": "Wilcoxon signed-rank test"
    }


def aggregate_and_test(
    results_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Load aggregated scores from JSON and perform statistical tests.
    
    Expected JSON format:
    {
        "seeds": [
            {"seed": 0, "rf_score": 0.85, "baseline_score": 0.82},
            {"seed": 1, "rf_score": 0.88, "baseline_score": 0.84},
            ...
        ]
    }
    
    Args:
        results_path: Path to aggregated scores JSON file
        output_path: Path to write results
        
    Returns:
        Dictionary containing all test results
    """
    # Load results
    results_file = Path(results_path)
    if not results_file.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    # Extract scores
    rf_scores = [seed_data['rf_score'] for seed_data in data['seeds']]
    baseline_scores = [seed_data['baseline_score'] for seed_data in data['seeds']]
    
    # Run Wilcoxon test
    wilcoxon_result = run_wilcoxon_signed_rank_test(rf_scores, baseline_scores)
    
    # For McNemar, we need contingency table data
    # If available in the data, use it; otherwise, skip
    mcnemar_result = None
    if 'contingency' in data:
        contingency = data['contingency']
        mcnemar_result = run_mcnemar_test(
            rf_correct=contingency['both_correct'],
            rf_incorrect_but_baseline_correct=contingency['rf_wrong_baseline_right'],
            baseline_correct_but_rf_incorrect=contingency['rf_right_baseline_wrong'],
            both_incorrect=contingency['both_wrong']
        )
    
    # Compile results
    results = {
        "wilcoxon_test": wilcoxon_result,
        "wilcoxon_interpretation": (
            "RF model performs significantly better" if wilcoxon_result['significant'] and wilcoxon_result['statistic'] > 0
            else "Baseline model performs significantly better" if wilcoxon_result['significant'] and wilcoxon_result['statistic'] < 0
            else "No significant difference between models"
        )
    }
    
    if mcnemar_result:
        results["mcnemar_test"] = mcnemar_result
        results["mcnemar_interpretation"] = (
            "RF model is significantly different" if mcnemar_result['significant']
            else "No significant difference in classification patterns"
        )
    
    # Write results to output file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


def main():
    """
    Main function to run statistical tests on aggregated results.
    """
    import sys
    
    # Default paths
    results_path = "data/results/aggregated_scores.json"
    output_path = "data/results/statistical_significance.json"
    
    # Allow command-line overrides
    if len(sys.argv) > 1:
        results_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    print(f"Loading results from: {results_path}")
    print(f"Writing results to: {output_path}")
    
    try:
        results = aggregate_and_test(results_path, output_path)
        print("\nStatistical Test Results:")
        print(f"Wilcoxon p-value: {results['wilcoxon_test']['p_value']:.4f}")
        print(f"Significant difference: {results['wilcoxon_test']['significant']}")
        print(f"Interpretation: {results['wilcoxon_interpretation']}")
        
        if 'mcnemar_test' in results:
            print(f"\nMcNemar p-value: {results['mcnemar_test']['p_value']:.4f}")
            print(f"Significant difference: {results['mcnemar_test']['significant']}")
            print(f"Interpretation: {results['mcnemar_interpretation']}")
            
        print(f"\nResults saved to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure aggregated_scores.json exists with the required format.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running statistical tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()