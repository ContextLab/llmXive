"""
Power analysis utility for A/B test audit.
Computes minimum sample size required for given parameters and validates corpus size.
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

# Logger setup
logger = get_default_logger(__name__)
audit_logger = AuditLogger(logger)

def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Set random seed for reproducibility in power analysis."""
    set_rng_seed(seed)

def calculate_sample_size_binary(
    baseline_rate: float,
    detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0
) -> int:
    """
    Calculate minimum sample size per group for a two-proportion z-test.
    
    Args:
        baseline_rate: Expected conversion rate in control group.
        detectable_effect: Minimum detectable difference in rates (absolute).
        alpha: Significance level (Type I error).
        power: Statistical power (1 - Type II error).
        ratio: Ratio of sample size in treatment to control (n2/n1).
    
    Returns:
        Minimum sample size per group (rounded up).
    """
    if not (0 < baseline_rate < 1):
        raise ValueError("Baseline rate must be between 0 and 1")
    if not (0 < detectable_effect < 1):
        raise ValueError("Detectable effect must be between 0 and 1")
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1")
    if not (0 < power < 1):
        raise ValueError("Power must be between 0 and 1")
    if not (ratio > 0):
        raise ValueError("Ratio must be positive")

    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect
    
    if p2 <= 0 or p2 >= 1:
        raise ValueError("Treatment rate (p2) must be between 0 and 1")

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    # Pooled proportion under null
    p_pooled = (p1 + p2) / 2 if ratio == 1.0 else (p1 + ratio * p2) / (1 + ratio)
    
    # Variance components
    var_null = p_pooled * (1 - p_pooled) * (1 + 1/ratio)
    var_alt = p1 * (1 - p1) + (p2 * (1 - p2)) / ratio

    # Sample size formula for two-proportion z-test
    n1 = ((z_alpha * np.sqrt(var_null) + z_beta * np.sqrt(var_alt)) ** 2) / (p2 - p1) ** 2
    
    return int(np.ceil(n1))

def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    std_dev: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0
) -> int:
    """
    Calculate minimum sample size per group for a Welch's t-test.
    
    Args:
        baseline_mean: Expected mean in control group.
        detectable_effect: Minimum detectable difference in means (absolute).
        std_dev: Expected standard deviation (assumed equal for both groups).
        alpha: Significance level.
        power: Statistical power.
        ratio: Ratio of sample size in treatment to control.
    
    Returns:
        Minimum sample size per group (rounded up).
    """
    if detectable_effect == 0:
        raise ValueError("Detectable effect must be non-zero")
    if std_dev <= 0:
        raise ValueError("Standard deviation must be positive")
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1")
    if not (0 < power < 1):
        raise ValueError("Power must be between 0 and 1")

    effect_size = detectable_effect / std_dev
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    # Sample size formula for two-sample t-test (approximation using normal)
    n1 = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    
    return int(np.ceil(n1))

def count_corpus_size(
    audit_records_path: Path,
    exclude_flagged: bool = True
) -> int:
    """
    Count the number of valid audit records in the corpus.
    
    Args:
        audit_records_path: Path to audit_report.json.
        exclude_flagged: If True, exclude records flagged for sample-size mismatch.
    
    Returns:
        Count of valid records.
    """
    if not audit_records_path.exists():
        audit_logger.error("ERR-028", f"Audit records file not found: {audit_records_path}")
        return 0

    try:
        with open(audit_records_path, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        if not isinstance(records, list):
            audit_logger.error("ERR-029", "Audit report is not a list of records")
            return 0
        
        count = 0
        for record in records:
            if exclude_flagged:
                # Exclude records with data_quality_warning for sample-size mismatch
                warnings = record.get('data_quality_warnings', [])
                is_sample_size_issue = any(
                    'sample_size' in str(w).lower() or 'mismatch' in str(w).lower()
                    for w in warnings
                )
                if not is_sample_size_issue:
                    count += 1
            else:
                count += 1
        
        return count
    except json.JSONDecodeError as e:
        audit_logger.error("ERR-030", f"Failed to parse audit report: {e}")
        return 0
    except Exception as e:
        audit_logger.error("ERR-031", f"Unexpected error reading audit records: {e}")
        return 0

def run_power_analysis(
    audit_records_path: Path,
    output_path: Path,
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.05,
    std_dev: float = 1.0,
    alpha: float = 0.05,
    power: float = 0.80,
    min_corpus_size: int = 300
) -> Dict[str, Any]:
    """
    Run power analysis and validate corpus size.
    
    Args:
        audit_records_path: Path to audit_report.json.
        output_path: Path to write power_analysis.json.
        baseline_rate: Assumed baseline conversion rate for binary tests.
        detectable_effect: Minimum detectable effect size.
        std_dev: Assumed standard deviation for continuous tests.
        alpha: Significance level.
        power: Statistical power.
        min_corpus_size: Minimum required corpus size (default 300).
    
    Returns:
        Dictionary with power analysis results and validation status.
    """
    set_rng_seed_for_power_analysis()
    
    # Calculate minimum sample sizes
    n_binary = calculate_sample_size_binary(
        baseline_rate=baseline_rate,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power
    )
    
    n_continuous = calculate_sample_size_continuous(
        baseline_mean=0.0,
        detectable_effect=detectable_effect,
        std_dev=std_dev,
        alpha=alpha,
        power=power
    )
    
    # Count actual corpus size
    corpus_size = count_corpus_size(audit_records_path, exclude_flagged=True)
    
    # Validation: N >= 300 OR N >= calculated_minimum
    calculated_minimum = max(n_binary, n_continuous)
    is_valid = corpus_size >= min_corpus_size or corpus_size >= calculated_minimum
    
    result = {
        "parameters": {
            "baseline_rate": baseline_rate,
            "detectable_effect": detectable_effect,
            "std_dev": std_dev,
            "alpha": alpha,
            "power": power,
            "min_corpus_size_threshold": min_corpus_size
        },
        "calculated_minimum_sample_sizes": {
            "binary_outcome_per_group": n_binary,
            "continuous_outcome_per_group": n_continuous,
            "overall_minimum": calculated_minimum
        },
        "corpus_statistics": {
            "total_valid_records": corpus_size,
            "excluded_flagged_records": True
        },
        "validation": {
            "meets_minimum_threshold": corpus_size >= min_corpus_size,
            "meets_calculated_minimum": corpus_size >= calculated_minimum,
            "is_valid": is_valid,
            "requirement": f"N >= {min_corpus_size} OR N >= {calculated_minimum}"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    if is_valid:
        audit_logger.info("PASS-028", f"Power analysis validation passed. Corpus size {corpus_size} meets requirements.")
    else:
        audit_logger.warning("WARN-028", f"Power analysis validation failed. Corpus size {corpus_size} is below required minimum.")
    
    return result

def write_power_analysis_result(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """Write power analysis result to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    audit_logger.info("INFO-028", f"Power analysis result written to {output_path}")

def main() -> int:
    """Main entry point for power analysis script."""
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description="Run power analysis on audit corpus")
    parser.add_argument(
        "--audit-records",
        type=Path,
        default=Path("output/audit_report.json"),
        help="Path to audit_report.json"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/power_analysis.json"),
        help="Path to write power_analysis.json"
    )
    parser.add_argument(
        "--baseline-rate",
        type=float,
        default=0.10,
        help="Assumed baseline conversion rate"
    )
    parser.add_argument(
        "--detectable-effect",
        type=float,
        default=0.05,
        help="Minimum detectable effect size"
    )
    parser.add_argument(
        "--std-dev",
        type=float,
        default=1.0,
        help="Assumed standard deviation for continuous tests"
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
        "--min-corpus-size",
        type=int,
        default=300,
        help="Minimum required corpus size"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_power_analysis(
            audit_records_path=args.audit_records,
            output_path=args.output,
            baseline_rate=args.baseline_rate,
            detectable_effect=args.detectable_effect,
            std_dev=args.std_dev,
            alpha=args.alpha,
            power=args.power,
            min_corpus_size=args.min_corpus_size
        )
        
        # Exit with error code if validation failed
        if not result["validation"]["is_valid"]:
            audit_logger.error("ERR-028", "Power analysis validation failed: corpus size insufficient")
            return 1
        
        return 0
    except Exception as e:
        audit_logger.error("ERR-028", f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
