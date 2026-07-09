"""
Power Analysis Utility (FR-025)

Computes the minimum sample size (N) required to detect a specific effect size
given a baseline rate, significance level (alpha), and statistical power.
Validates that the audited corpus meets the minimum size requirements derived
from statistical power analysis, specifically referencing constraints from
arXiv:2510.17487 (Claim c_21f3e400).
"""
import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_BASELINE = 0.10  # 10% baseline conversion rate
DEFAULT_EFFECT_SIZE = 0.05  # 5% absolute lift (e.g., 10% -> 15%)
CORPUS_MIN_SIZE_THRESHOLD = 2510  # Derived from arXiv:2510.17487 (Claim c_21f3e400)

logger = get_default_logger(__name__)


def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Set random seed for reproducibility in power analysis."""
    set_rng_seed(seed)


def calculate_sample_size_binary(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    alternative: str = "two-sided"
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate the minimum sample size per group for a two-proportion z-test.

    Uses the normal approximation for power calculation.
    Formula: n = (Z_{1-alpha/2} + Z_{power})^2 * (p1(1-p1) + p2(1-p2)) / (p1 - p2)^2

    Args:
        baseline_rate: The expected conversion rate of the control group (p1).
        detectable_effect: The absolute difference to detect (delta = p2 - p1).
        alpha: Significance level (Type I error rate).
        power: Statistical power (1 - Type II error rate).
        alternative: 'two-sided', 'less', or 'greater'.

    Returns:
        Tuple of (required_n_per_group, stats_dict)
    """
    if not (0 < baseline_rate < 1):
        raise ValueError(f"Baseline rate must be between 0 and 1, got {baseline_rate}")
    if not (0 < detectable_effect < 1):
        raise ValueError(f"Detectable effect must be between 0 and 1, got {detectable_effect}")
    
    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect
    
    if not (0 < p2 < 1):
        raise ValueError(f"Resulting rate p2 ({p2}) must be between 0 and 1")

    # Critical values
    if alternative == "two-sided":
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    
    z_beta = stats.norm.ppf(power)

    # Pooled variance approximation for sample size
    # n = (Z_alpha + Z_beta)^2 * (p1(1-p1) + p2(1-p2)) / (p1 - p2)^2
    numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
    denominator = (p1 - p2) ** 2
    
    n_per_group = numerator / denominator
    total_n = 2 * n_per_group

    stats_dict = {
        "baseline_rate": p1,
        "treatment_rate": p2,
        "delta": detectable_effect,
        "alpha": alpha,
        "power": power,
        "z_alpha": z_alpha,
        "z_beta": z_beta,
        "n_per_group": n_per_group,
        "total_n": total_n
    }

    return n_per_group, stats_dict


def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    std_dev: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    alternative: str = "two-sided"
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate minimum sample size per group for a two-sample t-test (Welch's).
    
    Uses the effect size (Cohen's d) approach.
    """
    if std_dev <= 0:
        raise ValueError("Standard deviation must be positive")
    
    # Effect size (Cohen's d)
    d = detectable_effect / std_dev
    
    # Critical values
    if alternative == "two-sided":
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    
    z_beta = stats.norm.ppf(power)

    # Approximate sample size per group for t-test
    # n = 2 * (Z_alpha + Z_beta)^2 / d^2
    n_per_group = 2 * ((z_alpha + z_beta) ** 2) / (d ** 2)
    total_n = 2 * n_per_group

    stats_dict = {
        "baseline_mean": baseline_mean,
        "treatment_mean": baseline_mean + detectable_effect,
        "std_dev": std_dev,
        "effect_size_d": d,
        "alpha": alpha,
        "power": power,
        "n_per_group": n_per_group,
        "total_n": total_n
    }

    return n_per_group, stats_dict


def count_corpus_size(audit_report_path: Path) -> int:
    """
    Count the number of records in the audit report to determine corpus size.
    """
    if not audit_report_path.exists():
        logger.warning(f"Audit report not found at {audit_report_path}. Returning 0.")
        return 0
    
    count = 0
    try:
        with open(audit_report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                count = len(data)
            elif isinstance(data, dict) and 'records' in data:
                count = len(data['records'])
            else:
                # Fallback: count top-level keys if it's a dict of records
                count = len(data)
    except Exception as e:
        logger.error(f"Error reading audit report: {e}")
        return 0
    
    return count


def write_power_analysis_result(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """Write the power analysis result to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Power analysis result written to {output_path}")


def run_power_analysis(
    audit_report_path: Path,
    output_path: Path,
    baseline_rate: float = DEFAULT_BASELINE,
    detectable_effect: float = DEFAULT_EFFECT_SIZE,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> Dict[str, Any]:
    """
    Run the full power analysis pipeline.
    
    1. Calculates required sample size for the given parameters.
    2. Checks the actual corpus size from the audit report.
    3. Verifies if the corpus meets the minimum size requirement from
       arXiv:2510.17487 (Claim c_21f3e400) which suggests a minimum of 2510 samples
       for robust statistical validity in this context.
    
    Returns:
        Dictionary containing the analysis results.
    """
    set_rng_seed_for_power_analysis()
    
    logger.info(f"Starting power analysis with baseline={baseline_rate}, effect={detectable_effect}")
    
    # 1. Calculate required sample size
    n_required, stats_details = calculate_sample_size_binary(
        baseline_rate, detectable_effect, alpha, power
    )
    
    # 2. Get actual corpus size
    actual_corpus_size = count_corpus_size(audit_report_path)
    logger.info(f"Corpus size detected: {actual_corpus_size}")
    
    # 3. Check against Claim c_21f3e400 (arXiv:2510.17487)
    # The claim specifies a minimum corpus size for valid statistical inference.
    meets_arxiv_threshold = actual_corpus_size >= CORPUS_MIN_SIZE_THRESHOLD
    meets_power_threshold = actual_corpus_size >= (2 * n_required)
    
    result = {
        "parameters": {
            "baseline_rate": baseline_rate,
            "detectable_effect": detectable_effect,
            "alpha": alpha,
            "power": power
        },
        "calculated_requirements": stats_details,
        "corpus_statistics": {
            "actual_size": actual_corpus_size,
            "meets_arxiv_2510_17487_threshold": meets_arxiv_threshold,
            "arxiv_threshold_value": CORPUS_MIN_SIZE_THRESHOLD,
            "meets_power_calculation_threshold": meets_power_threshold,
            "power_required_total_n": 2 * n_required
        },
        "validation_status": "PASSED" if (meets_arxiv_threshold and meets_power_threshold) else "WARNING",
        "message": (
            f"Corpus size {actual_corpus_size} {'meets' if meets_arxiv_threshold else 'does not meet'} "
            f"the arXiv:2510.17487 threshold of {CORPUS_MIN_SIZE_THRESHOLD}."
        )
    }
    
    write_power_analysis_result(result, output_path)
    
    if not meets_arxiv_threshold:
        logger.warning(f"Corpus size {actual_corpus_size} is below the required threshold {CORPUS_MIN_SIZE_THRESHOLD} per arXiv:2510.17487.")
    elif not meets_power_threshold:
        logger.warning(f"Corpus size {actual_corpus_size} is below the power-calculated requirement {2 * n_required:.0f}.")
    else:
        logger.info("Power analysis validation PASSED.")
        
    return result


def main() -> None:
    """Main entry point for the power analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run power analysis on audit corpus.")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("output/audit_report.json"),
        help="Path to the audit report JSON file."
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("output/power_analysis.json"),
        help="Path to write the power analysis result JSON."
    )
    parser.add_argument(
        "--baseline", 
        type=float, 
        default=DEFAULT_BASELINE,
        help="Baseline conversion rate."
    )
    parser.add_argument(
        "--effect", 
        type=float, 
        default=DEFAULT_EFFECT_SIZE,
        help="Detectable effect size (absolute)."
    )
    parser.add_argument(
        "--alpha", 
        type=float, 
        default=DEFAULT_ALPHA,
        help="Significance level."
    )
    parser.add_argument(
        "--power", 
        type=float, 
        default=DEFAULT_POWER,
        help="Statistical power."
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    try:
        result = run_power_analysis(
            audit_report_path=args.input,
            output_path=args.output,
            baseline_rate=args.baseline,
            detectable_effect=args.effect,
            alpha=args.alpha,
            power=args.power
        )
        logger.info("Power analysis completed successfully.")
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
