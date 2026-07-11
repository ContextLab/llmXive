"""
Statistical analysis module for comparing AST-based vs Neural adapter performance.

CRITICAL NOTE ON TEST SELECTION (T000 Resolution):
------------------------------------------------------------------
The project Plan.md originally specified a 'Paired t-test'.
However, the Feature Specification SC-005 explicitly mandates the
'Wilcoxon signed-rank test' as the primary method for this comparison.
This implementation prioritizes the Spec (SC-005) over the Plan.
We use Wilcoxon signed-rank test by default.
------------------------------------------------------------------
"""

import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from scipy import stats
import numpy as np


def load_scores_from_csv(file_path: str) -> List[float]:
    """
    Loads exact-match scores from a CSV file.
    Expected CSV format: task_id, score (or similar, we look for a numeric column).
    """
    scores = []
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Score file not found: {file_path}")

    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Determine which column contains the score (usually 'score' or 'exact_match')
        # We assume the CSV has a column named 'score' based on T021/T024 context.
        score_key = None
        if 'score' in reader.fieldnames:
            score_key = 'score'
        elif 'exact_match' in reader.fieldnames:
            score_key = 'exact_match'
        else:
            # Fallback: take the second column if 'score' not found
            if reader.fieldnames and len(reader.fieldnames) > 1:
                score_key = reader.fieldnames[1]
            else:
                raise ValueError(f"Could not identify score column in {file_path}. Headers: {reader.fieldnames}")

        for row in reader:
            val = row.get(score_key)
            if val is not None:
                try:
                    scores.append(float(val))
                except ValueError:
                    continue # Skip non-numeric values

    if len(scores) == 0:
        raise ValueError(f"No valid scores found in {file_path}")

    return scores


def run_wilcoxon_test(
    ast_scores: List[float],
    neural_scores: List[float]
) -> Dict[str, Any]:
    """
    Performs the Wilcoxon signed-rank test as mandated by SC-005.
    
    Args:
        ast_scores: List of scores from the AST-based adapter.
        neural_scores: List of scores from the neural baseline adapter.
    
    Returns:
        Dictionary containing:
            - 'p_value': float
            - 'statistic': float
            - 'test_used': 'wilcoxon'
            - 'n_samples': int (number of paired samples)
    """
    if len(ast_scores) != len(neural_scores):
        raise ValueError(
            f"Score lists must be of equal length. "
            f"AST: {len(ast_scores)}, Neural: {len(neural_scores)}"
        )
    
    if len(ast_scores) < 2:
        raise ValueError("Need at least 2 samples to perform statistical test.")

    # Convert to numpy arrays for easier handling
    arr_ast = np.array(ast_scores)
    arr_neural = np.array(neural_scores)

    # Perform Wilcoxon signed-rank test
    # alternative='two-sided' is default
    statistic, p_value = stats.wilcoxon(arr_ast, arr_neural)

    return {
        "p_value": float(p_value),
        "statistic": float(statistic),
        "test_used": "wilcoxon",
        "n_samples": len(ast_scores)
    }


def run_ttest_paired(
    ast_scores: List[float],
    neural_scores: List[float]
) -> Dict[str, Any]:
    """
    Fallback: Paired t-test.
    Note: Per T000 and SC-005, this is secondary and only used if Wilcoxon
    is deemed inappropriate (though Wilcoxon is generally preferred for non-normal data).
    """
    if len(ast_scores) != len(neural_scores):
        raise ValueError("Score lists must be of equal length.")
    
    if len(ast_scores) < 2:
        raise ValueError("Need at least 2 samples.")

    statistic, p_value = stats.ttest_rel(ast_scores, neural_scores)

    return {
        "p_value": float(p_value),
        "statistic": float(statistic),
        "test_used": "paired_t_test",
        "n_samples": len(ast_scores)
    }


def compare_adapters(
    ast_scores_path: str,
    neural_scores_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Main entry point for comparing two adapter score CSVs.
    
    1. Loads scores from both files.
    2. Runs Wilcoxon signed-rank test (primary, per SC-005).
    3. Outputs results to JSON.
    
    Args:
        ast_scores_path: Path to CSV with AST adapter scores.
        neural_scores_path: Path to CSV with Neural adapter scores.
        output_path: Path where the result JSON will be saved.
    
    Returns:
        The result dictionary.
    """
    ast_scores = load_scores_from_csv(ast_scores_path)
    neural_scores = load_scores_from_csv(neural_scores_path)

    # Primary test: Wilcoxon (as per SC-005 and T000 override)
    # We do not need to check normality first because Wilcoxon is the 
    # non-parametric alternative specifically chosen for this study.
    result = run_wilcoxon_test(ast_scores, neural_scores)

    # Ensure output directory exists
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to JSON
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    return result


def verify_significance(
    ast_scores_path: str,
    neural_scores_path: str,
    threshold: float = 0.05
) -> bool:
    """
    Verification step: Asserts that the p-value is less than the threshold
    for the given data. Used for testing or validation.
    
    Args:
        ast_scores_path: Path to AST scores CSV.
        neural_scores_path: Path to Neural scores CSV.
        threshold: P-value threshold (default 0.05).
    
    Returns:
        True if p_value < threshold, False otherwise.
    
    Raises:
        AssertionError if the condition is not met (for testing purposes).
    """
    ast_scores = load_scores_from_csv(ast_scores_path)
    neural_scores = load_scores_from_csv(neural_scores_path)
    
    result = run_wilcoxon_test(ast_scores, neural_scores)
    
    is_significant = result['p_value'] < threshold
    
    if not is_significant:
        # In a real run, we might just return False. 
        # For a verification step in tests, we raise to fail fast.
        raise AssertionError(
            f"Verification failed: p-value ({result['p_value']:.4f}) "
            f"is not less than threshold ({threshold})."
        )
    
    return True


def main():
    """
    CLI entry point for running the statistical comparison.
    Usage: python -m code.evaluation.stats --ast <path> --neural <path> --out <path>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Compare adapter performance stats")
    parser.add_argument("--ast", required=True, help="Path to AST scores CSV")
    parser.add_argument("--neural", required=True, help="Path to Neural scores CSV")
    parser.add_argument("--out", required=True, help="Path to output JSON")
    
    args = parser.parse_args()
    
    print(f"Loading scores from {args.ast} and {args.neural}...")
    try:
        result = compare_adapters(args.ast, args.neural, args.out)
        print(f"Analysis complete. Test used: {result['test_used']}")
        print(f"Statistic: {result['statistic']}, P-value: {result['p_value']}")
        print(f"Results saved to {args.out}")
        
        if result['p_value'] < 0.05:
            print("Result: Statistically significant difference detected (p < 0.05).")
        else:
            print("Result: No statistically significant difference detected (p >= 0.05).")
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()