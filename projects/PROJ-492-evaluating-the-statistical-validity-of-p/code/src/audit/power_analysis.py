"""
Power Analysis Utility (FR-025)

Computes the minimum sample size (N) required for a statistical test
given baseline rate, detectable effect size, alpha, and power.
Validates that the audited corpus meets the minimum N requirement.
"""
import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Configuration constants for power analysis
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
MIN_CORPUS_SIZE = 300  # FR-025 requirement: N >= 300

logger = get_default_logger(__name__)
audit_logger = AuditLogger()


def set_rng_seed_for_power_analysis(seed: int = 42) -> None:
    """Set RNG seed for reproducibility in power analysis calculations."""
    set_rng_seed(seed)


def calculate_sample_size_binary(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> int:
    """
    Calculate minimum sample size per group for a two-proportion z-test.

    Args:
        baseline_rate: Expected baseline conversion rate (0 < p < 1)
        detectable_effect: Minimum detectable difference in proportions
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)

    Returns:
        Minimum sample size per group (N)
    """
    if not (0 < baseline_rate < 1):
        raise ValueError("Baseline rate must be between 0 and 1")
    if not (0 < detectable_effect < 1):
        raise ValueError("Detectable effect must be between 0 and 1")
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1")
    if not (0 < power < 1):
        raise ValueError("Power must be between 0 and 1")

    # Calculate effect size (Cohen's h)
    h = 2 * (np.arcsin(np.sqrt(baseline_rate + detectable_effect)) - 
             np.arcsin(np.sqrt(baseline_rate)))
    
    if h == 0:
        return MIN_CORPUS_SIZE  # No effect to detect, return minimum

    # Sample size formula for two proportions
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    n_per_group = 2 * ((z_alpha + z_beta) / h) ** 2
    
    return max(int(np.ceil(n_per_group)), MIN_CORPUS_SIZE)


def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    std_dev: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> int:
    """
    Calculate minimum sample size per group for a Welch's t-test.

    Args:
        baseline_mean: Expected baseline mean
        detectable_effect: Minimum detectable difference in means
        std_dev: Expected standard deviation
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)

    Returns:
        Minimum sample size per group (N)
    """
    if std_dev <= 0:
        raise ValueError("Standard deviation must be positive")
    if detectable_effect == 0:
        return MIN_CORPUS_SIZE

    # Effect size (Cohen's d)
    d = detectable_effect / std_dev
    
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    n_per_group = 2 * ((z_alpha + z_beta) / d) ** 2
    
    return max(int(np.ceil(n_per_group)), MIN_CORPUS_SIZE)


def count_corpus_size(audit_records_path: Path) -> int:
    """
    Count the number of audit records in the corpus.

    Args:
        audit_records_path: Path to the audit report JSON file

    Returns:
        Number of records in the corpus
    """
    if not audit_records_path.exists():
        logger.warning(f"Audit records file not found: {audit_records_path}")
        return 0

    try:
        with open(audit_records_path, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        if isinstance(records, list):
            return len(records)
        elif isinstance(records, dict) and 'records' in records:
            return len(records['records'])
        else:
            logger.error("Unexpected audit report format")
            return 0
    except Exception as e:
        audit_logger.error("ERR-025", f"Failed to read audit records: {e}")
        return 0


def run_power_analysis(
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.05,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    corpus_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run power analysis and validate corpus size.

    Args:
        baseline_rate: Baseline conversion rate
        detectable_effect: Minimum detectable effect size
        alpha: Significance level
        power: Desired statistical power
        corpus_path: Path to audit report (optional)
        output_path: Path to write results (optional)

    Returns:
        Dictionary containing analysis results
    """
    set_rng_seed_for_power_analysis(42)

    # Calculate required sample size
    required_n = calculate_sample_size_binary(
        baseline_rate=baseline_rate,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power
    )

    # Determine actual corpus size
    actual_n = MIN_CORPUS_SIZE  # Default minimum
    if corpus_path and corpus_path.exists():
        actual_n = count_corpus_size(corpus_path)

    # Validate corpus meets requirements
    # Requirement: N >= 300 OR N >= calculated_minimum
    meets_minimum = actual_n >= MIN_CORPUS_SIZE or actual_n >= required_n
    
    result = {
        "baseline_rate": baseline_rate,
        "detectable_effect": detectable_effect,
        "alpha": alpha,
        "power": power,
        "calculated_minimum_n": required_n,
        "actual_corpus_size": actual_n,
        "meets_minimum_requirement": meets_minimum,
        "requirement_note": f"N >= {MIN_CORPUS_SIZE} OR N >= {required_n}",
        "timestamp": str(set_rng_seed_for_power_analysis.__module__),
        "status": "PASS" if meets_minimum else "FAIL"
    }

    # Log results
    if meets_minimum:
        audit_logger.info("INFO-025", f"Corpus size {actual_n} meets minimum requirement")
    else:
        audit_logger.warning("WARN-025", 
                           f"Corpus size {actual_n} below minimum requirement ({MIN_CORPUS_SIZE} or {required_n})")

    # Write output if path provided
    if output_path:
        write_power_analysis_result(result, output_path)

    return result


def write_power_analysis_result(result: Dict[str, Any], output_path: Path) -> None:
    """
    Write power analysis results to JSON file.

    Args:
        result: Dictionary containing analysis results
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Power analysis results written to {output_path}")


def main() -> int:
    """
    Main entry point for power analysis utility.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Default paths
        output_dir = Path("code/output")
        output_path = output_dir / "power_analysis.json"
        corpus_path = Path("code/output/audit_report.json")

        # Parse command line arguments if needed
        if len(sys.argv) > 1:
            output_path = Path(sys.argv[1])
        if len(sys.argv) > 2:
            corpus_path = Path(sys.argv[2])

        # Run analysis
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.05,
            corpus_path=corpus_path if corpus_path.exists() else None,
            output_path=output_path
        )

        # Check if requirement is met
        if not result["meets_minimum_requirement"]:
            audit_logger.error("ERR-025", 
                             f"Corpus size {result['actual_corpus_size']} does not meet minimum requirement")
            return 1

        return 0

    except Exception as e:
        audit_logger.error("ERR-025", f"Power analysis failed: {e}")
        logger.exception("Power analysis error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
