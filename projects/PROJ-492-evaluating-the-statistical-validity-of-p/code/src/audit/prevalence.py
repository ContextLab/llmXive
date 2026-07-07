"""
Prevalence analysis module for A/B test audit.
Implements binomial prevalence test, Wilson CI, sensitivity analysis,
and dynamic Bonferroni correction.
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

logger = get_default_logger(__name__)


def set_rng_seed_for_prevalence(seed: int = SEED) -> None:
    """Set RNG seed for reproducibility in prevalence calculations."""
    set_rng_seed(seed)


def binomial_test(
    successes: int,
    n: int,
    p0: float = 0.5
) -> float:
    """
    Perform a binomial test for observed successes against a null probability p0.
    Uses the two-sided exact binomial test from scipy.

    Args:
        successes: Number of successes observed.
        n: Total number of trials.
        p0: Null hypothesis probability of success.

    Returns:
        Two-sided p-value from the exact binomial test.
    """
    if n <= 0:
        logger.warning(f"Invalid sample size n={n} for binomial test.")
        return 1.0
    if successes < 0 or successes > n:
        logger.warning(f"Invalid successes={successes} for n={n}.")
        return 1.0

    # scipy.stats.binomtest is the recommended modern API
    result = stats.binomtest(successes, n, p=p0, alternative='two-sided')
    return result.pvalue


def wilson_ci(
    successes: int,
    n: int,
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate the Wilson score confidence interval for a proportion.

    Args:
        successes: Number of successes observed.
        n: Total number of trials.
        alpha: Significance level (default 0.05 for 95% CI).

    Returns:
        Tuple (lower_bound, upper_bound) of the confidence interval.
    """
    if n <= 0:
        logger.warning(f"Invalid sample size n={n} for Wilson CI.")
        return (0.0, 0.0)
    if successes < 0 or successes > n:
        logger.warning(f"Invalid successes={successes} for n={n}.")
        return (0.0, 0.0)

    z = stats.norm.ppf(1 - alpha / 2)
    p_hat = successes / n

    denominator = 1 + (z ** 2) / n
    center = p_hat + (z ** 2) / (2 * n)
    margin = z * np.sqrt(
        (p_hat * (1 - p_hat) / n) + ((z ** 2) / (4 * n ** 2))
    )

    lower = (center - margin) / denominator
    upper = (center + margin) / denominator

    # Clamp to [0, 1]
    return (float(max(0.0, lower)), float(min(1.0, upper)))


def compute_prevalence(
    audit_records: List[Dict[str, Any]],
    inconsistency_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Compute overall prevalence of inconsistent A/B test summaries.

    Args:
        audit_records: List of audit record dictionaries.
        inconsistency_threshold: Threshold for p-value difference to flag inconsistency.

    Returns:
        Dictionary containing total count, inconsistent count, prevalence rate,
        and Wilson CI bounds.
    """
    if not audit_records:
        return {
            "total_summaries": 0,
            "inconsistent_count": 0,
            "inconsistent_rate": 0.0,
            "wilson_ci_lower": 0.0,
            "wilson_ci_upper": 0.0
        }

    inconsistent_count = sum(
        1 for r in audit_records
        if r.get("is_inconsistent", False)
    )
    total = len(audit_records)
    rate = inconsistent_count / total if total > 0 else 0.0

    lower, upper = wilson_ci(inconsistent_count, total)

    return {
        "total_summaries": total,
        "inconsistent_count": inconsistent_count,
        "inconsistent_rate": rate,
        "wilson_ci_lower": lower,
        "wilson_ci_upper": upper
    }


def sensitivity_analysis(
    audit_records: List[Dict[str, Any]],
    baseline_range: List[float] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on prevalence estimates by varying the
    definition of inconsistency (baseline threshold).

    Args:
        audit_records: List of audit record dictionaries.
        baseline_range: List of p-value difference thresholds to test.
                        Defaults to [0.01, 0.02, 0.05, 0.10].

    Returns:
        Dictionary mapping each threshold to its prevalence estimate and CI.
        Includes a 'max_variation' field indicating the range of variation.
    """
    if baseline_range is None:
        baseline_range = [0.01, 0.02, 0.05, 0.10]

    results = {}
    rates = []

    for threshold in baseline_range:
        count = sum(
            1 for r in audit_records
            if r.get("p_value_difference", 0.0) > threshold
        )
        total = len(audit_records)
        rate = count / total if total > 0 else 0.0
        lower, upper = wilson_ci(count, total)

        results[str(threshold)] = {
            "threshold": threshold,
            "inconsistent_count": count,
            "inconsistent_rate": rate,
            "wilson_ci_lower": lower,
            "wilson_ci_upper": upper
        }
        rates.append(rate)

    max_variation = max(rates) - min(rates) if rates else 0.0

    return {
        "thresholds_tested": baseline_range,
        "results": results,
        "max_variation": max_variation,
        "max_variation_acceptable": max_variation < 0.02
    }


def apply_dynamic_bonferroni(
    num_subgroups: int,
    alpha: float = 0.05
) -> float:
    """
    Apply dynamic Bonferroni correction for multiple subgroup comparisons.

    Args:
        num_subgroups: Number of subgroups being tested.
        alpha: Original significance level.

    Returns:
        Adjusted alpha threshold.
    """
    if num_subgroups <= 0:
        logger.warning(f"Invalid num_subgroups={num_subgroups} for Bonferroni.")
        return alpha
    return alpha / num_subgroups


def load_audit_records(input_path: Path) -> List[Dict[str, Any]]:
    """Load audit records from a JSON file."""
    if not input_path.exists():
        logger.error(f"Audit report not found: {input_path}")
        return []

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "records" in data:
        return data["records"]
    else:
        logger.warning("Unexpected audit report format, attempting to parse as records.")
        return [data] if data else []


def write_prevalence_results(
    output_path: Path,
    prevalence_data: Dict[str, Any],
    sensitivity_data: Dict[str, Any],
    bonferroni_alpha: float
) -> None:
    """Write prevalence analysis results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "prevalence": prevalence_data,
        "sensitivity_analysis": sensitivity_data,
        "dynamic_bonferroni_alpha": bonferroni_alpha
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Prevalence results written to {output_path}")


def run_prevalence_analysis(
    input_path: Path,
    output_path: Path,
    num_subgroups: int = 1
) -> Dict[str, Any]:
    """
    Run full prevalence analysis pipeline.

    Args:
        input_path: Path to audit_report.json.
        output_path: Path for output prevalence.json.
        num_subgroups: Number of subgroups for Bonferroni correction.

    Returns:
        Dictionary with analysis results.
    """
    set_rng_seed_for_prevalence()
    logger.info(f"Loading audit records from {input_path}")

    records = load_audit_records(input_path)
    if not records:
        logger.warning("No audit records found. Writing empty result.")
        write_prevalence_results(
            output_path,
            {"total_summaries": 0, "inconsistent_count": 0, "inconsistent_rate": 0.0},
            {"results": {}, "max_variation": 0.0},
            0.05
        )
        return {}

    # Compute overall prevalence
    prevalence = compute_prevalence(records)
    logger.info(f"Prevalence: {prevalence['inconsistent_rate']:.2%} ({prevalence['inconsistent_count']}/{prevalence['total_summaries']})")

    # Sensitivity analysis
    sensitivity = sensitivity_analysis(records)
    logger.info(f"Sensitivity max variation: {sensitivity['max_variation']:.4f}")

    # Dynamic Bonferroni
    bonferroni_alpha = apply_dynamic_bonferroni(num_subgroups)
    logger.info(f"Dynamic Bonferroni alpha: {bonferroni_alpha}")

    # Write results
    write_prevalence_results(output_path, prevalence, sensitivity, bonferroni_alpha)

    return {
        "prevalence": prevalence,
        "sensitivity": sensitivity,
        "bonferroni_alpha": bonferroni_alpha
    }


def main() -> int:
    """Main entry point for prevalence analysis script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute prevalence, Wilson CI, sensitivity analysis, and Bonferroni correction."
    )
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
        "--subgroups",
        type=int,
        default=1,
        help="Number of subgroups for dynamic Bonferroni correction"
    )

    args = parser.parse_args()

    try:
        run_prevalence_analysis(args.input, args.output, args.subgroups)
        return 0
    except Exception as e:
        logger.error(f"Prevalence analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
