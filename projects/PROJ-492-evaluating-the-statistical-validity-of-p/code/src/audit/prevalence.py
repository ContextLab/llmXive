"""
Prevalence analysis module implementing binomial tests, Wilson CI, sensitivity analysis,
and dynamic Bonferroni correction as per FR-005a, FR-005b, and FR-032.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

logger: logging.Logger = get_default_logger(__name__)
audit_logger: AuditLogger = AuditLogger()


def set_rng_seed_for_prevalence(seed: int = SEED) -> None:
    """Set random seed for reproducibility in prevalence calculations."""
    set_rng_seed(seed)
    logger.info(f"Random seed set to {seed} for prevalence analysis")


def binomial_test(successes: int, trials: int, p: float = 0.5) -> float:
    """
    Compute the two-sided binomial test p-value.
    
    Args:
        successes: Number of observed successes (inconsistent audits)
        trials: Total number of trials (total audits)
        p: Null hypothesis probability of success
        
    Returns:
        Two-sided p-value from the binomial test
    """
    if trials == 0:
        return 1.0
    
    # Use scipy.stats.binom_test (deprecated in newer scipy, use binomtest for v1.7+)
    # Fallback to manual calculation if needed, but scipy is robust
    try:
        # For scipy >= 1.9.0, use binomtest
        if hasattr(stats, 'binomtest'):
            result = stats.binomtest(successes, trials, p=p, alternative='two-sided')
            return result.pvalue
        else:
            # Fallback for older scipy versions
            return stats.binom_test(successes, trials, p=p, alternative='two-sided')
    except Exception as e:
        audit_logger.log_error("ERR-501", f"Binomial test calculation failed: {str(e)}")
        raise


def wilson_ci(successes: int, trials: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Compute the Wilson score confidence interval for a proportion.
    
    Args:
        successes: Number of successes
        trials: Total number of trials
        confidence: Confidence level (e.g., 0.95 for 95% CI)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if trials == 0:
        return (0.0, 1.0)
    
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    phat = successes / trials
    
    denominator = 1 + z**2 / trials
    centre_adjusted_probability = phat + z**2 / (2 * trials)
    adjusted_standard_deviation = np.sqrt((phat * (1 - phat) / trials) + (z**2 / (4 * trials**2)))
    
    lower = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
    upper = (centre_adjusted_probability + z * adjusted_standard_deviation) / denominator
    
    # Clamp to [0, 1]
    lower = max(0.0, min(1.0, lower))
    upper = max(0.0, min(1.0, upper))
    
    return (lower, upper)


def compute_prevalence(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute prevalence statistics from audit records.
    
    Args:
        records: List of audit records from audit_report.json
        
    Returns:
        Dictionary containing prevalence statistics
    """
    if not records:
        return {
            "total_summaries": 0,
            "inconsistent_count": 0,
            "inconsistent_rate": 0.0,
            "wilson_ci_lower": 0.0,
            "wilson_ci_upper": 1.0,
            "binomial_pvalue": 1.0
        }
    
    total = len(records)
    inconsistent = sum(1 for r in records if r.get("is_inconsistent", False))
    
    rate = inconsistent / total if total > 0 else 0.0
    lower, upper = wilson_ci(inconsistent, total)
    pval = binomial_test(inconsistent, total)
    
    return {
        "total_summaries": total,
        "inconsistent_count": inconsistent,
        "inconsistent_rate": rate,
        "wilson_ci_lower": lower,
        "wilson_ci_upper": upper,
        "binomial_pvalue": pval
    }


def sensitivity_analysis(
    records: List[Dict[str, Any]], 
    baseline_range: Tuple[float, float] = (0.01, 0.50), 
    step: float = 0.01
) -> List[Dict[str, Any]]:
    """
    Perform sensitivity analysis by varying the baseline inconsistency rate.
    Computes how the Wilson CI and p-value change across different assumed baselines.
    
    Args:
        records: List of audit records
        baseline_range: Tuple of (min_baseline, max_baseline)
        step: Step size for baseline variation
        
    Returns:
        List of sensitivity analysis results for each baseline
    """
    results = []
    total = len(records)
    inconsistent = sum(1 for r in records if r.get("is_inconsistent", False))
    
    if total == 0:
        return results
    
    current_baseline = baseline_range[0]
    while current_baseline <= baseline_range[1] + 1e-9:  # Floating point tolerance
        # Simulate what the CI would look like if the observed rate matched this baseline
        # This helps assess robustness of the conclusion
        simulated_successes = int(total * current_baseline)
        
        lower, upper = wilson_ci(simulated_successes, total)
        pval = binomial_test(simulated_successes, total)
        
        results.append({
            "assumed_baseline": round(current_baseline, 4),
            "simulated_inconsistent_count": simulated_successes,
            "wilson_ci_lower": round(lower, 4),
            "wilson_ci_upper": round(upper, 4),
            "binomial_pvalue": round(pval, 4),
            "ci_width": round(upper - lower, 4)
        })
        
        current_baseline += step
        
    return results


def apply_dynamic_bonferroni(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply dynamic Bonferroni correction based on the number of subgroups/tests.
    Per FR-032: alpha_corrected = 0.05 / number_of_subgroups
    
    Args:
        p_values: List of raw p-values from subgroup tests
        alpha: Original significance level (default 0.05)
        
    Returns:
        Dictionary with corrected alpha, adjusted p-values, and significance flags
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {
            "original_alpha": alpha,
            "corrected_alpha": alpha,
            "adjusted_p_values": [],
            "significant_count": 0,
            "non_significant_count": 0
        }
    
    corrected_alpha = alpha / n_tests
    adjusted_p_values = [min(p * n_tests, 1.0) for p in p_values]
    
    significant = sum(1 for p in adjusted_p_values if p < corrected_alpha)
    non_significant = n_tests - significant
    
    return {
        "original_alpha": alpha,
        "corrected_alpha": round(corrected_alpha, 6),
        "n_tests": n_tests,
        "adjusted_p_values": [round(p, 6) for p in adjusted_p_values],
        "significant_count": significant,
        "non_significant_count": non_significant,
        "significant_flags": [p < corrected_alpha for p in adjusted_p_values]
    }


def load_audit_records(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load audit records from the JSON report file.
    Excludes records flagged for sample-size mismatch per FR-004b/T025c.
    
    Args:
        input_path: Path to audit_report.json
        
    Returns:
        List of valid audit records
    """
    if not input_path.exists():
        audit_logger.log_error("ERR-502", f"Audit report file not found: {input_path}")
        return []
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        audit_logger.log_error("ERR-503", f"Failed to parse audit report JSON: {str(e)}")
        return []
    
    records = data.get("records", []) if isinstance(data, dict) else data
    
    # Filter out records with sample_size_mismatch warning
    valid_records = [
        r for r in records 
        if not r.get("data_quality_warning", "").lower().find("sample_size") != -1
        and not r.get("flags", [])
        or not any("sample_size" in str(flag).lower() for flag in r.get("flags", []))
    ]
    
    # Double check via data_quality_warning field explicitly
    filtered_records = []
    for r in valid_records:
        warning = r.get("data_quality_warning", "")
        if "sample_size" not in str(warning).lower():
            filtered_records.append(r)
    
    logger.info(f"Loaded {len(filtered_records)} valid audit records (excluded sample-size mismatches)")
    return filtered_records


def write_prevalence_results(
    output_path: Path,
    prevalence_data: Dict[str, Any],
    sensitivity_data: List[Dict[str, Any]],
    bonferroni_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Write prevalence analysis results to JSON file.
    
    Args:
        output_path: Path to output JSON file
        prevalence_data: Main prevalence statistics
        sensitivity_data: Sensitivity analysis results
        bonferroni_data: Optional Bonferroni correction results
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "prevalence": prevalence_data,
        "sensitivity_analysis": sensitivity_data,
        "dynamic_bonferroni_correction": bonferroni_data if bonferroni_data else {}
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Prevalence results written to {output_path}")


def run_prevalence_analysis(
    input_path: Path,
    output_path: Path,
    sensitivity_range: Tuple[float, float] = (0.01, 0.50),
    sensitivity_step: float = 0.01,
    bonferroni_p_values: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Main entry point to run the full prevalence analysis pipeline.
    
    Args:
        input_path: Path to audit_report.json
        output_path: Path for output prevalence.json
        sensitivity_range: Range for sensitivity analysis
        sensitivity_step: Step size for sensitivity analysis
        bonferroni_p_values: Optional list of p-values for Bonferroni correction
        
    Returns:
        Dictionary containing the analysis results
    """
    set_rng_seed_for_prevalence()
    
    logger.info(f"Starting prevalence analysis on {input_path}")
    
    records = load_audit_records(input_path)
    
    if not records:
        audit_logger.log_error("ERR-504", "No valid audit records found for analysis")
        prevalence_data = {
            "total_summaries": 0,
            "inconsistent_count": 0,
            "inconsistent_rate": 0.0,
            "wilson_ci_lower": 0.0,
            "wilson_ci_upper": 1.0,
            "binomial_pvalue": 1.0
        }
        sensitivity_data = []
        bonferroni_data = None
    else:
        prevalence_data = compute_prevalence(records)
        sensitivity_data = sensitivity_analysis(records, sensitivity_range, sensitivity_step)
        
        if bonferroni_p_values:
            bonferroni_data = apply_dynamic_bonferroni(bonferroni_p_values)
        else:
            # Default: apply to all subgroup tests if we had them, but here we just note the capability
            bonferroni_data = apply_dynamic_bonferroni([])
    
    write_prevalence_results(output_path, prevalence_data, sensitivity_data, bonferroni_data)
    
    logger.info("Prevalence analysis completed successfully")
    return {
        "prevalence": prevalence_data,
        "sensitivity_analysis_count": len(sensitivity_data),
        "bonferroni_applied": bonferroni_data is not None
    }


def main() -> int:
    """
    CLI entry point for prevalence analysis.
    Reads from data/processed/audit_report.json and writes to output/prevalence.json.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run prevalence analysis on audit results")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("output/audit_report.json"),
        help="Path to audit_report.json"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("output/prevalence.json"),
        help="Path for output prevalence.json"
    )
    parser.add_argument(
        "--sensitivity-min", 
        type=float, 
        default=0.01,
        help="Minimum baseline for sensitivity analysis"
    )
    parser.add_argument(
        "--sensitivity-max", 
        type=float, 
        default=0.50,
        help="Maximum baseline for sensitivity analysis"
    )
    parser.add_argument(
        "--sensitivity-step", 
        type=float, 
        default=0.01,
        help="Step size for sensitivity analysis"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_prevalence_analysis(
            args.input,
            args.output,
            (args.sensitivity_min, args.sensitivity_max),
            args.sensitivity_step
        )
        print(f"Prevalence analysis completed. Output: {args.output}")
        print(f"Total summaries: {result['prevalence']['total_summaries']}")
        print(f"Inconsistent rate: {result['prevalence']['inconsistent_rate']:.4f}")
        return 0
    except Exception as e:
        audit_logger.log_error("ERR-505", f"Prevalence analysis failed: {str(e)}")
        logger.exception("Prevalence analysis error")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
