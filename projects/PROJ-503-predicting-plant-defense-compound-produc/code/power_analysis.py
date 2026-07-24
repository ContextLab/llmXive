"""
Power analysis utility for Phase 0.
Calculates required sample size for correlation-based hypothesis testing.
Implements abort logic if required n < 28 per plan.md T009/T015.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import numpy as np
from scipy.stats import norm

from exceptions import E_POWER

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_REQUIRED_N = 28  # Per plan.md T009/T015

def calculate_z_score(alpha: float = 0.05, power: float = 0.8) -> tuple:
    """
    Calculate Z-scores for significance level and desired power.
    
    Args:
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.8)
        
    Returns:
        Tuple of (Z_alpha, Z_beta)
    """
    # Two-tailed test: divide alpha by 2
    z_alpha = norm.ppf(1 - alpha / 2)
    # Power = 1 - beta
    z_beta = norm.ppf(power)
    return z_alpha, z_beta

def calculate_required_n(effect_size: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """
    Calculate required sample size for correlation test.
    
    Uses Fisher's z-transformation for correlation power analysis.
    Formula: n = [(Z_alpha + Z_beta) / 0.5 * ln((1+r)/(1-r))]^2 + 3
    
    Args:
        effect_size: Expected correlation coefficient (r)
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.8)
        
    Returns:
        Required sample size (n)
        
    Raises:
        ValueError: If effect_size is outside valid range [-1, 1]
    """
    if not -1 < effect_size < 1:
        raise ValueError(f"Effect size must be in (-1, 1), got {effect_size}")
    
    z_alpha, z_beta = calculate_z_score(alpha, power)
    
    # Fisher's z-transformation
    z_r = 0.5 * np.log((1 + effect_size) / (1 - effect_size))
    
    # Calculate required n
    # n = ((Z_alpha + Z_beta) / z_r)^2 + 3
    n = ((z_alpha + z_beta) / z_r) ** 2 + 3
    
    return int(np.ceil(n))

def run_power_analysis(
    effect_size: float = 0.5,
    alpha: float = 0.05,
    power: float = 0.8,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Run power analysis and optionally save results to JSON.
    
    Args:
        effect_size: Expected correlation coefficient (r)
        alpha: Significance level
        power: Desired statistical power
        output_path: Path to save JSON results (default: logs/power_analysis.json)
        
    Returns:
        Dictionary containing analysis results
        
    Raises:
        E_POWER: If required n < MIN_REQUIRED_N (28)
    """
    if output_path is None:
        output_path = Path("projects/PROJ-503-predicting-plant-defense-compound-produc/logs/power_analysis.json")
    else:
        output_path = Path(output_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate required sample size
    required_n = calculate_required_n(effect_size, alpha, power)
    
    # Prepare results
    results = {
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "required_n": required_n,
        "min_required_n": MIN_REQUIRED_N,
        "passes_threshold": required_n >= MIN_REQUIRED_N,
        "status": "PASS" if required_n >= MIN_REQUIRED_N else "FAIL"
    }
    
    # Log results
    logger.info(f"Power Analysis Results:")
    logger.info(f"  Effect size (r): {effect_size}")
    logger.info(f"  Alpha: {alpha}")
    logger.info(f"  Power: {power}")
    logger.info(f"  Required sample size (n): {required_n}")
    logger.info(f"  Minimum required (n >= {MIN_REQUIRED_N}): {results['passes_threshold']}")
    logger.info(f"  Status: {results['status']}")
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {output_path}")
    
    # Check abort condition
    if required_n < MIN_REQUIRED_N:
        error_msg = (
            f"Power analysis failed: Required sample size (n={required_n}) "
            f"is below minimum threshold (n={MIN_REQUIRED_N}). "
            f"Project must abort per plan.md T009/T015."
        )
        logger.error(error_msg)
        raise E_POWER(error_msg)
    
    return results

def main():
    """Main entry point for power analysis script."""
    try:
        # Default parameters as specified in task
        effect_size = 0.5
        alpha = 0.05
        power = 0.8
        
        output_path = Path(
            "projects/PROJ-503-predicting-plant-defense-compound-produc/logs/power_analysis.json"
        )
        
        logger.info("Starting power analysis...")
        logger.info(f"Parameters: r={effect_size}, alpha={alpha}, power={power}")
        
        results = run_power_analysis(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            output_path=str(output_path)
        )
        
        logger.info("Power analysis completed successfully.")
        return 0
        
    except E_POWER as e:
        logger.error(f"Power analysis failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
