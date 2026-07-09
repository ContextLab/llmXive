"""
Power analysis utility for determining minimum sample size requirements.
Implements FR-025: Computes minimum N given baseline, detectable effect, alpha, and power.
Validates corpus size against statistical power requirements from literature.
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

# Set default logger
logger = get_default_logger()

def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Set random seed for reproducibility in power analysis."""
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
        baseline_rate: Expected conversion rate in control group (0-1)
        detectable_effect: Minimum detectable difference in rates (absolute)
        alpha: Significance level (Type I error rate)
        power: Desired statistical power (1 - Type II error rate)
        two_sided: Whether to use two-sided test
    
    Returns:
        Minimum sample size per group (float, can be rounded up)
    
    Formula based on normal approximation for two-proportion test:
    n = 2 * (Z_alpha/2 + Z_beta)^2 * p_bar * (1 - p_bar) / effect^2
    where p_bar = (p1 + p2) / 2
    """
    if not 0 < baseline_rate < 1:
        raise ValueError(f"Baseline rate must be between 0 and 1, got {baseline_rate}")
    if not 0 < detectable_effect < 1:
        raise ValueError(f"Detectable effect must be between 0 and 1, got {detectable_effect}")
    if baseline_rate + detectable_effect >= 1:
        raise ValueError(f"Baseline + effect ({baseline_rate + detectable_effect}) must be < 1")
    
    p1 = baseline_rate
    p2 = baseline_rate + detectable_effect
    p_bar = (p1 + p2) / 2
    
    # Critical values
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Sample size calculation
    numerator = 2 * (z_alpha + z_beta) ** 2 * p_bar * (1 - p_bar)
    denominator = (p2 - p1) ** 2
    
    n = numerator / denominator
    return n

def calculate_sample_size_continuous(
    baseline_mean: float,
    detectable_effect: float,
    std_dev: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True
) -> float:
    """
    Calculate minimum sample size per group for a Welch's t-test.
    
    Args:
        baseline_mean: Expected mean in control group
        detectable_effect: Minimum detectable difference in means
        std_dev: Expected standard deviation (assumed equal for both groups)
        alpha: Significance level
        power: Desired statistical power
        two_sided: Whether to use two-sided test
    
    Returns:
        Minimum sample size per group
    """
    if std_dev <= 0:
        raise ValueError(f"Standard deviation must be positive, got {std_dev}")
    
    # Effect size (Cohen's d)
    effect_size = detectable_effect / std_dev
    
    # Critical values
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Sample size calculation for t-test (normal approximation)
    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return n

def count_corpus_size(
    audit_records_path: Path,
    exclude_inconsistent: bool = True
) -> int:
    """
    Count the number of valid audit records in the corpus.
    
    Args:
        audit_records_path: Path to audit_report.json
        exclude_inconsistent: If True, only count consistent records
    
    Returns:
        Number of records
    """
    if not audit_records_path.exists():
        logger.warning(f"Audit records file not found: {audit_records_path}")
        return 0
    
    try:
        with open(audit_records_path, 'r') as f:
            records = json.load(f)
    
        if not isinstance(records, list):
            logger.error(f"Audit report should be a list, got {type(records)}")
            return 0
    
        count = 0
        for record in records:
            if exclude_inconsistent:
                # Only count records that passed validation (no inconsistency flags)
                # Assuming 'is_consistent' field or absence of 'inconsistency_flags'
                if record.get('is_consistent', True) or not record.get('inconsistency_flags'):
                    count += 1
            else:
                count += 1
    
        return count
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse audit report: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error reading audit records: {e}")
        return 0

def write_power_analysis_result(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write power analysis results to JSON file.
    
    Args:
        result: Dictionary containing power analysis results
        output_path: Path to write the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Power analysis results written to {output_path}")

def run_power_analysis(
    audit_records_path: Path,
    output_path: Path,
    baseline_rate: float = 0.10,
    detectable_effect: float = 0.02,
    alpha: float = 0.05,
    power: float = 0.80,
    std_dev: float = 1.0
) -> Dict[str, Any]:
    """
    Run full power analysis and validate corpus meets requirements.
    
    Args:
        audit_records_path: Path to audit_report.json
        output_path: Path to write power_analysis.json
        baseline_rate: Assumed baseline conversion rate
        detectable_effect: Minimum detectable effect size
        alpha: Significance level
        power: Desired statistical power
        std_dev: Standard deviation for continuous outcomes
    
    Returns:
        Dictionary with analysis results
    """
    # Calculate required sample sizes
    n_binary = calculate_sample_size_binary(
        baseline_rate=baseline_rate,
        detectable_effect=detectable_effect,
        alpha=alpha,
        power=power
    )
    
    n_continuous = calculate_sample_size_continuous(
        baseline_mean=0,  # Not used in effect size calculation
        detectable_effect=detectable_effect * std_dev,  # Convert to absolute effect
        std_dev=std_dev,
        alpha=alpha,
        power=power
    )
    
    # Count actual corpus size
    corpus_size = count_corpus_size(audit_records_path, exclude_inconsistent=True)
    
    # Check against claim c_21f3e400 (2510.17487)
    # The claim requires corpus size to be sufficient for detecting effect sizes
    # with 80% power at alpha=0.05. We verify this by comparing actual vs required.
    claim_reference = "2510.17487"
    claim_url = "https://arxiv.org/abs/2510.17487"
    
    # For binary outcomes (most common in A/B tests)
    meets_binary_requirement = corpus_size >= n_binary
    meets_continuous_requirement = corpus_size >= n_continuous
    
    # Overall assessment
    meets_requirement = meets_binary_requirement and corpus_size > 0
    
    result = {
        "analysis_parameters": {
            "baseline_rate": baseline_rate,
            "detectable_effect": detectable_effect,
            "alpha": alpha,
            "power": power,
            "std_dev": std_dev
        },
        "required_sample_sizes": {
            "binary_outcome_per_group": round(n_binary, 2),
            "continuous_outcome_per_group": round(n_continuous, 2)
        },
        "actual_corpus_size": corpus_size,
        "validation": {
            "meets_binary_requirement": meets_binary_requirement,
            "meets_continuous_requirement": meets_continuous_requirement,
            "meets_overall_requirement": meets_requirement,
            "claim_reference": claim_reference,
            "claim_url": claim_url,
            "note": "Corpus size is sufficient to detect the specified effect size with 80% power" if meets_requirement else "Corpus size is insufficient for the specified effect size"
        },
        "metadata": {
            "timestamp": str(datetime.now()),
            "tool": "power_analysis_utility",
            "version": "1.0.0"
        }
    }
    
    write_power_analysis_result(result, output_path)
    return result

def main() -> int:
    """
    Main entry point for power analysis utility.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Set random seed
    set_rng_seed_for_power_analysis(SEED)
    
    # Default paths
    base_dir = Path(__file__).parent.parent.parent.parent
    audit_records_path = base_dir / "output" / "audit_report.json"
    output_path = base_dir / "output" / "power_analysis.json"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        audit_records_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    
    logger.info(f"Starting power analysis")
    logger.info(f"Audit records: {audit_records_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        result = run_power_analysis(
            audit_records_path=audit_records_path,
            output_path=output_path,
            baseline_rate=0.10,  # Default 10% baseline
            detectable_effect=0.02,  # Default 2% absolute effect
            alpha=0.05,
            power=0.80,
            std_dev=1.0
        )
        
        logger.info(f"Power analysis complete")
        logger.info(f"Corpus size: {result['actual_corpus_size']}")
        logger.info(f"Required for binary: {result['required_sample_sizes']['binary_outcome_per_group']}")
        logger.info(f"Meets requirement: {result['validation']['meets_overall_requirement']}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
