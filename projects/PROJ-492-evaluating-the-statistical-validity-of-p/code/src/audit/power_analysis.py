"""
Power analysis utility for determining minimum sample size requirements.

Implements FR-025: Computes minimum N given baseline, detectable effect, alpha, and power.
Also validates that the audited corpus meets the minimum sample size requirement
derived from the statistical power analysis (Constraint: c_21f3e400).
"""
import json
import logging
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from scipy import stats
from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Set random seed for reproducibility in power analysis calculations."""
    set_rng_seed(seed)

def calculate_sample_size_binary(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True
) -> float:
    """
    Calculate minimum sample size per group for a binary outcome (A/B test).
    
    Uses the standard formula for two-proportion z-test power analysis:
    n = (Z_alpha/2 + Z_beta)^2 * (p1*(1-p1) + p2*(1-p2)) / (p1 - p2)^2
    
    Args:
        baseline_rate: The baseline conversion rate (p1)
        detectable_effect: The minimum detectable effect size (difference in proportions)
        alpha: Significance level (default 0.05)
        power: Statistical power (default 0.80)
        two_sided: Whether to use two-sided test (default True)
        
    Returns:
        Minimum sample size per group (float)
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not 0 < baseline_rate < 1:
        raise ValueError(f"Baseline rate must be between 0 and 1, got {baseline_rate}")
    if not 0 < detectable_effect < 1:
        raise ValueError(f"Detectable effect must be between 0 and 1, got {detectable_effect}")
    if not 0 < alpha < 1:
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
    if not 0 < power < 1:
        raise ValueError(f"Power must be between 0 and 1, got {power}")
    
    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect
    
    if not 0 < p2 < 1:
        raise ValueError(f"Resulting rate p2 ({p2}) must be between 0 and 1")
    
    # Critical values
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    
    z_beta = stats.norm.ppf(power)
    
    # Variance components
    variance = p1 * (1 - p1) + p2 * (1 - p2)
    
    # Sample size formula
    n_per_group = ((z_alpha + z_beta) ** 2 * variance) / (detectable_effect ** 2)
    
    return float(n_per_group)

def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    std_dev: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True
) -> float:
    """
    Calculate minimum sample size per group for a continuous outcome.
    
    Uses the standard formula for Welch's t-test power analysis:
    n = 2 * (Z_alpha/2 + Z_beta)^2 * (sigma^2) / delta^2
    
    Args:
        baseline_mean: The baseline mean (not directly used in formula, but for context)
        detectable_effect: The minimum detectable difference (delta)
        std_dev: The standard deviation of the outcome
        alpha: Significance level (default 0.05)
        power: Statistical power (default 0.80)
        two_sided: Whether to use two-sided test (default True)
        
    Returns:
        Minimum sample size per group (float)
    """
    if detectable_effect == 0:
        raise ValueError("Detectable effect cannot be zero")
    if std_dev <= 0:
        raise ValueError(f"Standard deviation must be positive, got {std_dev}")
    if not 0 < alpha < 1:
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
    if not 0 < power < 1:
        raise ValueError(f"Power must be between 0 and 1, got {power}")
    
    # Critical values
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula for two-sample t-test (equal variance assumption for simplicity)
    n_per_group = 2 * ((z_alpha + z_beta) ** 2 * (std_dev ** 2)) / (detectable_effect ** 2)
    
    return float(n_per_group)

def count_corpus_size(audit_records_path: Path) -> int:
    """
    Count the number of audit records in the corpus.
    
    Args:
        audit_records_path: Path to the audit_report.json file
        
    Returns:
        Number of records in the corpus
    """
    if not audit_records_path.exists():
        logging.warning(f"Audit records file not found: {audit_records_path}")
        return 0
    
    try:
        with open(audit_records_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict) and 'records' in data:
            return len(data['records'])
        else:
            logging.warning(f"Unexpected audit records format in {audit_records_path}")
            return 0
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to read audit records: {e}")
        return 0

def write_power_analysis_result(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write power analysis results to a JSON file.
    
    Args:
        result: Dictionary containing power analysis results
        output_path: Path to write the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    
    logging.info(f"Power analysis results written to {output_path}")

def run_power_analysis(
    audit_records_path: Path,
    output_path: Path,
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.05,
    alpha: float = 0.05,
    power: float = 0.80,
    std_dev: Optional[float] = None,
    test_type: str = "binary"
) -> Dict[str, Any]:
    """
    Run complete power analysis and validate corpus size.
    
    This function:
    1. Calculates minimum sample size based on parameters
    2. Counts actual corpus size from audit records
    3. Validates that corpus meets minimum requirements
    4. Writes results to output JSON
    
    Args:
        audit_records_path: Path to audit_report.json
        output_path: Path for output JSON file
        baseline_rate: Baseline conversion rate for binary tests
        detectable_effect: Minimum detectable effect size
        alpha: Significance level
        power: Statistical power
        std_dev: Standard deviation for continuous tests (required if test_type="continuous")
        test_type: Type of test ("binary" or "continuous")
        
    Returns:
        Dictionary with power analysis results and validation status
    """
    set_rng_seed_for_power_analysis()
    
    logger = get_default_logger()
    
    # Calculate minimum sample size
    if test_type == "binary":
        min_n_per_group = calculate_sample_size_binary(
            baseline_rate=baseline_rate,
            detectable_effect=detectable_effect,
            alpha=alpha,
            power=power
        )
        min_total_n = 2 * min_n_per_group
    elif test_type == "continuous":
        if std_dev is None:
            raise ValueError("std_dev is required for continuous test type")
        min_n_per_group = calculate_sample_size_continuous(
            baseline_mean=0,  # Not used in formula
            detectable_effect=detectable_effect,
            std_dev=std_dev,
            alpha=alpha,
            power=power
        )
        min_total_n = 2 * min_n_per_group
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    # Count actual corpus size
    actual_corpus_size = count_corpus_size(audit_records_path)
    
    # Validate corpus meets requirements
    # Claim c_21f3e400: Corpus must meet minimum sample size requirement
    # The requirement is that the corpus size >= minimum required N
    meets_requirement = actual_corpus_size >= min_total_n
    
    result = {
        "test_type": test_type,
        "parameters": {
            "baseline_rate": baseline_rate if test_type == "binary" else None,
            "detectable_effect": detectable_effect,
            "alpha": alpha,
            "power": power,
            "std_dev": std_dev if test_type == "continuous" else None
        },
        "minimum_sample_size": {
            "per_group": round(min_n_per_group, 2),
            "total": round(min_total_n, 2)
        },
        "actual_corpus_size": actual_corpus_size,
        "corpus_meets_requirement": meets_requirement,
        "validation_status": "PASS" if meets_requirement else "FAIL",
        "claim_reference": "c_21f3e400",
        "arxiv_reference": "2510.17487",
        "timestamp": str(datetime.now())
    }
    
    # Write results
    write_power_analysis_result(result, output_path)
    
    if not meets_requirement:
        logger.error(
            f"Corpus size ({actual_corpus_size}) is below minimum requirement ({min_total_n:.2f}). "
            f"Power analysis validation failed. See claim c_21f3e400."
        )
    else:
        logger.info(
            f"Corpus size ({actual_corpus_size}) meets minimum requirement ({min_total_n:.2f}). "
            f"Power analysis validation passed."
        )
    
    return result

def main() -> int:
    """
    Main entry point for power analysis utility.
    
    Reads configuration from command line or defaults, runs power analysis,
    and writes results to output/power_analysis.json.
    
    Returns:
        0 on success, 1 on failure
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Power Analysis Utility")
    parser.add_argument(
        "--audit-records",
        type=str,
        default="output/audit_report.json",
        help="Path to audit_report.json"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/power_analysis.json",
        help="Path for output JSON file"
    )
    parser.add_argument(
        "--baseline-rate",
        type=float,
        default=0.10,
        help="Baseline conversion rate (for binary tests)"
    )
    parser.add_argument(
        "--detectable-effect",
        type=float,
        default=0.05,
        help="Minimum detectable effect size"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level"
    )
    parser.add_argument(
        "--power",
        type=float,
        default=0.80,
        help="Statistical power"
    )
    parser.add_argument(
        "--std-dev",
        type=float,
        default=None,
        help="Standard deviation (for continuous tests)"
    )
    parser.add_argument(
        "--test-type",
        type=str,
        choices=["binary", "continuous"],
        default="binary",
        help="Type of statistical test"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_power_analysis(
            audit_records_path=Path(args.audit_records),
            output_path=Path(args.output),
            baseline_rate=args.baseline_rate,
            detectable_effect=args.detectable_effect,
            alpha=args.alpha,
            power=args.power,
            std_dev=args.std_dev,
            test_type=args.test_type
        )
        
        # Exit with error if validation failed
        if not result["corpus_meets_requirement"]:
            logging.error("Power analysis validation failed: corpus does not meet minimum size requirement")
            return 1
        
        return 0
        
    except Exception as e:
        logging.error(f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
