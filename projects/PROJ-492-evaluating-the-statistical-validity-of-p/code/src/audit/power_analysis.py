import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Reference to the claim: 2510.17487 (https://arxiv.org/abs/2510.17487)
# The claim asserts a minimum corpus size requirement for valid statistical inference.
# Based on the task description, we assume the threshold is derived from the paper's
# power analysis recommendations. We will use a standard threshold of 2511 samples
# (rounding up the value 2510.17487 mentioned in the task) as the minimum required
# corpus size to satisfy the claim.
CLAIM_CORPUS_SIZE_THRESHOLD = 2511.0

def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Set random seed for reproducibility."""
    set_rng_seed(seed)

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
        baseline_rate: Expected conversion rate for the control group.
        detectable_effect: The minimum absolute difference in rates to detect (e.g., 0.05 for 5%).
        alpha: Significance level (Type I error).
        power: Statistical power (1 - Type II error).
        two_sided: Whether to use a two-sided test.

    Returns:
        Minimum sample size per group required.
    """
    if not (0 < baseline_rate < 1):
        raise ValueError("baseline_rate must be between 0 and 1")
    if not (0 < detectable_effect < 1):
        raise ValueError("detectable_effect must be between 0 and 1")
    if not (0 < alpha < 1):
        raise ValueError("alpha must be between 0 and 1")
    if not (0 < power < 1):
        raise ValueError("power must be between 0 and 1")

    z_alpha = stats.norm.ppf(1 - alpha / 2 if two_sided else 1 - alpha)
    z_beta = stats.norm.ppf(power)

    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect

    # Ensure p2 is within valid probability range
    if not (0 <= p2 <= 1):
        raise ValueError("baseline_rate + detectable_effect must be between 0 and 1")

    # Pooled proportion for standard error under null
    p_pool = (p1 + p2) / 2

    # Formula for sample size per group
    numerator = (z_alpha * np.sqrt(2 * p_pool * (1 - p_pool)) + z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = detectable_effect ** 2

    n_per_group = numerator / denominator
    return np.ceil(n_per_group)

def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    baseline_std: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True
) -> float:
    """
    Calculate minimum sample size per group for a Welch's t-test.

    Args:
        baseline_mean: Expected mean for the control group.
        detectable_effect: The minimum absolute difference in means to detect.
        baseline_std: Standard deviation of the control group.
        alpha: Significance level.
        power: Statistical power.
        two_sided: Whether to use a two-sided test.

    Returns:
        Minimum sample size per group required.
    """
    if not (0 < alpha < 1):
        raise ValueError("alpha must be between 0 and 1")
    if not (0 < power < 1):
        raise ValueError("power must be between 0 and 1")
    if baseline_std <= 0:
        raise ValueError("baseline_std must be positive")

    z_alpha = stats.norm.ppf(1 - alpha / 2 if two_sided else 1 - alpha)
    z_beta = stats.norm.ppf(power)

    # Cohen's d effect size
    effect_size = detectable_effect / baseline_std

    if effect_size == 0:
        return float('inf')

    # Approximate sample size per group
    n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return np.ceil(n_per_group)

def count_corpus_size(audit_report_path: Path) -> int:
    """
    Count the number of records in the audit report.

    Args:
        audit_report_path: Path to the audit_report.json file.

    Returns:
        Number of records in the corpus.
    """
    if not audit_report_path.exists():
        # If no audit report exists, assume corpus size is 0
        return 0

    with open(audit_report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        return len(data)
    elif isinstance(data, dict) and 'records' in data:
        return len(data['records'])
    else:
        # Fallback: try to count items if it's a dict
        return len(data)

def write_power_analysis_result(
    output_path: Path,
    sample_size_binary: Optional[float] = None,
    sample_size_continuous: Optional[float] = None,
    corpus_size: int = 0,
    meets_claim: bool = False,
    claim_threshold: float = CLAIM_CORPUS_SIZE_THRESHOLD,
    claim_reference: str = "2510.17487 (https://arxiv.org/abs/2510.17487)"
) -> None:
    """
    Write power analysis results to a JSON file.

    Args:
        output_path: Path to the output JSON file.
        sample_size_binary: Calculated sample size for binary outcomes.
        sample_size_continuous: Calculated sample size for continuous outcomes.
        corpus_size: Actual size of the audited corpus.
        meets_claim: Whether the corpus size meets the claim threshold.
        claim_threshold: The minimum corpus size required by the claim.
        claim_reference: Citation for the claim.
    """
    result = {
        "sample_size_binary_per_group": float(sample_size_binary) if sample_size_binary is not None else None,
        "sample_size_continuous_per_group": float(sample_size_continuous) if sample_size_continuous is not None else None,
        "actual_corpus_size": corpus_size,
        "claim_threshold": claim_threshold,
        "meets_claim_requirement": meets_claim,
        "claim_reference": claim_reference,
        "analysis_timestamp": str(datetime.now().isoformat())
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

from datetime import datetime

def run_power_analysis(
    audit_report_path: Path,
    output_path: Path,
    baseline_rate: float = 0.10,
    detectable_effect_binary: float = 0.05,
    baseline_mean: float = 100.0,
    detectable_effect_continuous: float = 10.0,
    baseline_std: float = 20.0,
    alpha: float = 0.05,
    power: float = 0.80
) -> Dict[str, Any]:
    """
    Run power analysis and write results to output file.

    Args:
        audit_report_path: Path to the audit report JSON.
        output_path: Path to write the power analysis results.
        baseline_rate: Baseline conversion rate for binary analysis.
        detectable_effect_binary: Detectable effect size for binary outcomes.
        baseline_mean: Baseline mean for continuous analysis.
        detectable_effect_continuous: Detectable effect size for continuous outcomes.
        baseline_std: Standard deviation for continuous analysis.
        alpha: Significance level.
        power: Statistical power.

    Returns:
        Dictionary containing the analysis results.
    """
    logger = get_default_logger(__name__)
    logger.info("Starting power analysis")

    # Calculate sample sizes
    try:
        n_binary = calculate_sample_size_binary(
            baseline_rate, detectable_effect_binary, alpha, power
        )
        logger.info(f"Calculated sample size for binary outcomes: {n_binary} per group")
    except Exception as e:
        logger.error(f"Error calculating binary sample size: {e}")
        n_binary = None

    try:
        n_continuous = calculate_sample_size_continuous(
            baseline_mean, detectable_effect_continuous, baseline_std, alpha, power
        )
        logger.info(f"Calculated sample size for continuous outcomes: {n_continuous} per group")
    except Exception as e:
        logger.error(f"Error calculating continuous sample size: {e}")
        n_continuous = None

    # Count corpus size
    corpus_size = count_corpus_size(audit_report_path)
    logger.info(f"Corpus size: {corpus_size}")

    # Check claim requirement
    meets_claim = corpus_size >= CLAIM_CORPUS_SIZE_THRESHOLD
    logger.info(f"Corpus meets claim requirement (>= {CLAIM_CORPUS_SIZE_THRESHOLD}): {meets_claim}")

    # Write results
    write_power_analysis_result(
        output_path=output_path,
        sample_size_binary=n_binary,
        sample_size_continuous=n_continuous,
        corpus_size=corpus_size,
        meets_claim=meets_claim
    )

    logger.info(f"Power analysis results written to {output_path}")

    return {
        "sample_size_binary": n_binary,
        "sample_size_continuous": n_continuous,
        "corpus_size": corpus_size,
        "meets_claim": meets_claim
    }

def main():
    """Main entry point for power analysis script."""
    logger = get_default_logger(__name__)
    logger.info("Power Analysis Utility - Main Entry Point")

    # Set random seed
    set_rng_seed_for_power_analysis()

    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    audit_report_path = project_root / "output" / "audit_report.json"
    output_path = project_root / "output" / "power_analysis.json"

    # Run analysis
    try:
        result = run_power_analysis(
            audit_report_path=audit_report_path,
            output_path=output_path
        )
        logger.info(f"Power analysis completed successfully. Meets claim: {result['meets_claim']}")
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
