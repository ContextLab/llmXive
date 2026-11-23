"""
Statistical Validation Module for OCC-RAG Pruning Analysis

This module implements the statistical validation logic for comparing
the faithfulness scores of the original model versus the pruned model.
It includes paired t-tests, collinearity analysis, and significance flagging.
"""

import os
import json
import csv
import logging
import sys
import math
from typing import List, Dict, Any, Tuple, Optional

# Import from local config
from code_00_config import Config, validate_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def load_faithfulness_scores(file_path: str) -> List[Dict[str, Any]]:
    """
    Load faithfulness scores from a CSV file.

    Args:
        file_path: Path to the CSV file containing faithfulness scores.

    Returns:
        List of dictionaries with 'sample_id' and 'faithfulness_score'.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Faithfulness scores file not found: {file_path}")

    scores = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append({
                'sample_id': row['sample_id'],
                'faithfulness_score': float(row['faithfulness_score'])
            })
    return scores


def align_scores(
    original_scores: List[Dict[str, Any]],
    pruned_scores: List[Dict[str, Any]]
) -> Tuple[List[float], List[float]]:
    """
    Align scores from original and pruned models by sample_id.

    Args:
        original_scores: List of original model scores.
        pruned_scores: List of pruned model scores.

    Returns:
        Tuple of (original_aligned, pruned_aligned) lists of scores.

    Raises:
        ValueError: If sample_ids do not match or counts differ.
    """
    original_map = {s['sample_id']: s['faithfulness_score'] for s in original_scores}
    pruned_map = {s['sample_id']: s['faithfulness_score'] for s in pruned_scores}

    common_ids = sorted(set(original_map.keys()) & set(pruned_map.keys()))

    if not common_ids:
        raise ValueError("No common sample IDs found between original and pruned scores.")

    if len(common_ids) != len(original_map) or len(common_ids) != len(pruned_map):
        logger.warning(
            f"Sample ID mismatch: {len(common_ids)} common out of "
            f"{len(original_map)} original and {len(pruned_map)} pruned."
        )

    original_aligned = [original_map[sid] for sid in common_ids]
    pruned_aligned = [pruned_map[sid] for sid in common_ids]

    return original_aligned, pruned_aligned


def calculate_mean(values: List[float]) -> float:
    """Calculate the arithmetic mean."""
    if not values:
        raise ValueError("Cannot calculate mean of empty list")
    return sum(values) / len(values)


def calculate_std(values: List[float], ddof: int = 1) -> float:
    """Calculate standard deviation with specified degrees of freedom."""
    n = len(values)
    if n <= ddof:
        return 0.0
    mean = calculate_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / (n - ddof)
    return math.sqrt(variance)


def perform_paired_ttest(
    original_scores: List[float],
    pruned_scores: List[float]
) -> Dict[str, float]:
    """
    Perform a paired t-test to compare original and pruned model scores.

    Args:
        original_scores: List of original model scores.
        pruned_scores: List of pruned model scores (must be same length).

    Returns:
        Dictionary containing t-statistic, p-value, mean difference, and confidence interval.
    """
    if len(original_scores) != len(pruned_scores):
        raise ValueError("Score lists must be of equal length for paired t-test.")

    n = len(original_scores)
    if n < 2:
        raise ValueError("Paired t-test requires at least 2 samples.")

    # Calculate differences
    differences = [o - p for o, p in zip(original_scores, pruned_scores)]

    mean_diff = calculate_mean(differences)
    std_diff = calculate_std(differences, ddof=1)

    # Standard error of the mean difference
    se_diff = std_diff / math.sqrt(n) if std_diff > 0 else 0.0

    # T-statistic
    if se_diff == 0:
        t_stat = float('inf') if mean_diff != 0 else 0.0
    else:
        t_stat = mean_diff / se_diff

    # Approximate p-value using t-distribution (two-tailed)
    # Since we don't have scipy, we use a simple approximation or return a placeholder
    # For a real implementation, we would use scipy.stats.t.sf
    # Here we implement a basic approximation for the p-value based on t-statistic
    # This is a simplified version; for production, scipy is recommended.
    # Using a simple approximation: for |t| > 3, p is very small; for |t| < 1, p is large.
    # A more accurate approximation using the error function or a lookup table could be used.
    # For this task, we will use a simple heuristic or return a calculated value if possible.
    # However, without scipy, we cannot get an exact p-value.
    # Let's implement a basic approximation using the fact that for large n, t ~ N(0,1).
    # We'll use a simple approximation for the two-tailed p-value.

    # Approximation for p-value (two-tailed) using the standard normal distribution
    # P(|Z| > |t|) = 2 * (1 - Phi(|t|))
    # Using a simple approximation for Phi (CDF of standard normal)
    def normal_cdf(x):
        # Approximation of the standard normal CDF
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    p_value = 2 * (1 - normal_cdf(abs(t_stat)))

    # 95% Confidence Interval for the mean difference
    # t_critical for 95% CI with n-1 degrees of freedom
    # For large n, t_critical ≈ 1.96
    t_critical = 1.96 if n > 30 else 2.0  # Simplified; ideally use t-table
    ci_lower = mean_diff - t_critical * se_diff
    ci_upper = mean_diff + t_critical * se_diff

    return {
        't_statistic': t_stat,
        'p_value': p_value,
        'mean_difference': mean_diff,
        'std_difference': std_diff,
        'n_samples': n,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper
    }


def calculate_collinearity(
    original_scores: List[float],
    pruned_scores: List[float]
) -> float:
    """
    Calculate Pearson correlation coefficient between original and pruned scores.

    Args:
        original_scores: List of original model scores.
        pruned_scores: List of pruned model scores.

    Returns:
        Pearson correlation coefficient.
    """
    if len(original_scores) != len(pruned_scores):
        raise ValueError("Score lists must be of equal length.")

    n = len(original_scores)
    if n < 2:
        return 0.0

    mean_orig = calculate_mean(original_scores)
    mean_pruned = calculate_mean(pruned_scores)

    numerator = sum((o - mean_orig) * (p - mean_pruned) for o, p in zip(original_scores, pruned_scores))

    sum_sq_orig = sum((o - mean_orig) ** 2 for o in original_scores)
    sum_sq_pruned = sum((p - mean_pruned) ** 2 for p in pruned_scores)

    denominator = math.sqrt(sum_sq_orig * sum_sq_pruned)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def generate_report(
    ttest_results: Dict[str, float],
    collinearity: float,
    output_path: str
) -> Dict[str, Any]:
    """
    Generate a comprehensive statistical validation report.

    Args:
        ttest_results: Results from the paired t-test.
        collinearity: Pearson correlation coefficient.
        output_path: Path to save the JSON report.

    Returns:
        The report dictionary.
    """
    # Flag for statistical significance
    is_significant = ttest_results['p_value'] < 0.05

    report = {
        'ttest_results': ttest_results,
        'collinearity': collinearity,
        'significance_flag': is_significant,
        'conclusion': (
            "Performance drop is statistically significant."
            if is_significant
            else "Performance drop is NOT statistically significant."
        ),
        'timestamp': None  # Could be filled with datetime if needed
    }

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Statistical validation report saved to {output_path}")
    return report


def main():
    """
    Main entry point for statistical validation.
    """
    config = Config()
    validate_config(config)

    # Paths to input files
    original_scores_path = "data/processed/original_faithfulness_scores.csv"
    pruned_scores_path = "data/processed/pruned_faithfulness_scores.csv"
    report_path = "data/processed/statistical_validation_report.json"

    logger.info("Loading original faithfulness scores...")
    original_scores = load_faithfulness_scores(original_scores_path)

    logger.info("Loading pruned faithfulness scores...")
    pruned_scores = load_faithfulness_scores(pruned_scores_path)

    logger.info("Aligning scores...")
    original_aligned, pruned_aligned = align_scores(original_scores, pruned_scores)

    logger.info("Performing paired t-test...")
    ttest_results = perform_paired_ttest(original_aligned, pruned_aligned)

    logger.info(f"T-test Results: t={ttest_results['t_statistic']:.4f}, p={ttest_results['p_value']:.6f}")

    logger.info("Calculating collinearity...")
    collinearity = calculate_collinearity(original_aligned, pruned_aligned)
    logger.info(f"Collinearity (Pearson r): {collinearity:.4f}")

    logger.info("Generating report...")
    report = generate_report(ttest_results, collinearity, report_path)

    # Log the significance flag as per T025
    if report['significance_flag']:
        logger.info("SIGNIFICANCE FLAG: Performance drop is STATISTICALLY SIGNIFICANT (p < 0.05).")
    else:
        logger.info("SIGNIFICANCE FLAG: Performance drop is NOT STATISTICALLY SIGNIFICANT (p >= 0.05).")

    return report


if __name__ == "__main__":
    main()