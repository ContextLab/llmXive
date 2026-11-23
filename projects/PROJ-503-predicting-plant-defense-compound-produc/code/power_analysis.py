"""
Power analysis module for determining sample size sufficiency.

Performs power analysis on the final paired set using F-test parameters.
Enforces abort criteria if N < 40 (Minimum Viable N for SC-001).
"""
import json
import logging
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

# Import local exception
from exceptions import E_POWER

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_z_score(effect_size: float) -> float:
    """
    Calculate z-score approximation for effect size in correlation context.
    Uses Fisher's z-transformation approximation for power calculation.
    
    Args:
        effect_size: The expected effect size (correlation coefficient r)
        
    Returns:
        float: z-score corresponding to the effect size
    """
    # Fisher's z-transformation
    if abs(effect_size) >= 1.0:
        raise ValueError("Effect size must be strictly between -1 and 1")
    z = 0.5 * math.log((1 + effect_size) / (1 - effect_size))
    return z


def calculate_required_n(effect_size: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """
    Calculate the required sample size for a given effect size, alpha, and power.
    Uses the standard formula for correlation power analysis.
    
    Formula: N = ((Z_alpha + Z_beta) / z_r)^2 + 3
    Where z_r is Fisher's z-transformed correlation.
    
    Args:
        effect_size: Expected correlation coefficient (r)
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.8)
        
    Returns:
        int: Required sample size N
    """
    if not 0 < effect_size < 1:
        raise ValueError("Effect size must be between 0 and 1 (exclusive)")
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1")
    if not 0 < power < 1:
        raise ValueError("Power must be between 0 and 1")
        
    # Z-scores for alpha and power
    # Using scipy.stats.norm.ppf would be ideal, but using numpy approximation
    # Z_alpha for two-tailed test:
    z_alpha = np.abs(np.percentile(np.random.randn(1000000), alpha * 100 / 2))
    # More precise calculation using scipy if available, else approximation
    try:
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power)
    except ImportError:
        # Fallback approximation if scipy not available
        # For alpha=0.05, z_alpha ~ 1.96
        # For power=0.8, z_beta ~ 0.84
        z_alpha = 1.96
        z_beta = 0.84
        
    z_r = calculate_z_score(effect_size)
    
    if z_r == 0:
        raise ValueError("Effect size results in zero z-score, cannot calculate N")
        
    n = ((z_alpha + z_beta) / z_r) ** 2 + 3
    return int(math.ceil(n))


def calculate_power(n: int, effect_size: float, alpha: float = 0.05) -> float:
    """
    Calculate statistical power given sample size, effect size, and alpha.
    
    Args:
        n: Sample size
        effect_size: Expected correlation coefficient (r)
        alpha: Significance level
        
    Returns:
        float: Statistical power (0 to 1)
    """
    if n < 3:
        return 0.0
        
    z_r = calculate_z_score(effect_size)
    
    try:
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = z_r * math.sqrt(n - 3) - z_alpha
        power = norm.cdf(z_beta)
    except ImportError:
        # Fallback approximation
        z_alpha = 1.96
        z_beta = z_r * math.sqrt(n - 3) - z_alpha
        # Approximate CDF
        power = 0.5 * (1 + math.erf(z_beta / math.sqrt(2)))
        
    return max(0.0, min(1.0, power))


def run_power_analysis(
    n_samples: int,
    effect_size: float = 0.5,
    alpha: float = 0.05,
    target_power: float = 0.8,
    min_viable_n: int = 40
) -> Dict[str, Any]:
    """
    Run power analysis on the paired dataset.
    
    Args:
        n_samples: Number of paired samples available
        effect_size: Expected effect size (default 0.5)
        alpha: Significance level (default 0.05)
        target_power: Target statistical power (default 0.8)
        min_viable_n: Minimum viable sample size threshold (default 40)
        
    Returns:
        dict: Power analysis results including N, power, effect_size, alpha, test_type
        
    Raises:
        E_POWER: If sample size is below minimum viable N
    """
    logger.info(f"Running power analysis with N={n_samples}, effect_size={effect_size}")
    
    # Calculate achieved power
    achieved_power = calculate_power(n_samples, effect_size, alpha)
    
    # Calculate required N for target power
    required_n = calculate_required_n(effect_size, alpha, target_power)
    
    result = {
        "N": n_samples,
        "power": round(achieved_power, 4),
        "effect_size": effect_size,
        "alpha": alpha,
        "test_type": "F-test (correlation)",
        "target_power": target_power,
        "required_n_for_target": required_n,
        "min_viable_n": min_viable_n,
        "meets_minimum_viable": n_samples >= min_viable_n,
        "meets_target_power": achieved_power >= target_power
    }
    
    logger.info(f"Power analysis result: N={n_samples}, Power={achieved_power:.4f}")
    
    # Check abort criteria
    if n_samples < min_viable_n:
        error_msg = (
            f"E-POWER: Sample size N={n_samples} is below minimum viable N={min_viable_n}. "
            f"Project aborted per SC-001. Required N for target power: {required_n}."
        )
        logger.error(error_msg)
        raise E_POWER(error_msg)
        
    if achieved_power < target_power:
        logger.warning(
            f"Power {achieved_power:.4f} is below target {target_power}. "
            f"Consider collecting more samples (required: {required_n})."
        )
    
    return result


def main():
    """
    Main entry point for power analysis script.
    Reads paired sample count from data/processed/paired_samples.csv
    and writes report to logs/power_analysis_report.json.
    """
    # Paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    paired_samples_path = project_root / "data" / "processed" / "paired_samples.csv"
    output_path = project_root / "logs" / "power_analysis_report.json"
    
    # Ensure logs directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load paired sample count
    if not paired_samples_path.exists():
        error_msg = f"Paired samples file not found: {paired_samples_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
        
    # Count samples from CSV (skip header)
    with open(paired_samples_path, 'r') as f:
        # Count lines excluding header
        lines = f.readlines()
        n_samples = len(lines) - 1 if len(lines) > 1 else 0
        
    if n_samples == 0:
        error_msg = "No paired samples found in paired_samples.csv"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    logger.info(f"Found {n_samples} paired samples")
    
    # Run power analysis
    try:
        result = run_power_analysis(
            n_samples=n_samples,
            effect_size=0.5,
            alpha=0.05,
            target_power=0.8,
            min_viable_n=40
        )
    except E_POWER as e:
        # Re-raise to trigger abort
        raise
        
    # Write report
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Power analysis report written to {output_path}")
    
    # Print summary
    print(f"Power Analysis Summary:")
    print(f"  N: {result['N']}")
    print(f"  Achieved Power: {result['power']}")
    print(f"  Target Power: {result['target_power']}")
    print(f"  Meets Minimum Viable N: {result['meets_minimum_viable']}")
    print(f"  Meets Target Power: {result['meets_target_power']}")
    
    if not result['meets_minimum_viable']:
        print("\nABORT: E-POWER triggered - sample size below minimum threshold")
        sys.exit(1)
        
    return result


if __name__ == "__main__":
    main()
