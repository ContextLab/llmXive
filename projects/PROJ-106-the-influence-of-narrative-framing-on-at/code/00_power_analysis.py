"""
Prospective Power Analysis for Narrative Framing Study.

This script calculates the required sample size (N) for an independent-samples
t-test to achieve 80% power at a medium effect size (Cohen's d = 0.4)
with a significance level (alpha) of 0.05.

It enforces the recruitment target of N=300 as per FR-009 and SC-002.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

import numpy as np
from scipy import stats
from scipy.stats import ttest_ind

# Add project root to path for imports if running as script
# but rely on standard import for module usage
try:
    from utils.logger import setup_logger, log_script_start, log_script_end, info, warning, error
    from utils.random_utils import set_global_seed
except ImportError:
    # Fallback for direct execution without proper path setup during dev
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_script_start(*args, **kwargs): pass
    def log_script_end(*args, **kwargs): pass
    def info(msg): logging.info(msg)
    def warning(msg): logging.warning(msg)
    def error(msg): logging.error(msg)
    
    def set_global_seed(seed): 
        np.random.seed(seed)
        import random
        random.seed(seed)

def calculate_required_n(effect_size: float = 0.4, alpha: float = 0.05, power: float = 0.80) -> int:
    """
    Calculates the required sample size per group for an independent t-test.
    
    Uses the normal approximation for power calculation:
    n = 2 * ((Z_{1-alpha/2} + Z_{1-beta}) / d)^2
    
    Parameters:
    -----------
    effect_size : float
        Expected Cohen's d.
    alpha : float
        Significance level.
    power : float
        Desired statistical power (1 - beta).
        
    Returns:
    --------
    int
        Required sample size per group.
    """
    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Formula for two-sample t-test (equal variance, equal n)
    # n per group
    n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    
    return int(np.ceil(n_per_group))

def calculate_power(n_per_group: int, effect_size: float, alpha: float = 0.05) -> float:
    """
    Calculates the achieved power given a sample size and effect size.
    """
    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n_per_group / 2)
    
    # Critical t-value (approximated with normal for large N, or exact t)
    # For power calculation, we often use the non-central t-distribution
    # scipy.stats.nct is the non-central t
    df = 2 * n_per_group - 2
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Power is the probability that the t-statistic exceeds the critical value
    # under the alternative hypothesis (non-central t)
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    return power

def run_power_analysis(effect_size: float = 0.4, alpha: float = 0.05, target_power: float = 0.80) -> Dict[str, Any]:
    """
    Runs the full prospective power analysis.
    """
    n_per_group = calculate_required_n(effect_size, alpha, target_power)
    total_n = n_per_group * 2
    
    # Verify power with calculated N
    actual_power = calculate_power(n_per_group, effect_size, alpha)
    
    # Enforce FR-009: N=300 target for recruitment planning
    # The spec says "enforce the N=300 target". 
    # If calculated N is less than 300, we still recommend 300 to ensure robustness
    # and account for dropouts/manipulation check failures.
    recommended_n = max(total_n, 300)
    recommended_per_group = recommended_n // 2
    
    # Recalculate power for the enforced target
    enforced_power = calculate_power(recommended_per_group, effect_size, alpha)
    
    return {
        "parameters": {
            "effect_size": effect_size,
            "alpha": alpha,
            "target_power": target_power
        },
        "calculated_requirements": {
            "n_per_group": n_per_group,
            "total_n": total_n,
            "achieved_power": float(actual_power)
        },
        "enforced_target": {
            "reason": "FR-009 / SC-002: Minimum recruitment target of 300",
            "total_n": recommended_n,
            "n_per_group": recommended_per_group,
            "achieved_power_at_target": float(enforced_power)
        },
        "status": "success" if enforced_power >= target_power else "warning_low_power"
    }

def main():
    parser = argparse.ArgumentParser(description="Prospective Power Analysis for AI Narrative Framing Study")
    parser.add_argument("--output", type=str, default="data/processed/power_analysis.json",
                      help="Path to save the JSON report")
    parser.add_argument("--effect-size", type=float, default=0.4,
                      help="Expected Cohen's d effect size")
    parser.add_argument("--alpha", type=float, default=0.05,
                      help="Significance level")
    parser.add_argument("--power", type=float, default=0.80,
                      help="Target power")
    parser.add_argument("--seed", type=int, default=42,
                      help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Setup
    set_global_seed(args.seed)
    logger = setup_logger("power_analysis")
    log_script_start(logger, "code/00_power_analysis.py", vars(args))
    
    try:
        info(f"Running power analysis for effect_size={args.effect_size}, alpha={args.alpha}, power={args.power}")
        
        results = run_power_analysis(
            effect_size=args.effect_size,
            alpha=args.alpha,
            target_power=args.power
        )
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        info(f"Power analysis complete. Results saved to {output_path}")
        info(f"Required N per group (calculated): {results['calculated_requirements']['n_per_group']}")
        info(f"Recommended N total (enforced): {results['enforced_target']['total_n']}")
        info(f"Power at enforced target: {results['enforced_target']['achieved_power_at_target']:.4f}")
        
        log_script_end(logger, "code/00_power_analysis.py", status="success")
        
        # Return code 0 for success
        return 0
        
    except Exception as e:
        error(f"Power analysis failed: {e}")
        log_script_end(logger, "code/00_power_analysis.py", status="failed", exception=e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
