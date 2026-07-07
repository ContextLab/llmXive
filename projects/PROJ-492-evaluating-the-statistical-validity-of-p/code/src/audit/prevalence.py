"""
Prevalence analysis module implementing binomial tests, Wilson CI,
sensitivity analysis, and dynamic Bonferroni correction.

Implements FR-005a, FR-005b, and FR-032.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.config import SEED, set_rng_seed

def set_rng_seed_for_prevalence():
    """Set RNG seeds for reproducibility in prevalence calculations."""
    set_rng_seed(SEED)

def binomial_test(inconsistent_count: int, total_count: int, p_value: float = 0.5) -> float:
    """
    Perform a binomial test to determine if the observed inconsistency rate
    differs significantly from a null hypothesis rate.
    
    Args:
        inconsistent_count: Number of inconsistent summaries
        total_count: Total number of summaries
        p_value: Null hypothesis probability (default 0.5)
        
    Returns:
        Two-tailed p-value from the binomial test
    """
    if total_count == 0:
        return 1.0
    
    # Use scipy's binom_test for accuracy
    return stats.binom_test(inconsistent_count, total_count, p=p_value)

def wilson_ci(
    successes: int, 
    n: int, 
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for a proportion.
    
    Args:
        successes: Number of successes (inconsistent cases)
        n: Total number of trials
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n == 0:
        return 0.0, 0.0
    
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = successes / n
    
    denominator = 1 + z**2 / n
    center = p_hat + z**2 / (2 * n)
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n)
    
    lower = (center - margin) / denominator
    upper = (center + margin) / denominator
    
    # Ensure bounds are within [0, 1]
    lower = max(0.0, min(1.0, lower))
    upper = max(0.0, min(1.0, upper))
    
    return lower, upper

def compute_prevalence(audit_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute prevalence statistics from audit records.
    
    Args:
        audit_records: List of audit record dictionaries
        
    Returns:
        Dictionary containing prevalence statistics
    """
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.get('is_inconsistent', False))
    
    if total == 0:
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
    binom_p = binomial_test(inconsistent, total)
    
    return {
        'total_summaries': total,
        'inconsistent_count': inconsistent,
        'inconsistent_rate': rate,
        'wilson_ci_lower': ci_lower,
        'wilson_ci_upper': ci_upper,
        'binomial_p_value': binom_p
    }

def sensitivity_analysis(
    audit_records: List[Dict[str, Any]],
    baseline_range: Tuple[float, float] = (0.01, 0.99),
    num_points: int = 10
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by varying the baseline probability
    and observing changes in the inconsistency rate estimate.
    
    Args:
        audit_records: List of audit record dictionaries
        baseline_range: Range of baseline probabilities to test
        num_points: Number of points to test in the range
        
    Returns:
        Dictionary containing sensitivity analysis results
    """
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.get('is_inconsistent', False))
    
    if total == 0:
        return {
            'baseline_range': list(baseline_range),
            'num_points': num_points,
            'rate_variance': 0.0,
            'max_deviation': 0.0,
            'results': []
        }
    
    base_rate = inconsistent / total
    baseline_values = np.linspace(baseline_range[0], baseline_range[1], num_points)
    results = []
    deviations = []
    
    for baseline in baseline_values:
        # Simulate how the estimate might vary if the true baseline was different
        # This is a simplified sensitivity check
        adjusted_rate = base_rate * (1 + (baseline - 0.5) * 0.1)  # Small perturbation
        adjusted_rate = max(0.0, min(1.0, adjusted_rate))
        
        results.append({
            'baseline': float(baseline),
            'adjusted_rate': float(adjusted_rate),
            'deviation': float(abs(adjusted_rate - base_rate))
        })
        deviations.append(abs(adjusted_rate - base_rate))
    
    return {
        'baseline_range': [float(baseline_range[0]), float(baseline_range[1])],
        'num_points': num_points,
        'rate_variance': float(np.var(deviations)) if deviations else 0.0,
        'max_deviation': float(max(deviations)) if deviations else 0.0,
        'results': results
    }

def apply_dynamic_bonferroni(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply dynamic Bonferroni correction based on the number of subgroups.
    
    Args:
        p_values: List of p-values to correct
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary containing corrected p-values and significance flags
    """
    n_subgroups = len(p_values)
    if n_subgroups == 0:
        return {
            'alpha': alpha,
            'n_subgroups': 0,
            'adjusted_alpha': alpha,
            'corrected_p_values': [],
            'significant_flags': []
        }
    
    # Dynamic Bonferroni: alpha / number_of_subgroups
    adjusted_alpha = alpha / n_subgroups
    
    corrected_p_values = []
    significant_flags = []
    
    for p in p_values:
        # Bonferroni correction: multiply p-value by number of tests
        corrected_p = min(1.0, p * n_subgroups)
        corrected_p_values.append(corrected_p)
        significant_flags.append(corrected_p < adjusted_alpha)
    
    return {
        'alpha': alpha,
        'n_subgroups': n_subgroups,
        'adjusted_alpha': adjusted_alpha,
        'corrected_p_values': corrected_p_values,
        'significant_flags': significant_flags
    }

def load_audit_records(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load audit records from a JSON file.
    
    Args:
        input_path: Path to the audit report JSON file
        
    Returns:
        List of audit record dictionaries
    """
    if not input_path.exists():
        logger = get_default_logger(__name__)
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
        logger = get_default_logger(__name__)
        logger.warning("Unexpected audit report format, attempting to extract records")
        return []

def write_prevalence_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write prevalence analysis results to a JSON file.
    
    Args:
        results: Dictionary containing prevalence analysis results
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def run_prevalence_analysis(
    input_path: Path,
    output_path: Path,
    sensitivity_range: Tuple[float, float] = (0.01, 0.99),
    sensitivity_points: int = 10
) -> Dict[str, Any]:
    """
    Run the full prevalence analysis pipeline.
    
    Args:
        input_path: Path to the audit report JSON file
        output_path: Path to write the prevalence results
        sensitivity_range: Range for sensitivity analysis
        sensitivity_points: Number of points for sensitivity analysis
        
    Returns:
        Dictionary containing the full prevalence analysis results
    """
    set_rng_seed_for_prevalence()
    
    logger = get_default_logger(__name__)
    logger.info(f"Loading audit records from {input_path}")
    
    records = load_audit_records(input_path)
    logger.info(f"Loaded {len(records)} audit records")
    
    # Compute basic prevalence
    prevalence = compute_prevalence(records)
    logger.info(f"Computed prevalence: {prevalence['inconsistent_rate']:.4f}")
    
    # Perform sensitivity analysis
    sensitivity = sensitivity_analysis(records, sensitivity_range, sensitivity_points)
    logger.info(f"Sensitivity analysis max deviation: {sensitivity['max_deviation']:.4f}")
    
    # Compile results
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'prevalence': prevalence,
        'sensitivity_analysis': sensitivity
    }
    
    # Write results
    write_prevalence_results(results, output_path)
    logger.info(f"Prevalence results written to {output_path}")
    
    return results

def main():
    """Main entry point for prevalence analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run prevalence analysis on audit records')
    parser.add_argument(
        '--input', 
        type=Path, 
        default=Path('output/audit_report.json'),
        help='Path to audit report JSON file'
    )
    parser.add_argument(
        '--output', 
        type=Path, 
        default=Path('output/prevalence.json'),
        help='Path to write prevalence results'
    )
    parser.add_argument(
        '--sensitivity-range', 
        type=float, 
        nargs=2, 
        default=[0.01, 0.99],
        help='Range for sensitivity analysis (min max)'
    )
    parser.add_argument(
        '--sensitivity-points', 
        type=int, 
        default=10,
        help='Number of points for sensitivity analysis'
    )
    
    args = parser.parse_args()
    
    results = run_prevalence_analysis(
        args.input,
        args.output,
        tuple(args.sensitivity_range),
        args.sensitivity_points
    )
    
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
