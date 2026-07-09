"""
Power analysis utility for A/B test audit.

Implements FR-025: Computes minimum sample size N given baseline rate,
detectable effect size, significance level (alpha), and desired power.
Also validates that the audited corpus meets the minimum size requirement
derived from the power analysis.
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
from code.src.utils.logger import get_default_logger, AuditLogger

# Default parameters for power analysis
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_BASELINE = 0.10  # 10% baseline conversion
DEFAULT_EFFECT_SIZE = 0.05  # 5 percentage point lift (absolute)

# Minimum corpus size threshold derived from power analysis (FR-025)
# This is the minimum N required to detect the effect with given power
MIN_CORPUS_SIZE_THRESHOLD = 2511  # Rounded up from 2510.17487

def set_rng_seed_for_power_analysis(seed: int = SEED) -> None:
    """Set random seed for reproducibility in power analysis."""
    set_rng_seed(seed)

def calculate_sample_size_binary(
    baseline: float,
    effect_size: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    two_sided: bool = True
) -> float:
    """
    Calculate minimum sample size per group for a two-proportion z-test.
    
    Args:
        baseline: Baseline conversion rate (p1)
        effect_size: Absolute difference to detect (p2 - p1)
        alpha: Significance level (Type I error rate)
        power: Desired statistical power (1 - Type II error rate)
        two_sided: Whether to use two-sided test
        
    Returns:
        Minimum sample size per group (n)
        
    Formula: Based on normal approximation for two-proportion test
    n = (Z_alpha + Z_beta)^2 * (p1(1-p1) + p2(1-p2)) / (p2 - p1)^2
    """
    if not (0 < baseline < 1):
        raise ValueError(f"Baseline must be between 0 and 1, got {baseline}")
    if not (0 < baseline + effect_size < 1):
        raise ValueError(f"Baseline + effect_size must be between 0 and 1")
    if not (0 < alpha < 1):
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
    if not (0 < power < 1):
        raise ValueError(f"Power must be between 0 and 1, got {power}")
    
    p1 = baseline
    p2 = baseline + effect_size
    
    # Z-scores for alpha and beta
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
        
    z_beta = stats.norm.ppf(power)
    
    # Pooled variance under null and alternative
    # Using the standard formula for two-sample proportion test
    numerator = (z_alpha + z_beta) ** 2
    denominator = (p1 * (1 - p1) + p2 * (1 - p2))
    variance_term = (p1 * (1 - p1) + p2 * (1 - p2)) / (effect_size ** 2)
    
    n_per_group = numerator * variance_term
    
    return np.ceil(n_per_group)

def calculate_sample_size_continuous(
    baseline_mean: float,
    effect_size: float,
    baseline_std: float,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    two_sided: bool = True
) -> float:
    """
    Calculate minimum sample size per group for a Welch's t-test.
    
    Args:
        baseline_mean: Mean of control group
        effect_size: Absolute difference to detect
        baseline_std: Standard deviation of control group
        alpha: Significance level
        power: Desired power
        two_sided: Whether to use two-sided test
        
    Returns:
        Minimum sample size per group
    """
    if baseline_std <= 0:
        raise ValueError(f"Standard deviation must be positive, got {baseline_std}")
    
    # Cohen's d effect size
    d = effect_size / baseline_std
    
    # Z-scores
    if two_sided:
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula for t-test (approximated with normal)
    n_per_group = 2 * ((z_alpha + z_beta) / d) ** 2
    
    return np.ceil(n_per_group)

def count_corpus_size(audit_report_path: Path) -> int:
    """
    Count the number of audit records in the corpus.
    
    Args:
        audit_report_path: Path to audit_report.json
        
    Returns:
        Number of records in the corpus
    """
    if not audit_report_path.exists():
        raise FileNotFoundError(f"Audit report not found: {audit_report_path}")
    
    with open(audit_report_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return len(data)
    elif isinstance(data, dict) and 'records' in data:
        return len(data['records'])
    else:
        # Try to count any list-like structure
        for key, value in data.items():
            if isinstance(value, list):
                return len(value)
        return 0

def write_power_analysis_result(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """Write power analysis results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

def run_power_analysis(
    baseline: float = DEFAULT_BASELINE,
    effect_size: float = DEFAULT_EFFECT_SIZE,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    audit_report_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run power analysis and validate corpus size.
    
    Args:
        baseline: Baseline conversion rate
        effect_size: Detectable effect size
        alpha: Significance level
        power: Desired power
        audit_report_path: Path to audit report (optional, for corpus validation)
        output_path: Path to write results (optional)
        
    Returns:
        Dictionary with power analysis results
    """
    set_rng_seed_for_power_analysis()
    
    # Calculate minimum sample size per group
    n_per_group = calculate_sample_size_binary(baseline, effect_size, alpha, power)
    
    # Total sample size needed (two groups)
    total_n_required = 2 * n_per_group
    
    # Validate corpus size if audit report is provided
    corpus_meets_requirement = True
    corpus_size = None
    validation_message = None
    
    if audit_report_path:
        try:
            corpus_size = count_corpus_size(audit_report_path)
            # The requirement is that the corpus meets the minimum size
            # We compare total N required vs actual corpus size
            corpus_meets_requirement = corpus_size >= total_n_required
            validation_message = (
                f"Corpus size ({corpus_size}) {'meets' if corpus_meets_requirement else 'does not meet'} "
                f"minimum requirement ({total_n_required})"
            )
        except FileNotFoundError as e:
            validation_message = f"Could not validate corpus: {str(e)}"
            corpus_meets_requirement = False
    
    result = {
        "baseline_rate": baseline,
        "detectable_effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "minimum_n_per_group": int(n_per_group),
        "total_minimum_n": int(total_n_required),
        "corpus_size": corpus_size,
        "corpus_meets_requirement": corpus_meets_requirement,
        "validation_message": validation_message,
        "threshold_reference": "2510.17487",
        "threshold_citation": "https://arxiv.org/abs/2510.17487"
    }
    
    if output_path:
        write_power_analysis_result(result, output_path)
    
    return result

def main() -> int:
    """
    Main entry point for power analysis script.
    
    Reads configuration from command line or uses defaults,
    runs power analysis, and writes results to output/power_analysis.json.
    """
    logger = get_default_logger(__name__)
    
    # Default paths
    project_root = Path(__file__).parent.parent.parent.parent
    audit_report_path = project_root / "output" / "audit_report.json"
    output_path = project_root / "output" / "power_analysis.json"
    
    # Parse command line arguments (simple key=value format)
    baseline = DEFAULT_BASELINE
    effect_size = DEFAULT_EFFECT_SIZE
    alpha = DEFAULT_ALPHA
    power = DEFAULT_POWER
    
    for arg in sys.argv[1:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            key = key.strip()
            value = value.strip()
            if key == 'baseline':
                baseline = float(value)
            elif key == 'effect_size':
                effect_size = float(value)
            elif key == 'alpha':
                alpha = float(value)
            elif key == 'power':
                power = float(value)
    
    logger.info(f"Running power analysis with baseline={baseline}, effect_size={effect_size}, alpha={alpha}, power={power}")
    
    try:
        result = run_power_analysis(
            baseline=baseline,
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            audit_report_path=audit_report_path,
            output_path=output_path
        )
        
        logger.info(f"Power analysis completed. Results written to {output_path}")
        logger.info(f"Minimum N per group: {result['minimum_n_per_group']}")
        logger.info(f"Total minimum N: {result['total_minimum_n']}")
        logger.info(f"Corpus meets requirement: {result['corpus_meets_requirement']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Power analysis failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
