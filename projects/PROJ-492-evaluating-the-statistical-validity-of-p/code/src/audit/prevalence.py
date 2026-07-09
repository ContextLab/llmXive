"""
Prevalence analysis module for A/B test audit.

Implements:
- Binomial prevalence test
- Wilson Confidence Interval
- Sensitivity analysis
- Dynamic Bonferroni correction (FR-032)

Output: output/prevalence.json
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

# Ensure output directory exists
OUTPUT_DIR = Path("code/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def set_rng_seed_for_prevalence(seed: int = SEED) -> None:
    """Set random seed for reproducibility."""
    set_rng_seed(seed)

def binomial_test(successes: int, trials: int, p_null: float = 0.5) -> float:
    """
    Compute two-sided binomial test p-value.
    
    Args:
        successes: Number of successes (inconsistent tests)
        trials: Total number of trials (total tests)
        p_null: Null hypothesis proportion (default 0.5)
    
    Returns:
        Two-sided p-value from binomial test
    """
    if trials == 0:
        return 1.0
    
    # Use scipy binom_test (deprecated but still available) or binomtest
    try:
        result = stats.binomtest(successes, trials, p_null)
        return result.pvalue
    except AttributeError:
        # Fallback for older scipy versions
        return stats.binom_test(successes, trials, p_null)

def wilson_ci(successes: int, trials: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Compute Wilson score confidence interval for proportion.
    
    Args:
        successes: Number of successes
        trials: Total number of trials
        confidence: Confidence level (default 0.95)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if trials == 0:
        return (0.0, 0.0)
    
    proportion = successes / trials
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    denominator = 1 + (z ** 2) / trials
    center = (proportion + (z ** 2) / (2 * trials)) / denominator
    margin = (z * np.sqrt((proportion * (1 - proportion) / trials) + (z ** 2) / (4 * trials ** 2))) / denominator
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)

def compute_prevalence(audit_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute overall prevalence of inconsistent A/B test summaries.
    
    Args:
        audit_records: List of audit records from validator
    
    Returns:
        Dictionary containing prevalence statistics
    """
    total = len(audit_records)
    if total == 0:
        return {
            "total_summaries": 0,
            "inconsistent_count": 0,
            "inconsistent_rate": 0.0,
            "consistent_count": 0,
            "consistent_rate": 0.0,
            "wilson_ci_lower": 0.0,
            "wilson_ci_upper": 0.0,
            "binomial_pvalue": 1.0,
            "confidence_level": 0.95
        }
    
    inconsistent_count = sum(1 for r in audit_records if r.get("is_inconsistent", False))
    consistent_count = total - inconsistent_count
    
    inconsistent_rate = inconsistent_count / total
    consistent_rate = consistent_count / total
    
    # Wilson CI
    ci_lower, ci_upper = wilson_ci(inconsistent_count, total)
    
    # Binomial test against null hypothesis of 50% inconsistency rate
    p_value = binomial_test(inconsistent_count, total, p_null=0.5)
    
    return {
        "total_summaries": total,
        "inconsistent_count": inconsistent_count,
        "inconsistent_rate": inconsistent_rate,
        "consistent_count": consistent_count,
        "consistent_rate": consistent_rate,
        "wilson_ci_lower": ci_lower,
        "wilson_ci_upper": ci_upper,
        "binomial_pvalue": p_value,
        "confidence_level": 0.95,
        "timestamp": datetime.utcnow().isoformat()
    }

def sensitivity_analysis(
    audit_records: List[Dict[str, Any]], 
    baseline_range: List[float] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by varying the inconsistency threshold.
    
    Args:
        audit_records: List of audit records
        baseline_range: List of baseline rates to test (default: 0.01 to 0.10)
    
    Returns:
        Dictionary containing sensitivity analysis results
    """
    if baseline_range is None:
        baseline_range = [0.01 * i for i in range(1, 11)]
    
    total = len(audit_records)
    if total == 0:
        return {
            "baseline_rates": baseline_range,
            "inconsistent_counts": [],
            "inconsistent_rates": [],
            "wilson_ci_ranges": [],
            "max_variation": 0.0
        }
    
    inconsistent_counts = []
    inconsistent_rates = []
    wilson_ci_ranges = []
    
    for rate in baseline_range:
        # Count records that would be flagged at this threshold
        # For this analysis, we use the reported p-value difference threshold
        # and see how many records exceed varying multiples of the threshold
        threshold = 0.05 * rate  # Varying threshold based on baseline
        count = sum(1 for r in audit_records 
                   if r.get("p_value_difference", 0) > threshold)
        
        inconsistent_counts.append(count)
        inconsistent_rates.append(count / total if total > 0 else 0.0)
        
        ci_lower, ci_upper = wilson_ci(count, total)
        wilson_ci_ranges.append(ci_upper - ci_lower)
    
    # Calculate max variation in prevalence rates
    if inconsistent_rates:
        max_variation = max(inconsistent_rates) - min(inconsistent_rates)
    else:
        max_variation = 0.0
    
    return {
        "baseline_rates": baseline_range,
        "inconsistent_counts": inconsistent_counts,
        "inconsistent_rates": inconsistent_rates,
        "wilson_ci_ranges": wilson_ci_ranges,
        "max_variation": max_variation,
        "threshold_range_description": f"Threshold varied from {0.05 * baseline_range[0]:.4f} to {0.05 * baseline_range[-1]:.4f}"
    }

def apply_dynamic_bonferroni(
    audit_records: List[Dict[str, Any]], 
    num_subgroups: int
) -> Dict[str, Any]:
    """
    Apply dynamic Bonferroni correction for multiple subgroup comparisons.
    
    Args:
        audit_records: List of audit records
        num_subgroups: Number of subgroups being tested
    
    Returns:
        Dictionary containing corrected alpha and adjusted p-values
    """
    alpha = 0.05
    corrected_alpha = alpha / num_subgroups if num_subgroups > 0 else alpha
    
    adjusted_pvalues = []
    for record in audit_records:
        raw_pvalue = record.get("binomial_pvalue", 1.0)
        adjusted = min(raw_pvalue * num_subgroups, 1.0)
        adjusted_pvalues.append(adjusted)
    
    return {
        "original_alpha": alpha,
        "num_subgroups": num_subgroups,
        "corrected_alpha": corrected_alpha,
        "adjusted_pvalues": adjusted_pvalues,
        "significance_threshold": corrected_alpha
    }

def load_audit_records(input_path: str = "code/output/audit_report.json") -> List[Dict[str, Any]]:
    """
    Load audit records from JSON file.
    
    Args:
        input_path: Path to audit report JSON
    
    Returns:
        List of audit records
    """
    logger = get_default_logger()
    
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
            
        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "records" in data:
            return data["records"]
        else:
            logger.warning(f"Unexpected JSON structure in {input_path}")
            return []
            
    except FileNotFoundError:
        logger.error(f"Audit report not found: {input_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {input_path}: {e}")
        return []

def write_prevalence_results(
    results: Dict[str, Any],
    output_path: str = "code/output/prevalence.json"
) -> None:
    """
    Write prevalence analysis results to JSON file.
    
    Args:
        results: Dictionary containing all prevalence results
        output_path: Output file path
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger = get_default_logger()
    logger.info(f"Prevalence results written to {output_path}")

def run_prevalence_analysis(
    input_path: str = "code/output/audit_report.json",
    output_path: str = "code/output/prevalence.json"
) -> Dict[str, Any]:
    """
    Run complete prevalence analysis including sensitivity analysis.
    
    Args:
        input_path: Path to audit report JSON
        output_path: Path for output JSON
    
    Returns:
        Dictionary containing all analysis results
    """
    set_rng_seed_for_prevalence()
    logger = get_default_logger()
    
    logger.info("Loading audit records...")
    audit_records = load_audit_records(input_path)
    
    if not audit_records:
        logger.warning("No audit records found. Writing empty results.")
        results = {
            "prevalence": compute_prevalence([]),
            "sensitivity_analysis": sensitivity_analysis([]),
            "bonferroni_correction": {
                "original_alpha": 0.05,
                "num_subgroups": 0,
                "corrected_alpha": 0.05,
                "adjusted_pvalues": [],
                "significance_threshold": 0.05
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "input_file": input_path,
                "output_file": output_path,
                "records_processed": 0
            }
        }
        write_prevalence_results(results, output_path)
        return results
    
    logger.info(f"Processing {len(audit_records)} audit records...")
    
    # Compute overall prevalence
    prevalence = compute_prevalence(audit_records)
    logger.info(f"Inconsistency rate: {prevalence['inconsistent_rate']:.4f}")
    
    # Perform sensitivity analysis
    sensitivity = sensitivity_analysis(audit_records)
    logger.info(f"Sensitivity analysis max variation: {sensitivity['max_variation']:.4f}")
    
    # Apply Bonferroni correction (assuming 5 subgroups for initial run)
    num_subgroups = 5  # Default subgroups: domain, year, outcome_type, etc.
    bonferroni = apply_dynamic_bonferroni(audit_records, num_subgroups)
    
    # Compile results
    results = {
        "prevalence": prevalence,
        "sensitivity_analysis": sensitivity,
        "bonferroni_correction": bonferroni,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "input_file": input_path,
            "output_file": output_path,
            "records_processed": len(audit_records),
            "random_seed": SEED
        }
    }
    
    write_prevalence_results(results, output_path)
    logger.info("Prevalence analysis completed successfully.")
    
    return results

def main():
    """Main entry point for prevalence analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run prevalence analysis on audit results")
    parser.add_argument(
        "--input", 
        type=str, 
        default="code/output/audit_report.json",
        help="Path to input audit report JSON"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="code/output/prevalence.json",
        help="Path for output prevalence JSON"
    )
    
    args = parser.parse_args()
    
    logger = get_default_logger()
    logger.info("Starting prevalence analysis...")
    
    results = run_prevalence_analysis(args.input, args.output)
    
    # Print summary
    print("\n=== Prevalence Analysis Summary ===")
    print(f"Total records: {results['prevalence']['total_summaries']}")
    print(f"Inconsistent count: {results['prevalence']['inconsistent_count']}")
    print(f"Inconsistent rate: {results['prevalence']['inconsistent_rate']:.4f}")
    print(f"Wilson CI: [{results['prevalence']['wilson_ci_lower']:.4f}, {results['prevalence']['wilson_ci_upper']:.4f}]")
    print(f"Sensitivity max variation: {results['sensitivity_analysis']['max_variation']:.4f}")
    print(f"Bonferroni corrected alpha: {results['bonferroni_correction']['corrected_alpha']:.4f}")
    print(f"Output written to: {args.output}")

if __name__ == "__main__":
    main()