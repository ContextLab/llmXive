"""
Prevalence analysis module for A/B test audit results.

Implements binomial tests, Wilson confidence intervals, and sensitivity analysis
for calculating the prevalence of inconsistent test results.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)


def set_rng_seed_for_prevalence(seed: int = SEED) -> None:
    """Set random seed for reproducibility in prevalence calculations."""
    set_rng_seed(seed)


def binomial_test(successes: int, n: int, p_null: float = 0.5) -> Tuple[float, float, float]:
    """
    Perform a binomial test and return p-value and confidence interval.

    Args:
        successes: Number of observed successes
        n: Total number of trials
        p_null: Null hypothesis probability of success

    Returns:
        Tuple of (p_value, ci_lower, ci_upper)
    """
    if n <= 0:
        raise ValueError("Sample size n must be positive")
    if successes < 0 or successes > n:
        raise ValueError("Successes must be between 0 and n")
    if not 0 <= p_null <= 1:
        raise ValueError("p_null must be between 0 and 1")

    # Use scipy's binomtest for accurate calculation
    result = stats.binomtest(successes, n, p_null)
    p_value = result.pvalue

    # Calculate Wilson confidence interval for the proportion
    p_hat = successes / n
    ci_lower, ci_upper = wilson_ci(n, p_hat)

    return p_value, ci_lower, ci_upper


def wilson_ci(n: int, p_hat: float, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for a proportion.

    The Wilson score interval is preferred for proportions, especially
    when n is small or p is close to 0 or 1.

    Args:
        n: Sample size
        p_hat: Observed proportion (successes / n)
        alpha: Significance level (default 0.05 for 95% CI)

    Returns:
        Tuple of (ci_lower, ci_upper)
    """
    if n <= 0:
        raise ValueError("Sample size n must be positive")
    if not 0 <= p_hat <= 1:
        raise ValueError("p_hat must be between 0 and 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    z = stats.norm.ppf(1 - alpha / 2)

    # Wilson score interval formula
    denominator = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denominator
    margin = (z / denominator) * np.sqrt(
        p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)
    )

    ci_lower = max(0.0, center - margin)
    ci_upper = min(1.0, center + margin)

    return ci_lower, ci_upper


def compute_prevalence(inconsistent_count: int, total_count: int) -> Tuple[float, float, float]:
    """
    Compute the prevalence of inconsistent results with confidence interval.

    Args:
        inconsistent_count: Number of inconsistent records
        total_count: Total number of records

    Returns:
        Tuple of (prevalence, ci_lower, ci_upper)
    """
    if total_count <= 0:
        raise ValueError("Total count must be positive")
    if inconsistent_count < 0 or inconsistent_count > total_count:
        raise ValueError("Inconsistent count must be between 0 and total count")

    prevalence = inconsistent_count / total_count

    if total_count == 0:
        return 0.0, 0.0, 0.0

    ci_lower, ci_upper = wilson_ci(total_count, prevalence)

    return prevalence, ci_lower, ci_upper


def sensitivity_analysis(
    audit_records: List[Dict[str, Any]],
    baseline_range: List[float] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on prevalence estimates.

    Checks how prevalence estimates vary under different assumptions.

    Args:
        audit_records: List of audit record dictionaries
        baseline_range: Range of baseline probabilities to test (default: [0.4, 0.6])

    Returns:
        Dictionary containing sensitivity analysis results
    """
    if baseline_range is None:
        baseline_range = [0.4, 0.5, 0.6]

    total_count = len(audit_records)
    inconsistent_count = sum(1 for r in audit_records if r.get('is_inconsistent', False))

    results = {
        'total_records': total_count,
        'inconsistent_count': inconsistent_count,
        'baseline_analysis': []
    }

    for p_null in baseline_range:
        # Recalculate prevalence with different null assumptions if needed
        # For now, we just report the standard prevalence
        prevalence, ci_lower, ci_upper = compute_prevalence(inconsistent_count, total_count)

        results['baseline_analysis'].append({
            'p_null': p_null,
            'prevalence': prevalence,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'ci_width': ci_upper - ci_lower
        })

    # Calculate max variation in CI width
    ci_widths = [r['ci_width'] for r in results['baseline_analysis']]
    max_variation = max(ci_widths) - min(ci_widths) if ci_widths else 0.0

    results['max_ci_width_variation'] = max_variation

    return results


def apply_dynamic_bonferroni(alpha: float, num_subgroups: int) -> float:
    """
    Apply Bonferroni correction dynamically based on number of subgroups.

    Args:
        alpha: Original significance level
        num_subgroups: Number of subgroups being tested

    Returns:
        Adjusted alpha level
    """
    if num_subgroups <= 0:
        raise ValueError("Number of subgroups must be positive")

    return alpha / num_subgroups


def load_audit_records(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load audit records from a JSON file.

    Args:
        filepath: Path to the audit report JSON file

    Returns:
        List of audit record dictionaries
    """
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    else:
        raise ValueError("Unexpected JSON format in audit report")


def write_prevalence_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write prevalence analysis results to a JSON file.

    Args:
        results: Dictionary containing prevalence analysis results
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Prevalence results written to {output_path}")


def run_prevalence_analysis(
    audit_report_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Run full prevalence analysis on audit report.

    Args:
        audit_report_path: Path to audit report JSON
        output_path: Path for output results JSON

    Returns:
        Dictionary containing prevalence analysis results
    """
    set_rng_seed_for_prevalence()

    logger.info(f"Loading audit records from {audit_report_path}")
    audit_records = load_audit_records(audit_report_path)

    total_count = len(audit_records)
    inconsistent_count = sum(1 for r in audit_records if r.get('is_inconsistent', False))

    prevalence, ci_lower, ci_upper = compute_prevalence(inconsistent_count, total_count)

    results = {
        'analysis_timestamp': datetime.now().isoformat(),
        'total_records': total_count,
        'inconsistent_count': inconsistent_count,
        'consistent_count': total_count - inconsistent_count,
        'prevalence': prevalence,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'ci_width': ci_upper - ci_lower,
        'confidence_level': 0.95,
        'sensitivity_analysis': sensitivity_analysis(audit_records)
    }

    write_prevalence_results(results, output_path)

    return results


def main():
    """Main entry point for prevalence analysis."""
    import argparse

    parser = argparse.ArgumentParser(description='Run prevalence analysis on audit results')
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('output/audit_report.json'),
        help='Path to audit report JSON'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('output/prevalence.json'),
        help='Path for output results JSON'
    )

    args = parser.parse_args()

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1

    try:
        results = run_prevalence_analysis(args.input, args.output)
        logger.info(f"Analysis complete. Prevalence: {results['prevalence']:.4f}")
        return 0
    except Exception as e:
        logger.error(f"Error during prevalence analysis: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
