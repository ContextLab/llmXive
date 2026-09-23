import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
from scipy.stats import norm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants as per SC-006 and Assumptions
DEFAULT_EFFECT_SIZE = 0.2  # rho >= 0.2
DEFAULT_ALPHA = 0.05
TARGET_POWER = 0.8


def load_dependencies_data() -> Dict[str, Any]:
    """
    Loads the metrics from data/processed/metrics.json to determine sample size.
    Raises FileNotFoundError if the file does not exist.
    """
    metrics_path = Path("data/processed/metrics.json")
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {metrics_path}. "
            "Please run T019 (collect_data.py) first to generate metrics.json."
        )
    
    with open(metrics_path, 'r') as f:
        return json.load(f)


def calculate_effect_size() -> float:
    """
    Returns the assumed effect size (rho) for the power analysis.
    Per SC-006, effect_size >= 0.2.
    """
    return DEFAULT_EFFECT_SIZE


def calculate_power(effect_size: float, sample_size: int, alpha: float = 0.05) -> float:
    """
    Calculates the statistical power for a Spearman correlation test.
    
    Uses the normal approximation for the power of a correlation test.
    Fisher's z-transformation is used to normalize the correlation coefficient.
    
    Formula:
    z_r = 0.5 * ln((1+r)/(1-r))
    SE = 1 / sqrt(n - 3)
    z_beta = z_alpha - (|z_r| / SE)
    Power = Phi(z_beta)
    
    Args:
        effect_size (float): The expected correlation coefficient (rho).
        sample_size (int): The number of observations (N).
        alpha (float): Significance level.
        
    Returns:
        float: Calculated statistical power (0 to 1).
    """
    if sample_size <= 3:
        logger.warning("Sample size too small for Fisher transformation (n <= 3). Returning 0.")
        return 0.0
    
    # Fisher's z-transformation of the correlation coefficient
    # Clamp effect_size to (-1, 1) to avoid log domain errors
    r = np.clip(effect_size, -0.9999, 0.9999)
    z_r = 0.5 * np.log((1 + r) / (1 - r))
    
    # Standard error of z_r
    se = 1.0 / np.sqrt(sample_size - 3)
    
    # Critical z-value for the given alpha (two-tailed)
    # For alpha=0.05, z_alpha is approx 1.96
    z_alpha = norm.ppf(1 - alpha / 2)
    
    # Calculate z_beta (non-centrality parameter relative to critical value)
    # We are testing H0: rho = 0 vs H1: rho != 0
    # The distribution of z_r under H1 is N(z_r, SE^2)
    # Power = P(|Z| > z_alpha | H1)
    #       = P(Z > z_alpha - z_r/SE) + P(Z < -z_alpha - z_r/SE)
    # Since z_r is positive (assuming positive correlation), the second term is negligible.
    # Power approx = 1 - Phi(z_alpha - z_r/SE) = Phi(z_r/SE - z_alpha)
    
    z_beta = (abs(z_r) / se) - z_alpha
    power = norm.cdf(z_beta)
    
    return power


def run_power_analysis() -> Dict[str, Any]:
    """
    Runs the full power analysis pipeline.
    
    1. Loads sample size (N) from data/processed/metrics.json.
    2. Calculates power using default parameters (effect_size=0.2, alpha=0.05).
    3. Returns a dictionary with the results.
    
    Raises:
        FileNotFoundError: If metrics.json is missing.
        ValueError: If sample size is insufficient.
    """
    logger.info("Starting power analysis...")
    
    # Load data
    metrics = load_dependencies_data()
    sample_size = metrics.get("total_dependencies")
    
    if sample_size is None:
        raise ValueError("Could not find 'total_dependencies' in data/processed/metrics.json")
    
    if not isinstance(sample_size, int) or sample_size <= 0:
        raise ValueError(f"Invalid sample size: {sample_size}. Must be a positive integer.")
    
    logger.info(f"Loaded sample size (N): {sample_size}")
    
    # Parameters
    effect_size = calculate_effect_size()
    alpha = DEFAULT_ALPHA
    
    # Calculate power
    actual_power = calculate_power(effect_size, sample_size, alpha)
    
    # Verify against target
    meets_target = actual_power >= TARGET_POWER
    
    result = {
        "effect_size": effect_size,
        "alpha": alpha,
        "sample_size": sample_size,
        "actual_power": float(actual_power),
        "target_power": TARGET_POWER,
        "meets_target": meets_target,
        "methodology_notes": (
            f"Power calculated using Fisher's z-transformation for Spearman correlation. "
            f"Assumed effect size (rho) = {effect_size}, alpha = {alpha}. "
            f"Sample size N = {sample_size}. "
            f"{'Power meets target (>= 0.8).' if meets_target else 'Power is below target (0.8). Consider increasing sample size or accepting lower power.'}"
        )
    }
    
    logger.info(f"Power analysis complete. Actual Power: {actual_power:.4f}, Meets Target: {meets_target}")
    
    return result


def main():
    """
    Main entry point for the power analysis script.
    Reads from data/processed/metrics.json and writes to data/processed/power_analysis.json.
    """
    try:
        result = run_power_analysis()
        
        output_path = Path("data/processed/power_analysis.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Power analysis results written to {output_path}")
        print(f"Success: {output_path} created.")
        print(f"  Effect Size: {result['effect_size']}")
        print(f"  Sample Size: {result['sample_size']}")
        print(f"  Actual Power: {result['actual_power']:.4f}")
        print(f"  Meets Target (0.8): {result['meets_target']}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during power analysis: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()