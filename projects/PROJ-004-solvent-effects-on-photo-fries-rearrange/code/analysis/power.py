"""
Unified Power Analysis for Solvent Effects on Photo-Fries Rearrangement.

This module performs a single unified power analysis covering both:
1. Kinetic extraction (US-2): Detectable effect sizes for lifetime estimates.
2. Correlation slope (US-3): Detectable effect sizes for the relationship between
   solvent polarity and lifetime.

It explicitly documents the study's limitations due to low N (n=3 replicates).
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import standard libraries for statistical estimation
import numpy as np
from scipy import stats

# Import project config for paths
try:
    from config import get_processed_data_path, ensure_directories
except ImportError:
    # Fallback for direct execution outside project root if needed, though
    # the agent prompt assumes project context.
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config import get_processed_data_path, ensure_directories

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
# Study constraint: n >= 3 replicates per solvent as per task description
MIN_REPLICATES = 3
NUM_SOLVENTS = 5  # Based on T006b population

class PowerAnalysisError(Exception):
    """Custom exception for power analysis failures."""
    pass

def calculate_effect_size(mean_diff: float, std_dev: float) -> float:
    """
    Calculate Cohen's d effect size.

    Args:
        mean_diff: The difference in means to detect.
        std_dev: The pooled standard deviation.

    Returns:
        Cohen's d value.
    """
    if std_dev == 0:
        return 0.0
    return mean_diff / std_dev

def estimate_mdes(
    n: int,
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER,
    std_dev: float = 1.0,
    two_sided: bool = True
) -> float:
    """
    Estimate the Minimum Detectable Effect Size (MDES) for a given sample size.

    Uses the t-test approximation for MDES:
    MDES = (t_alpha + t_beta) * std_dev * sqrt(2/n)

    Args:
        n: Sample size per group.
        alpha: Significance level.
        power: Desired statistical power (1 - beta).
        std_dev: Assumed standard deviation of the population.
        two_sided: Whether the test is two-sided.

    Returns:
        The minimum detectable difference in means (in units of std_dev).
    """
    df = 2 * n - 2
    t_alpha = stats.t.ppf(1 - alpha / 2, df) if two_sided else stats.t.ppf(1 - alpha, df)
    t_beta = stats.t.ppf(power, df)

    # Approximation for MDES in units of standard deviation
    mdes_factor = (t_alpha + t_beta) * np.sqrt(2 / n)
    return mdes_factor * std_dev

def calculate_post_hoc_power(
    n: int,
    effect_size: float,
    alpha: float = DEFAULT_ALPHA,
    two_sided: bool = True
) -> float:
    """
    Calculate post-hoc power given an observed effect size.

    Args:
        n: Sample size per group.
        effect_size: Observed Cohen's d.
        alpha: Significance level.
        two_sided: Whether the test is two-sided.

    Returns:
        Calculated statistical power (0.0 to 1.0).
    """
    df = 2 * n - 2
    t_alpha = stats.t.ppf(1 - alpha / 2, df) if two_sided else stats.t.ppf(1 - alpha, df)
    
    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n / 2)
    
    # Power is the probability that the t-statistic exceeds the critical value
    # under the non-central t-distribution
    # Using survival function (1 - CDF) for the right tail
    # Note: For two-sided, we approximate by checking the right tail probability
    # and adjusting, but for effect size > 0, the right tail dominates.
    # A more precise calculation integrates the non-central t-distribution.
    # Here we use a standard approximation:
    
    # Critical t value
    crit_t = t_alpha
    
    # Probability of exceeding critical t under alternative hypothesis
    # We use the non-central t CDF
    from scipy.stats import nct
    
    # For two-sided, we sum probabilities in both tails, but typically
    # power is dominated by the tail in the direction of the effect.
    # We calculate P(T > crit_t | ncp) + P(T < -crit_t | ncp)
    # Since effect_size is usually positive in this context (detecting increase),
    # we focus on the right tail, but for rigor:
    
    p_right = 1 - nct.cdf(crit_t, df, ncp)
    p_left = nct.cdf(-crit_t, df, ncp)
    
    return p_right + p_left

def analyze_kinetic_power(
    n_replicates: int = MIN_REPLICATES,
    assumed_std_dev: float = 0.15, # Estimated from pilot data or literature (ns scale)
    alpha: float = DEFAULT_ALPHA,
    power: float = DEFAULT_POWER
) -> Dict[str, Any]:
    """
    Analyze power for the kinetic extraction step (US-2).
    
    Determines the detectable lifetime difference given n_replicates.

    Args:
        n_replicates: Number of replicates per solvent condition.
        assumed_std_dev: Assumed standard deviation of lifetime measurements (ns).
        alpha: Significance level.
        power: Desired power.

    Returns:
        Dictionary with kinetic power analysis results.
    """
    logger.info(f"Analyzing kinetic power for n={n_replicates}, sigma={assumed_std_dev}")
    
    # Calculate MDES (Minimum Detectable Effect Size)
    mdes = estimate_mdes(
        n=n_replicates,
        alpha=alpha,
        power=power,
        std_dev=assumed_std_dev,
        two_sided=True
    )
    
    # Calculate power for a "medium" effect size (Cohen's d = 0.5)
    # to give a sense of sensitivity
    medium_effect_d = 0.5
    power_medium = calculate_post_hoc_power(
        n=n_replicates,
        effect_size=medium_effect_d,
        alpha=alpha,
        two_sided=True
    )
    
    return {
        "n_replicates": n_replicates,
        "assumed_std_dev_ns": assumed_std_dev,
        "alpha": alpha,
        "target_power": power,
        "mdes_ns": mdes,
        "power_for_medium_effect": power_medium,
        "interpretation": (
            f"With n={n_replicates} replicates, the study can detect a lifetime "
            f"difference of at least {mdes:.3f} ns (assuming sigma={assumed_std_dev} ns) "
            f"with {power*100:.0f}% power. "
            f"Power to detect a medium effect (d=0.5) is {power_medium:.2%}."
        )
    }

def analyze_correlation_power(
    n_solvents: int = NUM_SOLVENTS,
    n_replicates: int = MIN_REPLICATES,
    assumed_r: float = 0.6, # Assumed correlation coefficient
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Analyze power for the correlation step (US-3).
    
    Determines the detectable correlation coefficient given N data points.
    Total N = n_solvents * n_replicates (if analyzing pooled) or n_solvents (if analyzing means).
    We assume analysis is done on the means per solvent to avoid pseudoreplication,
    so effective N = n_solvents.

    Args:
        n_solvents: Number of distinct solvent conditions.
        n_replicates: Number of replicates (used to justify mean stability, but N for correlation is n_solvents).
        assumed_r: Assumed population correlation coefficient.
        alpha: Significance level.

    Returns:
        Dictionary with correlation power analysis results.
    """
    logger.info(f"Analyzing correlation power for n_solvents={n_solvents}")
    
    # Effective sample size for correlation is the number of independent groups (solvents)
    # if we correlate mean lifetime vs mean polarity.
    # N = n_solvents
    N = n_solvents
    
    # Calculate critical r for significance
    df = N - 2
    t_crit = stats.t.ppf(1 - alpha/2, df)
    r_crit = t_crit / np.sqrt(t_crit**2 + df)
    
    # Calculate power to detect assumed_r
    # Non-centrality parameter for correlation test
    ncp = assumed_r * np.sqrt((N - 2) / (1 - assumed_r**2))
    
    # Power is probability that t-stat > t_crit under alternative
    # t = r * sqrt((N-2)/(1-r^2)) ~ non-central t with ncp
    # We approximate using the non-central t distribution
    from scipy.stats import nct
    
    # The test statistic under H1 follows a non-central t distribution
    # We need P(|T| > t_crit)
    # Since assumed_r is positive, we look at the right tail
    # But for two-sided, we sum both tails.
    # However, the distribution is shifted by ncp.
    
    # Approximation: Power = 1 - beta
    # Using the non-central t CDF
    p_right = 1 - nct.cdf(t_crit, df, ncp)
    p_left = nct.cdf(-t_crit, df, ncp)
    power_val = p_right + p_left
    
    # Calculate MDES for correlation (minimum detectable r)
    # We search for r such that power is 0.80
    # This is iterative, but we can approximate or list a few values
    # For N=5, power is generally very low for moderate effects.
    
    return {
        "n_solvents": n_solvents,
        "n_replicates_per_solvent": n_replicates,
        "effective_N": N,
        "alpha": alpha,
        "assumed_correlation": assumed_r,
        "critical_r": r_crit,
        "power_to_detect_assumed_r": power_val,
        "interpretation": (
            f"With N={N} independent solvent conditions, the study has {power_val:.1%} "
            f"power to detect a correlation of r={assumed_r}. "
            f"The critical r for significance (p<{alpha}) is {r_crit:.3f}. "
            f"Note: Low N ({N}) severely limits the ability to detect moderate correlations."
        )
    }

def write_power_report(
    kinetic_results: Dict[str, Any],
    correlation_results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write the unified power analysis report to a JSON file.

    Args:
        kinetic_results: Results from analyze_kinetic_power.
        correlation_results: Results from analyze_correlation_power.
        output_path: Path to the output JSON file.
    """
    report = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "task_id": "T059",
            "description": "Unified Power Analysis for US-2 and US-3",
            "constraints": {
                "min_replicates": MIN_REPLICATES,
                "num_solvents": NUM_SOLVENTS,
                "limitation": "Low N (n=3 replicates, 5 solvents) limits statistical power."
            }
        },
        "kinetic_analysis": kinetic_results,
        "correlation_analysis": correlation_results,
        "unified_conclusion": (
            f"This study is designed with n={MIN_REPLICATES} replicates per solvent "
            f"and {NUM_SOLVENTS} solvent conditions. "
            f"Kinetic analysis can detect lifetime differences of ~{kinetic_results['mdes_ns']:.3f} ns. "
            f"Correlation analysis has limited power ({correlation_results['power_to_detect_assumed_r']:.1%}) "
            f"to detect moderate correlations due to the small number of independent solvent conditions (N={NUM_SOLVENTS}). "
            f"Results should be interpreted as exploratory with appropriate caution regarding effect sizes."
        )
    }
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Power analysis report written to {output_path}")

def main():
    """Main entry point for the power analysis script."""
    parser = argparse.ArgumentParser(
        description="Perform unified power analysis for the Photo-Fries study."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output JSON file. Defaults to data/processed/study_power_analysis.json"
    )
    parser.add_argument(
        "--n-replicates",
        type=int,
        default=MIN_REPLICATES,
        help=f"Number of replicates per solvent (default: {MIN_REPLICATES})"
    )
    parser.add_argument(
        "--n-solvents",
        type=int,
        default=NUM_SOLVENTS,
        help=f"Number of solvent conditions (default: {NUM_SOLVENTS})"
    )
    parser.add_argument(
        "--std-dev-ns",
        type=float,
        default=0.15,
        help="Assumed standard deviation for kinetic measurements in ns (default: 0.15)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        processed_dir = get_processed_data_path()
        ensure_directories()
        output_path = processed_dir / "study_power_analysis.json"
    
    try:
        # Perform Kinetic Power Analysis
        kinetic_results = analyze_kinetic_power(
            n_replicates=args.n_replicates,
            assumed_std_dev=args.std_dev_ns
        )
        
        # Perform Correlation Power Analysis
        correlation_results = analyze_correlation_power(
            n_solvents=args.n_solvents,
            n_replicates=args.n_replicates
        )
        
        # Write Report
        write_power_report(kinetic_results, correlation_results, output_path)
        
        print(f"Power analysis complete. Report saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
