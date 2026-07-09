"""
Prevalence analysis module implementing binomial tests, Wilson CI, and sensitivity analysis.

Implements:
- FR-005a: Binomial prevalence test
- FR-005b: Sensitivity analysis
- FR-032: Dynamic Bonferroni correction for subgroup analysis

This module calculates the prevalence of inconsistent A/B test summaries,
computes confidence intervals, and performs sensitivity analysis across
baseline conversion rates.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message


def set_rng_seed_for_prevalence(seed: int = SEED) -> None:
    """Set random seed for reproducibility in prevalence calculations."""
    set_rng_seed(seed)


def binomial_test(
    x: int,
    n: int,
    p: float = 0.05,
    alternative: str = "two-sided"
) -> Tuple[float, float]:
    """
    Perform a binomial test for prevalence estimation.
    
    Args:
        x: Number of successes (inconsistent summaries)
        n: Total number of trials (total summaries)
        p: Null hypothesis proportion (default 0.05)
        alternative: Type of alternative hypothesis ("two-sided", "less", "greater")
    
    Returns:
        Tuple of (p_value, effect_size)
    """
    if n == 0:
        logger = get_default_logger()
        logger.warning("Sample size is zero, returning NaN for p-value")
        return float('nan'), float('nan')
    
    # Use scipy's binom_test (deprecated) or binomtest (new)
    try:
        result = stats.binomtest(x, n, p)
        p_value = result.pvalue
    except AttributeError:
        # Fallback for older scipy versions
        p_value = stats.binom_test(x, n, p)
    
    # Effect size: observed proportion minus null proportion
    observed_prop = x / n
    effect_size = observed_prop - p
    
    return p_value, effect_size


def wilson_ci(
    x: int,
    n: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for a proportion.
    
    Args:
        x: Number of successes (inconsistent summaries)
        n: Total number of trials (total summaries)
        confidence: Confidence level (default 0.95)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    
    Reference: 
        Wilson, E. B. (1927). Probable inference, the law of succession, 
        and statistical inference. Journal of the American Statistical Association.
    """
    if n == 0:
        logger = get_default_logger()
        logger.warning("Sample size is zero, returning NaN for CI")
        return float('nan'), float('nan')
    
    p_hat = x / n
    z = stats.norm.ppf((1 + confidence) / 2)
    
    # Wilson score interval formula
    denominator = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denominator
    
    lower = center - margin
    upper = center + margin
    
    # Ensure bounds are within [0, 1]
    lower = max(0.0, min(1.0, lower))
    upper = max(0.0, min(1.0, upper))
    
    return lower, upper


def compute_prevalence(
    audit_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute overall prevalence of inconsistent summaries.
    
    Args:
        audit_records: List of audit records from validator output
    
    Returns:
        Dictionary with prevalence statistics
    """
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.get('is_inconsistent', False))
    
    p_value, effect_size = binomial_test(inconsistent, total)
    ci_lower, ci_upper = wilson_ci(inconsistent, total)
    
    return {
        'total_summaries': total,
        'inconsistent_count': inconsistent,
        'prevalence': inconsistent / total if total > 0 else 0.0,
        'p_value_binomial': p_value,
        'effect_size': effect_size,
        'wilson_ci_lower': ci_lower,
        'wilson_ci_upper': ci_upper,
        'confidence_level': 0.95
    }


def sensitivity_analysis(
    audit_records: List[Dict[str, Any]],
    baseline_range: Tuple[float, float] = (0.01, 0.10),
    num_points: int = 10
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis across different baseline conversion rates.
    
    Tests how the inconsistency rate changes when assuming different 
    baseline conversion rates, as per FR-005b.
    
    Args:
        audit_records: List of audit records
        baseline_range: Tuple of (min_baseline, max_baseline)
        num_points: Number of points to test in the range
    
    Returns:
        Dictionary with sensitivity analysis results including
        variation metrics and per-point analysis
    """
    total = len(audit_records)
    if total == 0:
        return {
            'baseline_range': baseline_range,
            'num_points': num_points,
            'results': [],
            'max_variation': 0.0,
            'is_stable': True
        }
    
    inconsistent_count = sum(1 for r in audit_records if r.get('is_inconsistent', False))
    observed_rate = inconsistent_count / total
    
    baselines = np.linspace(baseline_range[0], baseline_range[1], num_points)
    results = []
    
    for baseline in baselines:
        # Simulate expected inconsistencies under this baseline
        # This is a simplified model; real implementation would use 
        # domain-specific knowledge
        expected_inconsistent = int(total * baseline)
        rate_at_baseline = expected_inconsistent / total if total > 0 else 0.0
        
        # Calculate deviation from observed
        deviation = abs(rate_at_baseline - observed_rate)
        
        results.append({
            'baseline': baseline,
            'expected_inconsistent': expected_inconsistent,
            'expected_rate': rate_at_baseline,
            'observed_rate': observed_rate,
            'deviation': deviation
        })
    
    # Calculate variation metrics
    deviations = [r['deviation'] for r in results]
    max_variation = max(deviations) if deviations else 0.0
    mean_variation = np.mean(deviations) if deviations else 0.0
    
    # Stability check: variation must be < 0.02 per SC-015
    is_stable = max_variation < 0.02
    
    return {
        'baseline_range': baseline_range,
        'num_points': num_points,
        'observed_prevalence': observed_rate,
        'results': results,
        'max_variation': max_variation,
        'mean_variation': mean_variation,
        'is_stable': is_stable,
        'stability_threshold': 0.02
    }


def apply_dynamic_bonferroni(
    num_subgroups: int,
    alpha: float = 0.05
) -> float:
    """
    Apply dynamic Bonferroni correction for multiple comparisons.
    
    Args:
        num_subgroups: Number of subgroups being tested
        alpha: Original significance level (default 0.05)
    
    Returns:
        Corrected alpha threshold
    
    Note: Per FR-032, alpha = 0.05 / number_of_subgroups
    """
    if num_subgroups <= 0:
        logger = get_default_logger()
        logger.warning("Number of subgroups must be positive, returning original alpha")
        return alpha
    
    corrected_alpha = alpha / num_subgroups
    return corrected_alpha


def load_audit_records(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load audit records from JSON file.
    
    Args:
        input_path: Path to audit_report.json
    
    Returns:
        List of audit record dictionaries
    """
    if not input_path.exists():
        logger = get_default_logger()
        logger.error(f"Audit report not found at {input_path}")
        return []
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    else:
        logger = get_default_logger()
        logger.warning("Unexpected audit report format, attempting to parse as list")
        return [data] if isinstance(data, dict) else []


def write_prevalence_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write prevalence analysis results to JSON file.
    
    Args:
        results: Dictionary containing all prevalence analysis results
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger = get_default_logger()
    logger.info(f"Prevalence results written to {output_path}")


def run_prevalence_analysis(
    input_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Run complete prevalence analysis pipeline.
    
    Args:
        input_path: Path to audit_report.json
        output_path: Path for output prevalence.json
    
    Returns:
        Dictionary with all analysis results
    """
    set_rng_seed_for_prevalence()
    
    logger = get_default_logger()
    logger.info("Starting prevalence analysis")
    
    # Load audit records
    audit_records = load_audit_records(input_path)
    if not audit_records:
        logger.warning("No audit records found, returning empty results")
        results = {
            'status': 'empty',
            'message': 'No audit records found',
            'timestamp': datetime.now().isoformat()
        }
        write_prevalence_results(results, output_path)
        return results
    
    # Compute overall prevalence
    prevalence_data = compute_prevalence(audit_records)
    
    # Perform sensitivity analysis
    sensitivity_data = sensitivity_analysis(audit_records)
    
    # Count unique subgroups for Bonferroni correction
    # Assuming subgroups are defined by 'domain' and 'year' fields
    subgroups = set()
    for record in audit_records:
        domain = record.get('domain', 'unknown')
        year = record.get('year', 'unknown')
        subgroups.add((domain, year))
    
    num_subgroups = len(subgroups)
    corrected_alpha = apply_dynamic_bonferroni(num_subgroups)
    
    # Compile results
    results = {
        'prevalence': prevalence_data,
        'sensitivity_analysis': sensitivity_data,
        'bonferroni_correction': {
            'num_subgroups': num_subgroups,
            'original_alpha': 0.05,
            'corrected_alpha': corrected_alpha
        },
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'seed': SEED,
            'input_file': str(input_path),
            'total_records_processed': len(audit_records)
        }
    }
    
    # Write results
    write_prevalence_results(results, output_path)
    
    logger.info(f"Prevalence analysis complete. Results written to {output_path}")
    return results


def main() -> None:
    """Main entry point for prevalence analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run prevalence analysis on audit records'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('output/audit_report.json'),
        help='Path to input audit report JSON'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('output/prevalence.json'),
        help='Path to output prevalence JSON'
    )
    
    args = parser.parse_args()
    
    logger = get_default_logger()
    logger.info(f"Running prevalence analysis: {args.input} -> {args.output}")
    
    try:
        results = run_prevalence_analysis(args.input, args.output)
        
        # Print summary
        if results.get('status') != 'empty':
            p = results['prevalence']
            logger.info(f"Total summaries: {p['total_summaries']}")
            logger.info(f"Inconsistent count: {p['inconsistent_count']}")
            logger.info(f"Prevalence: {p['prevalence']:.4f}")
            logger.info(f"Wilson CI: [{p['wilson_ci_lower']:.4f}, {p['wilson_ci_upper']:.4f}]")
            
            s = results['sensitivity_analysis']
            logger.info(f"Sensitivity analysis: max variation = {s['max_variation']:.4f}")
            logger.info(f"Stable: {s['is_stable']}")
        
    except Exception as e:
        logger.error(f"Prevalence analysis failed: {e}")
        raise


if __name__ == '__main__':
    main()
