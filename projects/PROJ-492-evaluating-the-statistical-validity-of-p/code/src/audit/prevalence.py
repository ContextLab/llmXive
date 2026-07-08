"""
Prevalence analysis module for A/B test audit.
Implements binomial prevalence test, Wilson CI, sensitivity analysis, and dynamic Bonferroni correction.
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

logger: AuditLogger = get_default_logger(__name__)

def set_rng_seed_for_prevalence(seed: int = SEED) -> None:
    """Set random seed for reproducibility in prevalence analysis."""
    set_rng_seed(seed)

def binomial_test(inconsistent_count: int, total_count: int, p0: float = 0.5) -> float:
    """
    Perform a binomial test to assess if the observed proportion of inconsistent
    summaries differs significantly from a null hypothesis proportion.

    Args:
        inconsistent_count: Number of inconsistent summaries.
        total_count: Total number of summaries.
        p0: Null hypothesis proportion (default 0.5).

    Returns:
        Two-tailed p-value from the binomial test.
    """
    if total_count == 0:
        logger.warning("Total count is zero; cannot perform binomial test.")
        return 1.0

    # Use exact binomial test
    # scipy.stats.binomtest returns a BinomTestResult object
    try:
        result = stats.binomtest(inconsistent_count, total_count, p=p0, alternative='two-sided')
        return result.pvalue
    except Exception as e:
        logger.error(f"Binomial test failed: {e}")
        return 1.0

def wilson_ci(successes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """
    Calculate the Wilson score interval for a proportion.

    Args:
        successes: Number of successes (inconsistent summaries).
        n: Total number of trials (summaries).
        z: Z-score for the desired confidence level (default 1.96 for 95%).

    Returns:
        Tuple (lower_bound, upper_bound).
    """
    if n == 0:
        logger.warning("Sample size is zero; returning (0.0, 0.0) for Wilson CI.")
        return 0.0, 0.0

    p_hat = successes / n
    denominator = 1 + (z ** 2) / n
    center = (p_hat + (z ** 2) / (2 * n)) / denominator
    margin = (z / denominator) * np.sqrt((p_hat * (1 - p_hat) / n) + (z ** 2) / (4 * n ** 2))

    lower = center - margin
    upper = center + margin

    # Clamp to [0, 1]
    lower = max(0.0, min(1.0, lower))
    upper = max(0.0, min(1.0, upper))

    return lower, upper

def compute_prevalence(audit_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute the overall prevalence of inconsistent A/B test summaries.

    Args:
        audit_records: List of audit record dictionaries.

    Returns:
        Dictionary containing prevalence metrics.
    """
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.get('is_inconsistent', False))

    if total == 0:
        logger.warning("No audit records provided; prevalence metrics will be zero/undefined.")
        return {
            'total_summaries': 0,
            'inconsistent_count': 0,
            'inconsistent_rate': 0.0,
            'wilson_ci_lower': 0.0,
            'wilson_ci_upper': 0.0,
            'binomial_p_value': 1.0
        }

    rate = inconsistent / total
    ci_lower, ci_upper = wilson_ci(inconsistent, total)
    p_val = binomial_test(inconsistent, total)

    return {
        'total_summaries': total,
        'inconsistent_count': inconsistent,
        'inconsistent_rate': rate,
        'wilson_ci_lower': ci_lower,
        'wilson_ci_upper': ci_upper,
        'binomial_p_value': p_val
    }

def sensitivity_analysis(audit_records: List[Dict[str, Any]], baseline_range: List[float]) -> List[Dict[str, Any]]:
    """
    Perform sensitivity analysis by varying the baseline proportion used in
    binomial tests or other threshold-dependent metrics.

    Args:
        audit_records: List of audit record dictionaries.
        baseline_range: List of baseline proportions to test (e.g., [0.1, 0.2, ..., 0.9]).

    Returns:
        List of dictionaries containing results for each baseline.
    """
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.get('is_inconsistent', False))

    results = []
    for p0 in baseline_range:
        p_val = binomial_test(inconsistent, total, p0=p0)
        results.append({
            'baseline_p0': p0,
            'binomial_p_value': p_val,
            'inconsistent_count': inconsistent,
            'total_summaries': total,
            'inconsistent_rate': inconsistent / total if total > 0 else 0.0
        })

    return results

def apply_dynamic_bonferroni(p_values: List[float], num_subgroups: int) -> List[float]:
    """
    Apply dynamic Bonferroni correction to a list of p-values.
    Adjusted alpha = 0.05 / num_subgroups.
    Each p-value is compared against this adjusted threshold.
    Returns adjusted p-values (min(p * num_subgroups, 1.0)).

    Args:
        p_values: List of raw p-values.
        num_subgroups: Number of subgroups being tested.

    Returns:
        List of Bonferroni-adjusted p-values.
    """
    if num_subgroups <= 0:
        logger.warning("Number of subgroups must be positive for Bonferroni correction.")
        return p_values

    adjusted_p_values = [min(p * num_subgroups, 1.0) for p in p_values]
    return adjusted_p_values

def load_audit_records(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load audit records from a JSON file.

    Args:
        input_path: Path to the audit report JSON file.

    Returns:
        List of audit record dictionaries.
    """
    if not input_path.exists():
        logger.error(f"Audit report file not found: {input_path}")
        return []

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Handle both list and dict with 'records' key
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'records' in data:
            return data['records']
        else:
            logger.warning("Unexpected JSON structure; expected list or dict with 'records' key.")
            return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {input_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading audit records from {input_path}: {e}")
        return []

def write_prevalence_results(output_path: Path, prevalence_data: Dict[str, Any]) -> None:
    """
    Write prevalence analysis results to a JSON file.

    Args:
        output_path: Path to the output JSON file.
        prevalence_data: Dictionary containing prevalence analysis results.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(prevalence_data, f, indent=2)
    logger.info(f"Prevalence results written to {output_path}")

def run_prevalence_analysis(
    input_path: Path,
    output_path: Path,
    sensitivity_baseline_range: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Main function to run the full prevalence analysis pipeline.

    Args:
        input_path: Path to the audit report JSON file.
        output_path: Path to write the prevalence results JSON.
        sensitivity_baseline_range: Optional list of baselines for sensitivity analysis.

    Returns:
        Dictionary containing the full analysis results.
    """
    set_rng_seed_for_prevalence()

    audit_records = load_audit_records(input_path)
    if not audit_records:
        logger.error("No audit records loaded; cannot compute prevalence.")
        # Write empty result
        write_prevalence_results(output_path, {'error': 'No audit records loaded'})
        return {'error': 'No audit records loaded'}

    # Compute overall prevalence
    prevalence = compute_prevalence(audit_records)

    # Perform sensitivity analysis if range provided
    sensitivity_results = None
    if sensitivity_baseline_range:
        sensitivity_results = sensitivity_analysis(audit_records, sensitivity_baseline_range)
        prevalence['sensitivity_analysis'] = sensitivity_results

    # Write results
    write_prevalence_results(output_path, prevalence)

    return prevalence

def main() -> int:
    """
    CLI entry point for prevalence analysis.
    Expects input and output paths as command-line arguments or uses defaults.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run prevalence analysis on audit records.")
    parser.add_argument(
        '--input', '-i',
        type=Path,
        default=Path('output/audit_report.json'),
        help='Path to input audit report JSON file.'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('output/prevalence.json'),
        help='Path to output prevalence results JSON file.'
    )
    parser.add_argument(
        '--sensitivity-range', '-s',
        type=float,
        nargs='+',
        default=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        help='Baseline proportions for sensitivity analysis.'
    )

    args = parser.parse_args()

    try:
        result = run_prevalence_analysis(
            args.input,
            args.output,
            args.sensitivity_range
        )
        logger.info("Prevalence analysis completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Prevalence analysis failed: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
