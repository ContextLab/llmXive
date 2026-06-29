"""
Power analysis utility for computing minimum sample size requirements.

Implements FR-025: Computes the minimum N given baseline, detectable effect,
alpha, and power. Writes result to output/power_analysis.json and asserts
audited corpus meets N >= 300 OR N >= calculated_minimum.

Depends on T010 (config.py with SEED = 42).
"""

import json
import logging
import csv
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from scipy import stats
import numpy as np

from code.src.config import set_rng_seed, get_config_summary
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants for power analysis
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_BASELINE = 0.10  # 10% baseline conversion rate
DEFAULT_EFFECT_SIZE = 0.05  # 5 percentage point detectable effect
MIN_CORPUS_SIZE = 300

# Output path
OUTPUT_DIR = Path("code/output")
OUTPUT_FILE = OUTPUT_DIR / "power_analysis.json"

# Synthetic dataset path for corpus size validation
SYNTHETIC_CSV = Path("code/data/synthetic/synthetic_validation.csv")

logger = get_default_logger(__name__)

def set_rng_seed_for_power_analysis():
    """Set RNG seed from config for reproducibility."""
    set_rng_seed()

def calculate_sample_size_binary(
    baseline: float,
    effect_size: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> float:
    """
    Calculate minimum sample size per group for a two-proportion z-test.
    
    Args:
        baseline: Baseline conversion rate (0-1)
        effect_size: Detectable effect size (absolute difference, 0-1)
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
    
    Returns:
        Minimum sample size per group (float)
    """
    if not (0 < baseline < 1):
        raise ValueError(f"Baseline must be between 0 and 1, got {baseline}")
    if not (0 < effect_size < 1):
        raise ValueError(f"Effect size must be between 0 and 1, got {effect_size}")
    if not (0 < alpha < 1):
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
    if not (0 < power < 1):
        raise ValueError(f"Power must be between 0 and 1, got {power}")
    
    # Effect size as absolute difference
    p1 = baseline
    p2 = baseline + effect_size
    
    if p2 >= 1:
        p2 = 0.99  # Cap at reasonable maximum
    
    # Pooled proportion under null
    p_pooled = (p1 + p2) / 2
    
    # Critical values
    z_alpha = stats.norm.ppf(1 - alpha / 2)  # Two-tailed
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula for two-proportion z-test
    # n = (z_alpha + z_beta)^2 * (p1*(1-p1) + p2*(1-p2)) / (p2 - p1)^2
    numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
    denominator = (p2 - p1) ** 2
    
    n_per_group = numerator / denominator
    
    return max(1.0, n_per_group)

def calculate_sample_size_continuous(
    effect_size: float,
    std_dev: float = 1.0,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> float:
    """
    Calculate minimum sample size per group for a two-sample t-test.
    
    Args:
        effect_size: Detectable effect size (absolute difference in means)
        std_dev: Standard deviation (default 1.0)
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
    
    Returns:
        Minimum sample size per group (float)
    """
    if not (0 < alpha < 1):
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
    if not (0 < power < 1):
        raise ValueError(f"Power must be between 0 and 1, got {power}")
    if std_dev <= 0:
        raise ValueError(f"Standard deviation must be positive, got {std_dev}")
    
    # Cohen's d effect size
    d = abs(effect_size) / std_dev
    
    # Critical values
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula for two-sample t-test
    n_per_group = 2 * ((z_alpha + z_beta) / d) ** 2
    
    return max(1.0, n_per_group)

def count_corpus_size(csv_path: Path) -> int:
    """
    Count the number of records in a CSV file.
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        Number of records (excluding header)
    """
    if not csv_path.exists():
        logger.warning(f"CSV file not found: {csv_path}")
        return 0
    
    with open(csv_path, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        count = sum(1 for _ in reader)
    
    return count

def run_power_analysis(
    baseline: float = DEFAULT_BASELINE,
    effect_size: float = DEFAULT_EFFECT_SIZE,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    corpus_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run complete power analysis and validate corpus size.
    
    Args:
        baseline: Baseline conversion rate
        effect_size: Detectable effect size
        alpha: Significance level
        power: Desired power
        corpus_path: Path to corpus CSV file (optional, uses synthetic if not provided)
    
    Returns:
        Dictionary with analysis results
    """
    # Set RNG seed for reproducibility
    set_rng_seed_for_power_analysis()
    
    # Calculate minimum sample size for binary outcome
    n_binary = calculate_sample_size_binary(baseline, effect_size, alpha, power)
    
    # Calculate minimum sample size for continuous outcome
    n_continuous = calculate_sample_size_continuous(effect_size, std_dev=1.0, alpha=alpha, power=power)
    
    # Determine required N (use the larger of the two)
    calculated_minimum = max(n_binary, n_continuous)
    
    # Get corpus size
    if corpus_path is None:
        corpus_path = SYNTHETIC_CSV
    
    corpus_size = count_corpus_size(corpus_path)
    
    # Validate corpus size: N >= 300 OR N >= calculated_minimum
    meets_requirement = corpus_size >= MIN_CORPUS_SIZE or corpus_size >= calculated_minimum
    
    result = {
        "baseline_rate": baseline,
        "detectable_effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "minimum_sample_size_binary": round(n_binary, 2),
        "minimum_sample_size_continuous": round(n_continuous, 2),
        "calculated_minimum": round(calculated_minimum, 2),
        "corpus_size": corpus_size,
        "minimum_corpus_requirement": MIN_CORPUS_SIZE,
        "meets_requirement": meets_requirement,
        "requirement_logic": f"N >= {MIN_CORPUS_SIZE} OR N >= {round(calculated_minimum, 2)}",
        "config_summary": get_config_summary()
    }
    
    return result

def write_power_analysis_result(result: Dict[str, Any], output_path: Path) -> None:
    """
    Write power analysis result to JSON file.
    
    Args:
        result: Dictionary with analysis results
        output_path: Path to output JSON file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Power analysis result written to {output_path}")

def main():
    """Main entry point for power analysis."""
    logger.info("Starting power analysis...")
    
    # Run analysis with default parameters
    result = run_power_analysis(
        baseline=DEFAULT_BASELINE,
        effect_size=DEFAULT_EFFECT_SIZE,
        alpha=DEFAULT_ALPHA,
        power=DEFAULT_POWER
    )
    
    # Write result to output file
    write_power_analysis_result(result, OUTPUT_FILE)
    
    # Verify output
    if not OUTPUT_FILE.exists():
        logger.error(f"Output file not created: {OUTPUT_FILE}")
        return 1
    
    # Verify JSON is valid and contains required fields
    with open(OUTPUT_FILE, 'r') as f:
        loaded_result = json.load(f)
    
    required_fields = [
        "calculated_minimum",
        "corpus_size",
        "meets_requirement"
    ]
    
    for field in required_fields:
        if field not in loaded_result:
            logger.error(f"Missing required field: {field}")
            return 1
    
    # Verify numeric N exists
    if not isinstance(loaded_result["calculated_minimum"], (int, float)):
        logger.error("calculated_minimum must be numeric")
        return 1
    
    # Verify condition is satisfied
    if not loaded_result["meets_requirement"]:
        logger.error(f"Corpus size {loaded_result['corpus_size']} does not meet requirement")
        return 1
    
    logger.info("Power analysis completed successfully")
    logger.info(f"Corpus size: {loaded_result['corpus_size']}")
    logger.info(f"Calculated minimum: {loaded_result['calculated_minimum']}")
    logger.info(f"Meets requirement: {loaded_result['meets_requirement']}")
    
    return 0

if __name__ == "__main__":
    exit(main())
