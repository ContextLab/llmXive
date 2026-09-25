"""
Statistical power analysis utilities for the llmXive research pipeline.
Calculates statistical power and margin of error for correlation studies.
"""
import os
import math
import argparse
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import pandas as pd

# Import logger from local utils
from src.utils.logger import get_logger

def calculate_effect_size(r: float) -> float:
    """
    Calculate Cohen's q (effect size for correlation difference) or Fisher's z.
    Here we use Fisher's z-transformation for correlation coefficients.
    
    Args:
        r: Pearson or Spearman correlation coefficient.
    
    Returns:
        Fisher's z transformed value.
    """
    # Clamp r to [-0.999, 0.999] to avoid log(0)
    r = max(-0.999, min(0.999, r))
    return 0.5 * math.log((1 + r) / (1 - r))

def calculate_power_spearman(sample_size: int, effect_size: float, alpha: float = 0.05) -> float:
    """
    Calculate statistical power for a Spearman correlation test.
    
    Args:
        sample_size: Number of observations.
        effect_size: Expected correlation coefficient (r).
        alpha: Significance level (default 0.05).
    
    Returns:
        Statistical power (probability of rejecting null when false).
    """
    if sample_size < 3:
        return 0.0
    
    # Fisher's z transformation
    z_r = calculate_effect_size(effect_size)
    
    # Standard error of z_r
    se = 1.0 / math.sqrt(sample_size - 3)
    
    # Critical z value for two-tailed test
    from scipy.stats import norm
    z_crit = norm.ppf(1 - alpha / 2)
    
    # Power calculation
    # Under H1, z follows N(z_r, se^2)
    # We reject H0 if |z| > z_crit * se (approx)
    # Power = P(|Z| > z_crit | H1)
    
    # Non-centrality parameter
    delta = z_r / se
    
    # Power = P(Z > z_crit - delta) + P(Z < -z_crit - delta)
    power = norm.cdf(delta - z_crit) + (1 - norm.cdf(delta + z_crit))
    
    return max(0.0, min(1.0, power))

def calculate_margin_of_error(sample_size: int, confidence_level: float = 0.95) -> float:
    """
    Calculate the margin of error for a correlation estimate.
    
    Args:
        sample_size: Number of observations.
        confidence_level: Confidence level (default 0.95).
    
    Returns:
        Margin of error in correlation units.
    """
    if sample_size < 3:
        return float('inf')
    
    from scipy.stats import norm
    z = norm.ppf((1 + confidence_level) / 2)
    se = 1.0 / math.sqrt(sample_size - 3)
    
    # Margin of error in Fisher's z space
    moe_z = z * se
    
    # Convert back to correlation space (approximate)
    # Using the inverse Fisher transform
    moe_r = math.tanh(moe_z)
    
    return moe_r

def run_power_analysis(sample_size: int, effect_size: float, alpha: float = 0.05, 
                       output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a complete power analysis and optionally write results to a file.
    
    Args:
        sample_size: Number of observations.
        effect_size: Expected correlation coefficient.
        alpha: Significance level.
        output_path: Optional path to write the report (TSV).
    
    Returns:
        Dictionary containing power, margin_of_error, and sample_size.
    """
    logger = get_logger(__name__)
    
    power = calculate_power_spearman(sample_size, effect_size, alpha)
    margin_of_error = calculate_margin_of_error(sample_size)
    
    result = {
        "sample_size": sample_size,
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "margin_of_error": margin_of_error
    }
    
    logger.info(f"Power Analysis: n={sample_size}, r={effect_size}, Power={power:.4f}, MoE={margin_of_error:.4f}")
    
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame([result])
        df.to_csv(output_file, sep='\t', index=False)
        logger.info(f"Power analysis report written to: {output_path}")
    
    return result

def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the power analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Calculate statistical power and margin of error for correlation studies."
    )
    parser.add_argument(
        "--sample-size", "-n",
        type=int,
        required=True,
        help="Number of observations in the study."
    )
    parser.add_argument(
        "--effect-size", "-r",
        type=float,
        required=True,
        help="Expected correlation coefficient (r)."
    )
    parser.add_argument(
        "--alpha", "-a",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to write the output TSV report."
    )
    return parser

def main():
    """Main entry point for CLI execution."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    
    try:
        result = run_power_analysis(
            sample_size=args.sample_size,
            effect_size=args.effect_size,
            alpha=args.alpha,
            output_path=args.output
        )
        print(f"Power: {result['power']:.4f}")
        print(f"Margin of Error: {result['margin_of_error']:.4f}")
        return 0
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
