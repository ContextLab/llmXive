"""
Power analysis utility for computing minimum sample size requirements.

Implements FR-025: Computes the minimum N given baseline, detectable effect, alpha, and power.
Asserts audited corpus meets N >= 300 OR N >= calculated_minimum.
Writes result to output/power_analysis.json.
"""
import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

logger = get_default_logger(__name__)

def set_rng_seed_for_power_analysis():
    """Set random seed for reproducibility."""
    set_rng_seed(SEED)

def calculate_sample_size_binary(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True
) -> float:
    """
    Calculate minimum sample size per group for a two-proportion z-test.

    Args:
        baseline_rate: Expected baseline conversion rate (0 < p < 1)
        detectable_effect: Minimum detectable difference in proportions (absolute)
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
        two_sided: Whether to use two-sided test (default True)

    Returns:
        Minimum sample size per group (float, rounded up to int)
    """
    if not 0 < baseline_rate < 1:
        raise ValueError(f"baseline_rate must be between 0 and 1, got {baseline_rate}")
    if not 0 < detectable_effect < 1:
        raise ValueError(f"detectable_effect must be between 0 and 1, got {detectable_effect}")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be between 0 and 1, got {alpha}")
    if not 0 < power < 1:
        raise ValueError(f"power must be between 0 and 1, got {power}")

    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect

    if not 0 < p2 < 1:
        raise ValueError(f"Resulting rate p2 = {p2} is out of valid range (0, 1)")

    # Pooled proportion under null
    p_pooled = (p1 + p2) / 2

    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha / 2) if two_sided else stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)

    # Standard deviations
    std_null = np.sqrt(2 * p_pooled * (1 - p_pooled))
    std_alt = np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))

    # Sample size formula for two proportions
    # n = (z_alpha * std_null + z_beta * std_alt)^2 / (p2 - p1)^2
    numerator = (z_alpha * std_null + z_beta * std_alt) ** 2
    denominator = (p2 - p1) ** 2

    n = numerator / denominator
    return np.ceil(n)

def calculate_sample_size_continuous(
    baseline_mean: float,
    baseline_std: float,
    detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True
) -> float:
    """
    Calculate minimum sample size per group for a Welch's t-test (continuous outcome).

    Args:
        baseline_mean: Expected baseline mean (not directly used in n calculation but for context)
        baseline_std: Expected baseline standard deviation
        detectable_effect: Minimum detectable difference in means
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
        two_sided: Whether to use two-sided test (default True)

    Returns:
        Minimum sample size per group (float, rounded up to int)
    """
    if baseline_std <= 0:
        raise ValueError(f"baseline_std must be positive, got {baseline_std}")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be between 0 and 1, got {alpha}")
    if not 0 < power < 1:
        raise ValueError(f"power must be between 0 and 1, got {power}")

    # Effect size (Cohen's d)
    effect_size = detectable_effect / baseline_std

    if effect_size <= 0:
        raise ValueError(f"effect_size must be positive, got {effect_size}")

    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha / 2) if two_sided else stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)

    # Sample size formula for t-test (approximated by z-test for large n)
    # n = 2 * (z_alpha + z_beta)^2 / effect_size^2
    n = 2 * ((z_alpha + z_beta) ** 2) / (effect_size ** 2)

    return np.ceil(n)

def count_corpus_size(audit_records_path: Path) -> int:
    """
    Count the number of valid audit records in the corpus.

    Args:
        audit_records_path: Path to the audit_report.json file

    Returns:
        Number of records in the corpus
    """
    if not audit_records_path.exists():
        logger.warning(f"Audit report not found at {audit_records_path}. Returning 0.")
        return 0

    try:
        with open(audit_records_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict) and 'records' in data:
            return len(data['records'])
        else:
            logger.warning(f"Unexpected audit report structure at {audit_records_path}")
            return 0
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read audit report: {e}")
        return 0

def run_power_analysis(
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.05,
    alpha: float = 0.05,
    power: float = 0.80,
    audit_records_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    minimum_corpus_size: int = 300
) -> Dict[str, Any]:
    """
    Run power analysis to determine minimum sample size and validate corpus size.

    Args:
        baseline_rate: Baseline conversion rate for binary outcomes
        detectable_effect: Detectable effect size
        alpha: Significance level
        power: Desired power
        audit_records_path: Path to audit_report.json (optional, if None, corpus size is assumed 0)
        output_path: Path to write results (optional)
        minimum_corpus_size: Minimum required corpus size (default 300 per FR-025)

    Returns:
        Dictionary containing analysis results
    """
    set_rng_seed_for_power_analysis()

    # Calculate minimum sample size for binary outcome
    min_n_binary = calculate_sample_size_binary(
        baseline_rate=baseline_rate,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power
    )

    # Calculate minimum sample size for continuous outcome (assuming std=0.5 as default)
    min_n_continuous = calculate_sample_size_continuous(
        baseline_mean=0.0,
        baseline_std=0.5,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power
    )

    # Use the more conservative (larger) requirement
    calculated_minimum = max(int(min_n_binary), int(min_n_continuous))

    # Get actual corpus size
    actual_corpus_size = 0
    if audit_records_path and audit_records_path.exists():
        actual_corpus_size = count_corpus_size(audit_records_path)

    # Validate against constraint: N >= 300 OR N >= calculated_minimum
    # This means we need at least 300 samples, or if the calculated minimum is higher,
    # we need at least that many.
    required_minimum = max(minimum_corpus_size, calculated_minimum)
    meets_requirement = actual_corpus_size >= required_minimum

    result = {
        "baseline_rate": baseline_rate,
        "detectable_effect": detectable_effect,
        "alpha": alpha,
        "power": power,
        "calculated_minimum_per_group_binary": int(min_n_binary),
        "calculated_minimum_per_group_continuous": int(min_n_continuous),
        "calculated_minimum_overall": calculated_minimum,
        "minimum_corpus_size_threshold": minimum_corpus_size,
        "required_minimum": required_minimum,
        "actual_corpus_size": actual_corpus_size,
        "meets_requirement": meets_requirement,
        "constraint_satisfied": actual_corpus_size >= 300 or actual_corpus_size >= calculated_minimum,
        "timestamp": str(datetime.now())
    }

    if not meets_requirement:
        logger.warning(
            f"Corpus size {actual_corpus_size} is below required minimum {required_minimum}. "
            f"Constraint: N >= 300 OR N >= {calculated_minimum}"
        )
    else:
        logger.info(
            f"Corpus size {actual_corpus_size} meets requirement (>= {required_minimum})."
        )

    if output_path:
        write_power_analysis_result(result, output_path)

    return result

def write_power_analysis_result(result: Dict[str, Any], output_path: Path):
    """Write power analysis results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    logger.info(f"Power analysis results written to {output_path}")

def main():
    """Main entry point for power analysis script."""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Run power analysis for A/B test audit")
    parser.add_argument(
        "--baseline-rate",
        type=float,
        default=0.10,
        help="Baseline conversion rate (default: 0.10)"
    )
    parser.add_argument(
        "--detectable-effect",
        type=float,
        default=0.05,
        help="Detectable effect size (default: 0.05)"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)"
    )
    parser.add_argument(
        "--power",
        type=float,
        default=0.80,
        help="Desired power (default: 0.80)"
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
        default=Path("output/power_analysis.json"),
        help="Output path for results"
    )
    parser.add_argument(
        "--min-corpus-size",
        type=int,
        default=300,
        help="Minimum required corpus size (default: 300)"
    )

    args = parser.parse_args()

    result = run_power_analysis(
        baseline_rate=args.baseline_rate,
        detectable_effect=args.detectable_effect,
        alpha=args.alpha,
        power=args.power,
        audit_records_path=args.audit_report,
        output_path=args.output,
        minimum_corpus_size=args.min_corpus_size
    )

    if not result["meets_requirement"]:
        logger.error(
            f"Power analysis failed: Corpus size {result['actual_corpus_size']} "
            f"does not meet requirement of {result['required_minimum']}. "
            f"Constraint: N >= 300 OR N >= {result['calculated_minimum_overall']}"
        )
        sys.exit(1)

    logger.info("Power analysis completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
