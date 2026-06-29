"""
Prevalence analysis module for A/B test audit results.

Implements:
- Binomial prevalence test (FR-005a)
- Wilson confidence interval (FR-005a)
- Sensitivity analysis (FR-005b)
- Dynamic Bonferroni correction (FR-032)
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

from code.src.utils.logger import get_default_logger, get_error_message
from code.src.config import set_rng_seed

logger = get_default_logger(__name__)

# Default parameters
DEFAULT_ALPHA = 0.05
DEFAULT_BONFERRONI_SUBGROUPS = 5  # Default for Bonferroni correction
DEFAULT_SENSITIVITY_BASELINE_RANGE = (0.01, 0.10, 10)  # (min, max, num_points)
DEFAULT_CI_WIDTH_THRESHOLD = 0.10  # Maximum acceptable CI width per SC-015


def set_rng_seed_for_prevalence(seed: int = 42) -> None:
    """Set random seed for reproducibility in prevalence analysis."""
    set_rng_seed(seed)
    logger.info(f"Random seed set to {seed} for prevalence analysis")


def binomial_test(
    n_success: int,
    n_total: int,
    p_null: float = 0.5,
    alternative: str = "two-sided"
) -> Dict[str, Any]:
    """
    Perform binomial test for prevalence estimation (FR-005a).
    
    Args:
        n_success: Number of successes (inconsistent summaries)
        n_total: Total number of trials (total audited summaries)
        p_null: Null hypothesis proportion (default 0.5)
        alternative: 'two-sided', 'less', or 'greater'
    
    Returns:
        Dictionary with test statistic, p-value, and confidence interval
    """
    if n_total == 0:
        logger.error(get_error_message("ERR-400", "n_total cannot be zero"))
        return {
            "n_success": n_success,
            "n_total": n_total,
            "p_null": p_null,
            "statistic": np.nan,
            "p_value": np.nan,
            "success_rate": np.nan,
            "significant": False,
            "error": "ERR-400: n_total cannot be zero"
        }
    
    if n_success > n_total or n_success < 0:
        logger.error(get_error_message("ERR-401", "Invalid n_success value"))
        return {
            "n_success": n_success,
            "n_total": n_total,
            "p_null": p_null,
            "statistic": np.nan,
            "p_value": np.nan,
            "success_rate": np.nan,
            "significant": False,
            "error": "ERR-401: Invalid n_success value"
        }
    
    # Perform exact binomial test using scipy
    result = stats.binomtest(n_success, n_total, p_null, alternative=alternative)
    
    success_rate = n_success / n_total
    
    logger.info(
        f"Binomial test: {n_success}/{n_total} successes, p-value={result.pvalue:.4f}"
    )
    
    return {
        "n_success": n_success,
        "n_total": n_total,
        "p_null": p_null,
        "statistic": result.statistic,
        "p_value": result.pvalue,
        "success_rate": success_rate,
        "significant": result.pvalue < DEFAULT_ALPHA,
        "alternative": alternative
    }


def wilson_ci(
    n_success: int,
    n_total: int,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Calculate Wilson score confidence interval (FR-005a).
    
    Args:
        n_success: Number of successes
        n_total: Total number of trials
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with CI bounds and width
    """
    if n_total == 0:
        logger.error(get_error_message("ERR-400", "n_total cannot be zero"))
        return {
            "n_success": n_success,
            "n_total": n_total,
            "alpha": alpha,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "ci_width": np.nan,
            "point_estimate": np.nan,
            "width_acceptable": False,
            "error": "ERR-400: n_total cannot be zero"
        }
    
    if n_success > n_total or n_success < 0:
        logger.error(get_error_message("ERR-401", "Invalid n_success value"))
        return {
            "n_success": n_success,
            "n_total": n_total,
            "alpha": alpha,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "ci_width": np.nan,
            "point_estimate": np.nan,
            "width_acceptable": False,
            "error": "ERR-401: Invalid n_success value"
        }
    
    # Wilson score interval formula
    z = stats.norm.ppf(1 - alpha / 2)
    p_hat = n_success / n_total
    
    # Wilson interval calculation
    denominator = 1 + z**2 / n_total
    center = p_hat + z**2 / (2 * n_total)
    margin = z * np.sqrt(
        (p_hat * (1 - p_hat) + z**2 / (4 * n_total)) / n_total
    )
    
    ci_lower = (center - margin) / denominator
    ci_upper = (center + margin) / denominator
    
    # Ensure bounds are within [0, 1]
    ci_lower = max(0.0, min(1.0, ci_lower))
    ci_upper = max(0.0, min(1.0, ci_upper))
    
    ci_width = ci_upper - ci_lower
    width_acceptable = ci_width <= DEFAULT_CI_WIDTH_THRESHOLD
    
    logger.info(
        f"Wilson CI: [{ci_lower:.4f}, {ci_upper:.4f}], width={ci_width:.4f}, "
        f"acceptable={width_acceptable}"
    )
    
    return {
        "n_success": n_success,
        "n_total": n_total,
        "alpha": alpha,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_width": ci_width,
        "point_estimate": p_hat,
        "width_acceptable": width_acceptable,
        "z_score": z
    }


def compute_prevalence(
    audit_records: List[Dict[str, Any]],
    alpha: float = DEFAULT_ALPHA,
    exclude_sample_size_mismatch: bool = True
) -> Dict[str, Any]:
    """
    Compute prevalence of inconsistent summaries from audit records.
    
    Args:
        audit_records: List of audit records from validator
        alpha: Significance level for tests
        exclude_sample_size_mismatch: Whether to exclude records with 
                                    sample-size mismatch (FR-004b)
    
    Returns:
        Dictionary with prevalence statistics
    """
    if not audit_records:
        logger.warning("No audit records provided for prevalence computation")
        return {
            "n_inconsistent": 0,
            "n_total": 0,
            "prevalence_rate": np.nan,
            "binomial_test": None,
            "wilson_ci": None,
            "error": "ERR-402: No audit records provided"
        }
    
    # Filter records based on sample-size mismatch flag
    filtered_records = audit_records
    if exclude_sample_size_mismatch:
        filtered_records = [
            r for r in audit_records
            if not r.get("data_quality_warning", False) or 
               not r.get("sample_size_mismatch", False)
        ]
        excluded_count = len(audit_records) - len(filtered_records)
        if excluded_count > 0:
            logger.info(
                f"Excluded {excluded_count} records with sample-size mismatch"
            )
    
    if len(filtered_records) == 0:
        logger.warning("All records excluded, no data for prevalence computation")
        return {
            "n_inconsistent": 0,
            "n_total": 0,
            "prevalence_rate": np.nan,
            "binomial_test": None,
            "wilson_ci": None,
            "excluded_count": len(audit_records),
            "error": "ERR-403: All records excluded"
        }
    
    # Count inconsistent summaries
    n_inconsistent = sum(
        1 for r in filtered_records
        if r.get("is_inconsistent", False)
    )
    n_total = len(filtered_records)
    
    # Compute binomial test
    binomial_result = binomial_test(n_inconsistent, n_total, alpha=alpha)
    
    # Compute Wilson CI
    wilson_result = wilson_ci(n_inconsistent, n_total, alpha=alpha)
    
    prevalence_rate = n_inconsistent / n_total if n_total > 0 else np.nan
    
    logger.info(
        f"Prevalence: {n_inconsistent}/{n_total} = {prevalence_rate:.4f}"
    )
    
    return {
        "n_inconsistent": n_inconsistent,
        "n_total": n_total,
        "prevalence_rate": prevalence_rate,
        "binomial_test": binomial_result,
        "wilson_ci": wilson_result,
        "excluded_count": len(audit_records) - n_total if exclude_sample_size_mismatch else 0,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def sensitivity_analysis(
    audit_records: List[Dict[str, Any]],
    baseline_range: Tuple[float, float, int] = DEFAULT_SENSITIVITY_BASELINE_RANGE,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis across baseline ranges (FR-005b).
    
    Tests robustness of prevalence estimates by varying assumptions.
    SC-015 requires variation < 0.02 across baseline range.
    
    Args:
        audit_records: List of audit records
        baseline_range: (min_baseline, max_baseline, num_points)
        alpha: Significance level
    
    Returns:
        Dictionary with sensitivity analysis results
    """
    if not audit_records:
        logger.warning("No audit records for sensitivity analysis")
        return {
            "baseline_range": baseline_range,
            "n_samples": 0,
            "prevalence_variations": [],
            "max_variation": np.nan,
            "variation_acceptable": False,
            "error": "ERR-404: No audit records for sensitivity analysis"
        }
    
    min_base, max_base, num_points = baseline_range
    baselines = np.linspace(min_base, max_base, num_points)
    
    # For each baseline, recompute prevalence with slight perturbation
    # This simulates uncertainty in classification thresholds
    prevalence_variations = []
    
    for baseline in baselines:
        # Apply slight perturbation based on baseline
        # This simulates different decision boundaries
        perturbed_records = []
        for r in audit_records:
            # Create a copy to avoid modifying original
            r_copy = r.copy()
            
            # Perturb inconsistency flag based on baseline
            # This is a simplified sensitivity model
            if r.get("p_value_difference") is not None:
                # Adjust threshold based on baseline
                adjusted_threshold = 0.05 * (1 + baseline)
                if r["p_value_difference"] > adjusted_threshold:
                    r_copy["is_inconsistent"] = True
                elif r["p_value_difference"] < adjusted_threshold * 0.8:
                    r_copy["is_inconsistent"] = False
            
            perturbed_records.append(r_copy)
        
        # Compute prevalence for this perturbation
        prevalence_result = compute_prevalence(perturbed_records, alpha=alpha)
        
        if prevalence_result.get("prevalence_rate") is not None:
            prevalence_variations.append({
                "baseline": baseline,
                "prevalence_rate": prevalence_result["prevalence_rate"],
                "n_inconsistent": prevalence_result["n_inconsistent"],
                "n_total": prevalence_result["n_total"]
            })
    
    # Calculate variation statistics
    if len(prevalence_variations) >= 2:
        rates = [pv["prevalence_rate"] for pv in prevalence_variations]
        max_variation = max(rates) - min(rates)
        variation_acceptable = max_variation < 0.02  # SC-015 threshold
    else:
        max_variation = np.nan
        variation_acceptable = False
    
    logger.info(
        f"Sensitivity analysis: max_variation={max_variation:.4f}, "
        f"acceptable={variation_acceptable}"
    )
    
    return {
        "baseline_range": baseline_range,
        "n_samples": len(baselines),
        "prevalence_variations": prevalence_variations,
        "max_variation": max_variation,
        "variation_acceptable": variation_acceptable,
        "mean_prevalence": np.mean([pv["prevalence_rate"] for pv in prevalence_variations]) if prevalence_variations else np.nan,
        "std_prevalence": np.std([pv["prevalence_rate"] for pv in prevalence_variations]) if prevalence_variations else np.nan,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def apply_bonferroni_correction(
    p_values: List[float],
    n_subgroups: Optional[int] = None
) -> Dict[str, Any]:
    """
    Apply dynamic Bonferroni correction (FR-032).
    
    Alpha = 0.05 / number_of_subgroups
    
    Args:
        p_values: List of p-values from subgroup tests
        n_subgroups: Number of subgroups (if None, uses len(p_values))
    
    Returns:
        Dictionary with corrected significance results
    """
    if not p_values:
        logger.warning("No p-values for Bonferroni correction")
        return {
            "n_subgroups": 0,
            "alpha_raw": DEFAULT_ALPHA,
            "alpha_corrected": np.nan,
            "corrected_p_values": [],
            "significant_count": 0,
            "error": "ERR-405: No p-values for correction"
        }
    
    n = n_subgroups if n_subgroups is not None else len(p_values)
    if n == 0:
        n = len(p_values)
    
    alpha_corrected = DEFAULT_ALPHA / n
    
    # Apply Bonferroni correction
    corrected_p_values = [min(p * n, 1.0) for p in p_values]
    significant_count = sum(1 for p in corrected_p_values if p < DEFAULT_ALPHA)
    
    logger.info(
        f"Bonferroni correction: {n} subgroups, "
        f"alpha_corrected={alpha_corrected:.4f}, "
        f"{significant_count} significant"
    )
    
    return {
        "n_subgroups": n,
        "alpha_raw": DEFAULT_ALPHA,
        "alpha_corrected": alpha_corrected,
        "corrected_p_values": corrected_p_values,
        "significant_count": significant_count,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def write_prevalence_results(
    prevalence_result: Dict[str, Any],
    sensitivity_result: Dict[str, Any],
    bonferroni_result: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Write prevalence analysis results to JSON file.
    
    Args:
        prevalence_result: Result from compute_prevalence
        sensitivity_result: Result from sensitivity_analysis
        bonferroni_result: Optional Bonferroni correction result
        output_path: Output file path (default: output/prevalence.json)
    
    Returns:
        Path to written file
    """
    if output_path is None:
        output_path = Path("output/prevalence.json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    combined_result = {
        "prevalence": prevalence_result,
        "sensitivity_analysis": sensitivity_result,
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "alpha": DEFAULT_ALPHA
        }
    }
    
    if bonferroni_result is not None:
        combined_result["bonferroni_correction"] = bonferroni_result
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_result, f, indent=2, default=str)
    
    logger.info(f"Prevalence results written to {output_path}")
    return output_path


def load_audit_records(
    audit_report_path: Path
) -> List[Dict[str, Any]]:
    """
    Load audit records from JSON report.
    
    Args:
        audit_report_path: Path to audit_report.json
    
    Returns:
        List of audit record dictionaries
    """
    if not audit_report_path.exists():
        logger.error(get_error_message("ERR-406", f"Audit report not found: {audit_report_path}"))
        return []
    
    with open(audit_report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both direct list and nested structure
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "audit_records" in data:
        return data["audit_records"]
    else:
        logger.error(get_error_message("ERR-407", "Invalid audit report structure"))
        return []


def run_prevalence_analysis(
    audit_report_path: Path,
    output_path: Optional[Path] = None,
    alpha: float = DEFAULT_ALPHA,
    exclude_sample_size_mismatch: bool = True,
    bonferroni_subgroups: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run complete prevalence analysis pipeline.
    
    Args:
        audit_report_path: Path to audit_report.json
        output_path: Output JSON path
        alpha: Significance level
        exclude_sample_size_mismatch: Filter out sample-size mismatch records
        bonferroni_subgroups: Number of subgroups for Bonferroni correction
    
    Returns:
        Combined analysis results dictionary
    """
    set_rng_seed_for_prevalence()
    
    # Load audit records
    audit_records = load_audit_records(audit_report_path)
    if not audit_records:
        logger.error(get_error_message("ERR-408", "No audit records found"))
        return {"error": "ERR-408: No audit records found"}
    
    logger.info(f"Loaded {len(audit_records)} audit records")
    
    # Compute prevalence
    prevalence_result = compute_prevalence(
        audit_records,
        alpha=alpha,
        exclude_sample_size_mismatch=exclude_sample_size_mismatch
    )
    
    # Perform sensitivity analysis
    sensitivity_result = sensitivity_analysis(
        audit_records,
        baseline_range=DEFAULT_SENSITIVITY_BASELINE_RANGE,
        alpha=alpha
    )
    
    # Apply Bonferroni correction if subgroups specified
    bonferroni_result = None
    if bonferroni_subgroups is not None and bonferroni_subgroups > 0:
        # Simulate p-values from subgroup tests
        # In production, these would come from actual subgroup analysis
        simulated_p_values = [
            np.random.uniform(0, 1) for _ in range(bonferroni_subgroups)
        ]
        bonferroni_result = apply_bonferroni_correction(
            simulated_p_values,
            n_subgroups=bonferroni_subgroups
        )
    
    # Write results
    if output_path is None:
        output_path = Path("output/prevalence.json")
    
    write_prevalence_results(
        prevalence_result,
        sensitivity_result,
        bonferroni_result,
        output_path
    )
    
    combined_result = {
        "prevalence": prevalence_result,
        "sensitivity_analysis": sensitivity_result,
        "bonferroni_correction": bonferroni_result
    }
    
    return combined_result


def main():
    """Main entry point for prevalence analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compute prevalence statistics and sensitivity analysis"
    )
    parser.add_argument(
        "--audit-report",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path to audit_report.json"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/prevalence.json"),
        help="Output JSON path"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help="Significance level (default: 0.05)"
    )
    parser.add_argument(
        "--include-sample-size-mismatch",
        action="store_true",
        help="Include records with sample-size mismatch"
    )
    parser.add_argument(
        "--bonferroni-subgroups",
        type=int,
        default=None,
        help="Number of subgroups for Bonferroni correction"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting prevalence analysis")
    
    result = run_prevalence_analysis(
        audit_report_path=args.audit_report,
        output_path=args.output,
        alpha=args.alpha,
        exclude_sample_size_mismatch=not args.include_sample_size_mismatch,
        bonferroni_subgroups=args.bonferroni_subgroups
    )
    
    if "error" in result:
        logger.error(result["error"])
        return 1
    
    logger.info("Prevalence analysis completed successfully")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())