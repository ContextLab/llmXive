"""
Statistical analysis module for llmXive project.

This module implements statistical tests to compare adapter performance.
Per Spec SC-005 and Plan amendment (T000), the PRIMARY method is the
Wilcoxon signed-rank test. The paired t-test is retained only for
reference/comparison purposes but is NOT the default.

PLAN AMENDMENT (T000):
- Original Plan.md stated 'Paired t-test'.
- Spec SC-005 mandates 'Wilcoxon signed-rank test'.
- Plan.md has been updated to reflect Wilcoxon as the primary method.
- This implementation follows the amended Plan and Spec SC-005.
"""
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from scipy import stats


def load_scores_from_csv(filepath: str) -> List[float]:
    """
    Load exact-match scores from a CSV file.

    Args:
        filepath: Path to the CSV file (e.g., 'data/results/ast_scores.csv')

    Returns:
        List of float scores (exact_match column)

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the CSV is empty or lacks the required column
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Scores file not found: {filepath}")

    scores = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'exact_match' not in reader.fieldnames:
            raise ValueError(f"CSV must contain 'exact_match' column. Found: {reader.fieldnames}")

        for row in reader:
            try:
                score = float(row['exact_match'])
                scores.append(score)
            except (ValueError, TypeError):
                # Skip rows with invalid scores
                continue

    if not scores:
        raise ValueError(f"No valid scores found in {filepath}")

    return scores


def run_wilcoxon_test(group_a: List[float], group_b: List[float]) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test (PRIMARY method per SC-005).

    This is a non-parametric test for paired data, suitable when
    the assumption of normality is not met.

    Args:
        group_a: List of scores from method A (e.g., AST-based)
        group_b: List of scores from method B (e.g., Neural baseline)

    Returns:
        Dictionary containing:
            - statistic: Wilcoxon test statistic
            - p_value: Two-sided p-value
            - test_used: "wilcoxon"

    Raises:
        ValueError: If lists are empty or have different lengths
    """
    if len(group_a) == 0 or len(group_b) == 0:
        raise ValueError("Input lists cannot be empty")

    if len(group_a) != len(group_b):
        raise ValueError(f"Lists must have equal length: {len(group_a)} vs {len(group_b)}")

    # Wilcoxon signed-rank test
    statistic, p_value = stats.wilcoxon(group_a, group_b)

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "test_used": "wilcoxon"
    }


def run_ttest_paired(group_a: List[float], group_b: List[float]) -> Dict[str, Any]:
    """
    Perform paired t-test (REFERENCE ONLY - NOT PRIMARY).

    This is retained for comparison purposes but is NOT the default
    method as per Spec SC-005 and Plan amendment (T000).

    Args:
        group_a: List of scores from method A
        group_b: List of scores from method B

    Returns:
        Dictionary containing:
            - statistic: t-statistic
            - p_value: Two-sided p-value
            - test_used: "ttest_paired"
    """
    if len(group_a) == 0 or len(group_b) == 0:
        raise ValueError("Input lists cannot be empty")

    if len(group_a) != len(group_b):
        raise ValueError(f"Lists must have equal length: {len(group_a)} vs {len(group_b)}")

    statistic, p_value = stats.ttest_rel(group_a, group_b)

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "test_used": "ttest_paired"
    }


def compare_adapters(ast_scores_path: str, neural_scores_path: str,
                     use_wilcoxon: bool = True) -> Dict[str, Any]:
    """
    Compare two adapter performance results using statistical testing.

    Per Spec SC-005 and Plan amendment (T000), the default test is
    Wilcoxon signed-rank (use_wilcoxon=True).

    Args:
        ast_scores_path: Path to AST adapter scores CSV
        neural_scores_path: Path to Neural baseline scores CSV
        use_wilcoxon: If True (default), use Wilcoxon; else use t-test

    Returns:
        Dictionary containing:
            - test_used: Name of the test performed
            - statistic: Test statistic
            - p_value: P-value
            - significant: True if p_value < 0.05
            - ast_mean: Mean of AST scores
            - neural_mean: Mean of Neural scores
            - delta: Neural mean - AST mean
    """
    ast_scores = load_scores_from_csv(ast_scores_path)
    neural_scores = load_scores_from_csv(neural_scores_path)

    if use_wilcoxon:
        result = run_wilcoxon_test(ast_scores, neural_scores)
    else:
        result = run_ttest_paired(ast_scores, neural_scores)

    ast_mean = sum(ast_scores) / len(ast_scores)
    neural_mean = sum(neural_scores) / len(neural_scores)
    delta = neural_mean - ast_mean

    return {
        **result,
        "significant": result["p_value"] < 0.05,
        "ast_mean": float(ast_mean),
        "neural_mean": float(neural_mean),
        "delta": float(delta)
    }


def verify_significance(p_value: float, threshold: float = 0.05) -> bool:
    """
    Verify if a p-value indicates statistical significance.

    Args:
        p_value: The p-value to check
        threshold: Significance threshold (default 0.05)

    Returns:
        True if p_value < threshold
    """
    return p_value < threshold


def main():
    """
    Main entry point for statistical comparison.

    Usage:
        python -m code.evaluation.stats --ast data/results/ast_scores.csv \
                                        --neural data/results/neural_scores.csv \
                                        --output data/results/stats.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Statistical comparison of adapter performance")
    parser.add_argument("--ast", required=True, help="Path to AST scores CSV")
    parser.add_argument("--neural", required=True, help="Path to Neural scores CSV")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    parser.add_argument("--use-ttest", action="store_true",
                        help="Use t-test instead of Wilcoxon (default: Wilcoxon per SC-005)")
    args = parser.parse_args()

    try:
        result = compare_adapters(
            args.ast,
            args.neural,
            use_wilcoxon=not args.use_ttest
        )

        # Write results to JSON
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        print(f"Results written to {args.output}")
        print(f"Test used: {result['test_used']}")
        print(f"P-value: {result['p_value']:.6f}")
        print(f"Significant (p < 0.05): {result['significant']}")

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()