"""
Power analysis utility for A/B test validity auditing.

Implements FR-025: Computes minimum sample size (N) required to detect
a given effect size with specified alpha and power.

Also validates that the audited corpus meets the statistical power
requirement defined in claim c_21f3e400 (arXiv:2510.17487).
"""

import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Set seed for reproducibility as per Constitution Principle I
set_rng_seed(SEED)

def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Ensure deterministic behavior for power analysis calculations."""
    np.random.seed(seed)

def calculate_sample_size_binary(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate minimum sample size per group for a two-proportion z-test.

    Args:
        baseline_rate: Expected conversion rate of control group (0-1).
        detectable_effect: Absolute difference to detect (e.g., 0.05 for 5%).
        alpha: Significance level (Type I error rate).
        power: Desired statistical power (1 - Type II error rate).
        two_sided: Whether to use a two-sided test.

    Returns:
        Tuple of (minimum N per group, metadata dict)
    """
    if not (0 < baseline_rate < 1):
        raise ValueError("Baseline rate must be between 0 and 1")
    if not (0 < detectable_effect < 1):
        raise ValueError("Detectable effect must be between 0 and 1")
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1")
    if not (0 < power < 1):
        raise ValueError("Power must be between 0 and 1")

    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect

    if not (0 < p2 < 1):
        raise ValueError("Treatment rate (baseline + effect) must be between 0 and 1")

    # Pooled proportion under null
    p_pooled = (p1 + p2) / 2

    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha / 2) if two_sided else stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)

    # Standard deviations
    sd_null = np.sqrt(2 * p_pooled * (1 - p_pooled))
    sd_alt = np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))

    # Sample size formula for two proportions
    # n = (z_alpha * sd_null + z_beta * sd_alt)^2 / (p2 - p1)^2
    numerator = (z_alpha * sd_null + z_beta * sd_alt) ** 2
    denominator = (p2 - p1) ** 2
    n_per_group = numerator / denominator

    metadata = {
        "baseline_rate": p1,
        "treatment_rate": p2,
        "detectable_effect": detectable_effect,
        "alpha": alpha,
        "power": power,
        "two_sided": two_sided,
        "z_alpha": z_alpha,
        "z_beta": z_beta,
        "pooled_proportion": p_pooled
    }

    return float(np.ceil(n_per_group)), metadata

def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    std_dev: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate minimum sample size per group for a Welch's t-test.

    Args:
        baseline_mean: Expected mean of control group.
        detectable_effect: Absolute difference to detect.
        std_dev: Expected standard deviation (assumed equal for both groups).
        alpha: Significance level.
        power: Desired statistical power.
        two_sided: Whether to use a two-sided test.

    Returns:
        Tuple of (minimum N per group, metadata dict)
    """
    if std_dev <= 0:
        raise ValueError("Standard deviation must be positive")
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1")
    if not (0 < power < 1):
        raise ValueError("Power must be between 0 and 1")

    # Effect size (Cohen's d)
    effect_size = abs(detectable_effect) / std_dev

    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha / 2) if two_sided else stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)

    # Sample size formula for t-test (approximation using normal)
    # n = 2 * (z_alpha + z_beta)^2 / effect_size^2
    n_per_group = 2 * ((z_alpha + z_beta) ** 2) / (effect_size ** 2)

    metadata = {
        "baseline_mean": baseline_mean,
        "detectable_effect": detectable_effect,
        "std_dev": std_dev,
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "two_sided": two_sided,
        "z_alpha": z_alpha,
        "z_beta": z_beta
    }

    return float(np.ceil(n_per_group)), metadata

def count_corpus_size(audit_report_path: Path) -> int:
    """
    Count the number of valid records in the audit report.

    Args:
        audit_report_path: Path to the audit_report.json file.

    Returns:
        Number of records in the corpus.
    """
    if not audit_report_path.exists():
        raise FileNotFoundError(f"Audit report not found: {audit_report_path}")

    with open(audit_report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both list and dict with 'records' key
    if isinstance(data, list):
        return len(data)
    elif isinstance(data, dict) and 'records' in data:
        return len(data['records'])
    else:
        raise ValueError("Unexpected audit report format")

def write_power_analysis_result(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write power analysis results to a JSON file.

    Args:
        result: Dictionary containing power analysis results.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)

    logging.info(f"Power analysis result written to {output_path}")

def run_power_analysis(
    audit_report_path: Path,
    output_path: Path,
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.05,
    alpha: float = 0.05,
    power: float = 0.80,
    claim_threshold: float = 2510.17487
) -> Dict[str, Any]:
    """
    Run power analysis on the audited corpus.

    This function:
    1. Counts the corpus size from the audit report.
    2. Calculates the minimum required sample size per group.
    3. Checks if the corpus meets the claim threshold (c_21f3e400).
    4. Writes results to the output JSON file.

    Args:
        audit_report_path: Path to the audit_report.json file.
        output_path: Path to write the power_analysis.json file.
        baseline_rate: Expected baseline conversion rate.
        detectable_effect: Minimum detectable effect size.
        alpha: Significance level.
        power: Desired statistical power.
        claim_threshold: Threshold from claim c_21f3e400 (arXiv:2510.17487).

    Returns:
        Dictionary containing the power analysis results.
    """
    logger = get_default_logger(__name__)

    # Calculate required sample size
    n_required, calculation_metadata = calculate_sample_size_binary(
        baseline_rate=baseline_rate,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power
    )

    # Count actual corpus size
    try:
        corpus_size = count_corpus_size(audit_report_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to count corpus: {e}")
        raise

    # Check against claim threshold
    meets_threshold = corpus_size >= claim_threshold
    meets_requirement = corpus_size >= n_required

    result = {
        "calculation_parameters": {
            "baseline_rate": baseline_rate,
            "detectable_effect": detectable_effect,
            "alpha": alpha,
            "power": power
        },
        "calculated_metadata": calculation_metadata,
        "minimum_required_n_per_group": n_required,
        "actual_corpus_size": corpus_size,
        "claim_reference": {
            "id": "c_21f3e400",
            "arxiv": "2510.17487",
            "url": "https://arxiv.org/abs/2510.17487",
            "threshold": claim_threshold
        },
        "results": {
            "meets_claim_threshold": meets_threshold,
            "meets_power_requirement": meets_requirement,
            "corpus_size": corpus_size,
            "required_size": n_required
        },
        "timestamp": str(datetime.now()),
        "status": "PASS" if (meets_threshold and meets_requirement) else "FAIL"
    }

    # Write results
    write_power_analysis_result(result, output_path)

    return result

def main() -> int:
    """
    Main entry point for power analysis script.

    Reads audit report, performs power analysis, and writes results.

    Returns:
        0 on success, non-zero on failure.
    """
    logger = get_default_logger(__name__)

    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    audit_report_path = project_root / "output" / "audit_report.json"
    output_path = project_root / "output" / "power_analysis.json"

    try:
        # Run power analysis with default parameters
        # These can be overridden via environment variables or CLI args in future
        result = run_power_analysis(
            audit_report_path=audit_report_path,
            output_path=output_path,
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80,
            claim_threshold=2510.17487
        )

        logger.info(f"Power analysis completed. Status: {result['results']['status']}")
        logger.info(f"Corpus size: {result['actual_corpus_size']}")
        logger.info(f"Required size: {result['minimum_required_n_per_group']}")
        logger.info(f"Meets claim threshold: {result['results']['meets_claim_threshold']}")

        # Exit with error if requirements not met
        if not (result['results']['meets_claim_threshold'] and result['results']['meets_power_requirement']):
            logger.error(get_error_message("ERR-901", "Power analysis requirements not met"))
            return 1

        return 0

    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
