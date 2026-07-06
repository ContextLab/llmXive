"""
Post-hoc power analysis for the correlation study.

Calculates the detectable effect size (rho) for a given sample size (N=50),
significance level (alpha=0.05), and desired power (0.80) using the
non-central t-distribution approximation for Pearson/Spearman correlation.

This module implements FR-009 and SC-001.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any

import numpy as np
from scipy import stats
from scipy.optimize import brentq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_N = 50
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_TAILS = 2  # Two-tailed test

def calculate_effect_size_for_power(
    n: int,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    tails: int = DEFAULT_TAILS
) -> float:
    """
    Calculate the minimum detectable effect size (rho) for a given sample size,
    power, and alpha level using the Fisher z-transformation approximation.

    This function solves for rho such that the power of the test equals the
    target power.

    Args:
        n: Sample size (number of subjects).
        power: Desired statistical power (default 0.80).
        alpha: Significance level (default 0.05).
        tails: Number of tails (1 or 2).

    Returns:
        The detectable correlation coefficient (rho).
    """
    if n < 3:
        raise ValueError("Sample size must be at least 3 for correlation power analysis.")
    if not 0 < power < 1:
        raise ValueError("Power must be between 0 and 1.")
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1.")

    # Degrees of freedom
    df = n - 2

    # Critical t-value for the given alpha and tails
    if tails == 2:
        t_crit = stats.t.ppf(1 - alpha / 2, df)
    else:
        t_crit = stats.t.ppf(1 - alpha, df)

    # Non-centrality parameter (ncp) required to achieve the target power
    # We need to find ncp such that P(T > t_crit | ncp) = power
    # This requires numerical inversion of the non-central t-distribution CDF

    def power_function(ncp):
        if tails == 2:
            # Two-tailed: power = P(T < -t_crit) + P(T > t_crit)
            cdf_low = stats.nct.cdf(-t_crit, df, ncp)
            cdf_high = 1 - stats.nct.cdf(t_crit, df, ncp)
            return cdf_low + cdf_high
        else:
            # One-tailed
            return 1 - stats.nct.cdf(t_crit, df, ncp)

    # Find ncp that gives the desired power
    # The ncp must be positive for a positive effect size
    # We search in a reasonable range [0.1, 20]
    try:
        ncp_target = brentq(lambda x: power_function(x) - power, 0.1, 20.0)
    except ValueError:
        # If we can't find it in the range, try a wider one or return a fallback
        logger.warning("Could not find ncp in [0.1, 20], trying wider range...")
        try:
            ncp_target = brentq(lambda x: power_function(x) - power, 0.01, 50.0)
        except ValueError:
            logger.error("Could not find ncp for target power. Returning NaN.")
            return np.nan

    # Convert ncp to correlation coefficient (rho)
    # ncp = rho * sqrt((n-2) / (1 - rho^2))
    # Solving for rho: rho = ncp / sqrt(ncp^2 + df)
    rho = ncp_target / np.sqrt(ncp_target**2 + df)

    return rho

def run_post_hoc_power_analysis(
    n: int = DEFAULT_N,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    tails: int = DEFAULT_TAILS
) -> Dict[str, Any]:
    """
    Run a full post-hoc power analysis and return results as a dictionary.

    Args:
        n: Sample size.
        power: Desired power.
        alpha: Significance level.
        tails: Number of tails.

    Returns:
        Dictionary containing analysis parameters and results.
    """
    logger.info(f"Running post-hoc power analysis: N={n}, Power={power}, Alpha={alpha}")

    rho_detectable = calculate_effect_size_for_power(n, power, alpha, tails)

    results = {
        "analysis_type": "post-hoc_power_analysis",
        "parameters": {
            "sample_size": n,
            "desired_power": power,
            "significance_level": alpha,
            "tails": tails
        },
        "results": {
            "detectable_effect_size_rho": float(rho_detectable),
            "interpretation": f"With N={n}, we have {power*100:.0f}% power to detect a correlation of |rho| >= {rho_detectable:.3f} at alpha={alpha}."
        }
    }

    # Additional context for the specific study
    results["context"] = {
        "study": "Dream Recall Frequency vs Brain Network Dynamics",
        "note": "This analysis assumes a two-tailed Spearman correlation test.",
        "threshold_explanation": "Effect sizes below this value may not be reliably detected with the current sample size."
    }

    return results

def save_power_analysis_results(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save the power analysis results to a JSON file.

    Args:
        results: Dictionary of results from run_post_hoc_power_analysis.
        output_path: Path to the output JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Power analysis results saved to {output_path}")

def main():
    """
    Main entry point for the power analysis script.

    Reads configuration from the project's config if available,
    or uses defaults. Outputs results to results/power_analysis.json.
    """
    # Default paths
    config = {}
    try:
        from utils.config import get_config_summary
        config = get_config_summary()
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using defaults.")

    # Determine sample size
    # The task specifies N=50 explicitly.
    n_subjects = DEFAULT_N
    if 'sample_size' in config:
        n_subjects = config['sample_size']
        logger.info(f"Using sample size from config: {n_subjects}")

    # Run analysis
    results = run_post_hoc_power_analysis(n=n_subjects)

    # Define output path
    # Following the project convention: results/
    output_path = "results/power_analysis.json"
    
    # If results directory doesn't exist, create it
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    save_power_analysis_results(results, output_path)

    # Print summary to stdout
    print(f"\n--- Post-Hoc Power Analysis Summary ---")
    print(f"Sample Size (N): {results['parameters']['sample_size']}")
    print(f"Target Power: {results['parameters']['desired_power']}")
    print(f"Alpha Level: {results['parameters']['significance_level']}")
    print(f"Detectable Effect Size (rho): {results['results']['detectable_effect_size_rho']:.4f}")
    print(f"Interpretation: {results['results']['interpretation']}")
    print(f"Results saved to: {output_path}")
    print("-----------------------------------------\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())