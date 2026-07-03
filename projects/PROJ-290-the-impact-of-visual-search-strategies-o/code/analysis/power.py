import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
from scipy.stats import nct, t, norm

from utils.logging import get_logger
from config import get_config

# Ensure logger is available
try:
    logger = get_logger(__name__)
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


def calculate_effect_size_d(mean_diff: float, std_dev: float) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        mean_diff: Difference between means
        std_dev: Pooled standard deviation
        
    Returns:
        Cohen's d value
    """
    if std_dev == 0:
        logger.warning("Standard deviation is zero, returning 0 for effect size.")
        return 0.0
    return mean_diff / std_dev


def calculate_power_from_d(
    d: float,
    n_per_group: int,
    alpha: float = 0.05,
    two_tailed: bool = True
) -> float:
    """
    Calculate statistical power for a two-sample t-test given effect size d.
    
    Uses the non-central t-distribution approximation.
    
    Args:
        d: Cohen's d effect size
        n_per_group: Sample size per group
        alpha: Significance level
        two_tailed: Whether the test is two-tailed
        
    Returns:
        Statistical power (probability of rejecting null when alternative is true)
    """
    if d == 0:
        return alpha if two_tailed else alpha / 2
    
    df = 2 * n_per_group - 2
    # Non-centrality parameter
    ncp = d * np.sqrt(n_per_group / 2)
    
    # Critical t-value
    if two_tailed:
        t_crit = t.ppf(1 - alpha/2, df)
    else:
        t_crit = t.ppf(1 - alpha, df)
    
    # Power is the probability that the t-statistic exceeds the critical value
    # under the non-central t-distribution
    if two_tailed:
        # For two-tailed, we sum the probabilities in both tails
        # Power = P(T > t_crit | ncp) + P(T < -t_crit | ncp)
        power_upper = 1 - nct.cdf(t_crit, df, ncp)
        power_lower = nct.cdf(-t_crit, df, ncp)
        power = power_upper + power_lower
    else:
        power = 1 - nct.cdf(t_crit, df, ncp)
        
    return max(0.0, min(1.0, power))


def find_sample_size_for_power(
    target_power: float,
    d: float,
    alpha: float = 0.05,
    two_tailed: bool = True,
    max_n: int = 10000,
    min_n: int = 2
) -> Tuple[int, float]:
    """
    Find the minimum sample size per group needed to achieve target power.
    
    Uses a binary search approach for efficiency.
    
    Args:
        target_power: Desired statistical power (e.g., 0.80)
        d: Expected effect size (Cohen's d)
        alpha: Significance level
        two_tailed: Whether the test is two-tailed
        max_n: Maximum sample size to search
        min_n: Minimum sample size to search
        
    Returns:
        Tuple of (required_sample_size, achieved_power)
    """
    if d == 0:
        logger.warning("Effect size is zero; power cannot be increased beyond alpha.")
        return (max_n, alpha if two_tailed else alpha / 2)
        
    low = min_n
    high = max_n
    best_n = max_n
    best_power = 0.0
    
    while low <= high:
        mid = (low + high) // 2
        power = calculate_power_from_d(d, mid, alpha, two_tailed)
        
        if power >= target_power:
            best_n = mid
            best_power = power
            high = mid - 1
        else:
            low = mid + 1
            
    return best_n, best_power


def run_a_priori_power_analysis(
    effect_size_d: float = 0.5,
    target_power: float = 0.80,
    alpha: float = 0.05,
    two_tailed: bool = True,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run a priori power analysis to determine required sample size.
    
    Args:
        effect_size_d: Expected effect size (Cohen's d)
        target_power: Target statistical power
        alpha: Significance level
        two_tailed: Whether the test is two-tailed
        output_path: Path to save results JSON file
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Running a priori power analysis:")
    logger.info(f"  Effect size (d): {effect_size_d}")
    logger.info(f"  Target power: {target_power}")
    logger.info(f"  Alpha: {alpha}")
    logger.info(f"  Two-tailed: {two_tailed}")
    
    required_n, achieved_power = find_sample_size_for_power(
        target_power=target_power,
        d=effect_size_d,
        alpha=alpha,
        two_tailed=two_tailed
    )
    
    results = {
        "analysis_type": "a_priori_power_analysis",
        "parameters": {
            "effect_size_d": effect_size_d,
            "target_power": target_power,
            "alpha": alpha,
            "two_tailed": two_tailed
        },
        "results": {
            "required_sample_size_per_group": required_n,
            "total_required_sample_size": required_n * 2,
            "achieved_power_at_required_n": achieved_power
        },
        "interpretation": {
            "status": "success" if achieved_power >= target_power else "warning",
            "message": (
                f"To detect an effect size of d={effect_size_d} with {target_power*100:.0f}% "
                f"power at alpha={alpha} ({'two-tailed' if two_tailed else 'one-tailed'}), "
                f"a sample size of {required_n} participants per group (total N={required_n*2}) is required."
            )
        }
    }
    
    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Power analysis results saved to: {output_path}")
    
    return results


def main():
    """Main entry point for power analysis script."""
    config = get_config()
    output_path = config.get("paths", {}).get("power_analysis_output", "results/power_analysis.json")
    output_path = Path(output_path)
    
    # Default parameters from task specification
    effect_size_d = 0.5
    target_power = 0.80
    alpha = 0.05
    two_tailed = True
    
    results = run_a_priori_power_analysis(
        effect_size_d=effect_size_d,
        target_power=target_power,
        alpha=alpha,
        two_tailed=two_tailed,
        output_path=output_path
    )
    
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    main()