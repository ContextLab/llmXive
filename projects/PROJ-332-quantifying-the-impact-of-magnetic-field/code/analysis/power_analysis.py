"""
Power analysis module for statistical validation of correlation studies.

This module implements power calculation for correlation tests as required by FR-008.
It calculates the statistical power to detect a specified effect size given the
sample size, and determines if the study is adequately powered.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from scipy import stats
from utils.logger import get_logger
from analysis.correlation import calculate_power, check_power_sufficiency

logger = get_logger(__name__)

def calculate_power_for_correlation(n: int, r: float = 0.5, alpha: float = 0.05) -> float:
    """
    Calculate statistical power for a Pearson correlation test.
    
    This implements the power calculation using Fisher's z-transformation
    as per standard statistical methodology (similar to 'pwr.r.test' in R).
    
    Args:
        n: Sample size (number of discharges)
        r: Expected effect size (correlation coefficient), default 0.5 (medium effect)
        alpha: Significance level, default 0.05
        
    Returns:
        Power value between 0 and 1
        
    Raises:
        ValueError: If sample size is too small
    """
    if n < 3:
        raise ValueError(f"Sample size must be at least 3, got {n}")
        
    # Fisher's z transformation of the correlation coefficient
    # z = 0.5 * ln((1+r)/(1-r))
    z_r = 0.5 * np.log((1 + r) / (1 - r))
    
    # Standard error of z_r
    se = 1.0 / np.sqrt(n - 3)
    
    # Critical z value for alpha (two-tailed test)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    
    # Non-centrality parameter
    delta = z_r / se
    
    # Power calculation:
    # For a two-tailed test, power is the probability that the test statistic
    # falls in the rejection region under the alternative hypothesis
    # Power = P(Z > z_crit - delta) + P(Z < -z_crit - delta)
    power_upper = 1 - stats.norm.cdf(z_crit - delta)
    power_lower = stats.norm.cdf(-z_crit - delta)
    
    power = power_upper + power_lower
    
    # Ensure power is within [0, 1]
    power = max(0.0, min(1.0, power))
    
    return float(power)

def check_power_sufficiency(power: float, threshold: float = 0.20) -> Tuple[bool, str]:
    """
    Check if statistical power is sufficient for the study.
    
    Args:
        power: Calculated power value
        threshold: Minimum acceptable power (default 0.20 per FR-008)
        
    Returns:
        Tuple of (is_sufficient, status_message)
    """
    if power < threshold:
        return False, f"Inconclusive due to low power (power={power:.3f} < {threshold})"
    return True, f"Power sufficient (power={power:.3f})"

def run_power_analysis(df: pd.DataFrame, sample_size_col: Optional[str] = None,
                      effect_size: float = 0.5, alpha: float = 0.05,
                      power_threshold: float = 0.20) -> Dict[str, Any]:
    """
    Run power analysis on the dataset.
    
    Args:
        df: DataFrame containing the data (used to determine sample size)
        sample_size_col: Column name for sample size (if not using df length)
        effect_size: Expected correlation coefficient to detect, default 0.5
        alpha: Significance level, default 0.05
        power_threshold: Minimum acceptable power, default 0.20
        
    Returns:
        Dictionary with power analysis results:
        - n: Sample size
        - effect_size: Expected effect size
        - alpha: Significance level
        - power: Calculated power
        - is_sufficient: Boolean indicating if power is sufficient
        - status_message: Human-readable status
        - warning_flag: Flag if power is insufficient
    """
    # Determine sample size
    if sample_size_col:
        if sample_size_col not in df.columns:
            logger.warning(f"Sample size column '{sample_size_col}' not found, using DataFrame length")
            n = len(df)
        else:
            n = int(df[sample_size_col].iloc[0]) if len(df) > 0 else 0
    else:
        n = len(df)
    
    logger.info(f"Running power analysis: n={n}, effect_size={effect_size}, alpha={alpha}")
    
    if n < 3:
        logger.warning(f"Insufficient sample size for power analysis: n={n}")
        return {
            'n': n,
            'effect_size': effect_size,
            'alpha': alpha,
            'power': 0.0,
            'is_sufficient': False,
            'status_message': f"Inconclusive due to low power (power=0.000 < {power_threshold})",
            'warning_flag': 'Insufficient sample size for power analysis'
        }
    
    # Calculate power
    power = calculate_power_for_correlation(n, effect_size, alpha)
    
    # Check sufficiency
    is_sufficient, status_message = check_power_sufficiency(power, power_threshold)
    
    result = {
        'n': n,
        'effect_size': effect_size,
        'alpha': alpha,
        'power': power,
        'is_sufficient': is_sufficient,
        'status_message': status_message,
        'warning_flag': None if is_sufficient else status_message
    }
    
    logger.info(f"Power analysis complete: power={power:.3f}, sufficient={is_sufficient}")
    
    return result

def main():
    """Main entry point for power analysis script."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Run power analysis on plasma confinement data')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file path')
    parser.add_argument('--effect-size', type=float, default=0.5, help='Expected effect size (correlation)')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--power-threshold', type=float, default=0.20, help='Minimum acceptable power')
    
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    logger.info(f"Running power analysis")
    results = run_power_analysis(
        df,
        effect_size=args.effect_size,
        alpha=args.alpha,
        power_threshold=args.power_threshold
    )
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Power analysis results saved to {output_path}")
    
    # Print summary
    print(f"Power Analysis Summary:")
    print(f"  Sample size (n): {results['n']}")
    print(f"  Effect size (r): {results['effect_size']}")
    print(f"  Alpha: {results['alpha']}")
    print(f"  Power: {results['power']:.3f}")
    print(f"  Status: {results['status_message']}")

if __name__ == '__main__':
    main()
