"""
Post-hoc Power Analysis for Dream Recall Frequency Study.

This module calculates the detectable effect size (Cohen's d) for the
given sample size (N=50) and statistical power parameters. It performs
a post-hoc power analysis based on the observed correlation coefficients
from the main statistical analysis.

Requirements:
- FR-009: Calculate and report post-hoc power analysis.
- SC-001: Ensure sufficient power for N=50.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.config import get_config

logger = logging.getLogger(__name__)

def calculate_detectable_effect_size(n: int, alpha: float = 0.05, power: float = 0.80) -> float:
    """
    Calculate the minimum detectable effect size (Cohen's d) for a given sample size.

    This uses the relationship between sample size, power, alpha, and effect size
    for a two-tailed test.

    Args:
        n: Sample size (number of subjects)
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)

    Returns:
        float: The minimum detectable Cohen's d effect size
    """
    # Using the approximation for two-sample t-test or correlation
    # For correlation, we can use the transformation:
    # d = 2 * r / sqrt(1 - r^2)
    # But for direct power analysis on correlation, we use:
    # n = (Z_alpha + Z_beta)^2 / (r^2) approximately for large n
    # More precisely, using Fisher's z-transformation:
    # SE_z = 1 / sqrt(n - 3)
    # Z_alpha = norm.ppf(1 - alpha/2)
    # Z_beta = norm.ppf(power)
    # r_detectable = tanh(Z_alpha * SE_z + Z_beta * SE_z)

    # Standard normal quantiles
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    # Standard error of Fisher's z
    se_z = 1.0 / np.sqrt(n - 3)

    # Minimum detectable z (Fisher transformed correlation)
    z_detectable = z_alpha * se_z + z_beta * se_z

    # Convert back to correlation coefficient
    r_detectable = np.tanh(z_detectable)

    # Convert correlation to Cohen's d for reporting
    # d = 2 * r / sqrt(1 - r^2)
    if abs(r_detectable) >= 1.0:
        # Edge case: if r is 1, d is infinite
        return float('inf')
    
    d_detectable = 2 * r_detectable / np.sqrt(1 - r_detectable ** 2)

    return d_detectable

def calculate_post_hoc_power(r_observed: float, n: int, alpha: float = 0.05) -> float:
    """
    Calculate the achieved statistical power for an observed effect size.

    Args:
        r_observed: Observed Pearson/Spearman correlation coefficient
        n: Sample size
        alpha: Significance level

    Returns:
        float: Statistical power (0 to 1)
    """
    if abs(r_observed) >= 1.0:
        return 1.0

    # Fisher's z-transformation
    z_observed = np.arctanh(r_observed)
    se_z = 1.0 / np.sqrt(n - 3)

    # Critical z value for significance
    z_critical = stats.norm.ppf(1 - alpha / 2)

    # Power is the probability of rejecting H0 when the true effect is z_observed
    # Power = P(|Z| > z_critical | true effect = z_observed)
    #       = P(Z > z_critical - z_observed/se) + P(Z < -z_critical - z_observed/se)
    
    # For two-tailed test
    z_power = z_observed / se_z
    power = stats.norm.cdf(z_power - z_critical) + stats.norm.cdf(-z_power - z_critical)

    return max(0.0, min(1.0, power))

def load_results_stats(results_path: Path) -> Dict[str, Any]:
    """
    Load the statistical results from the main analysis.

    Args:
        results_path: Path to results/stats.json

    Returns:
        Dict containing correlation results
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def run_power_analysis(
    n_subjects: int = 50,
    alpha: float = 0.05,
    target_power: float = 0.80,
    results_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the complete post-hoc power analysis.

    Args:
        n_subjects: Number of subjects in the study (default 50)
        alpha: Significance level (default 0.05)
        target_power: Target statistical power for detectable effect calculation (default 0.80)
        results_path: Optional path to results/stats.json to include observed effects
        output_path: Optional path to write results to JSON

    Returns:
        Dict containing power analysis results
    """
    config = get_config()
    if output_path is None:
        output_path = Path(config['paths']['results']) / 'power_analysis.json'
    
    if results_path is None:
        results_path = Path(config['paths']['results']) / 'stats.json'

    # Calculate detectable effect size for the given N
    detectable_d = calculate_detectable_effect_size(n_subjects, alpha, target_power)
    detectable_r = detectable_d / np.sqrt(4 + detectable_d ** 2) if detectable_d != float('inf') else 1.0

    results = {
        "study_parameters": {
            "n_subjects": n_subjects,
            "alpha": alpha,
            "target_power": target_power
        },
        "detectable_effect": {
            "cohen_d": detectable_d,
            "correlation_r": detectable_r,
            "interpretation": "Minimum effect size detectable with 80% power at N=50"
        },
        "power_thresholds": {
            "small_effect_r": 0.1,
            "medium_effect_r": 0.3,
            "large_effect_r": 0.5,
            "note": "Cohen's conventions for correlation effect sizes"
        }
    }

    # If we have observed results, calculate achieved power
    if results_path.exists():
        try:
            stats_data = load_results_stats(results_path)
            observed_powers = []
            
            # Handle both single result and per-network results
            metrics_to_analyze = []
            if 'network_correlations' in stats_data:
                metrics_to_analyze = stats_data['network_correlations']
            elif 'correlations' in stats_data:
                # Single correlation case
                metrics_to_analyze = [stats_data['correlations']]
            
            for metric in metrics_to_analyze:
                if 'rho' in metric and 'network' in metric:
                    r_obs = metric['rho']
                    power = calculate_post_hoc_power(r_obs, n_subjects, alpha)
                    observed_powers.append({
                        "network": metric['network'],
                        "observed_rho": r_obs,
                        "achieved_power": power,
                        "significant": metric.get('fdr_corrected_p', metric.get('p', 1.0)) < alpha
                    })
            
            results["observed_power_analysis"] = {
                "subjects_analyzed": n_subjects,
                "networks": observed_powers,
                "summary": {
                    "average_power": np.mean([p["achieved_power"] for p in observed_powers]) if observed_powers else 0.0,
                    "min_power": min([p["achieved_power"] for p in observed_powers]) if observed_powers else 0.0,
                    "max_power": max([p["achieved_power"] for p in observed_powers]) if observed_powers else 0.0
                }
            }
        except (KeyError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load observed statistics for power analysis: {e}")
            results["observed_power_analysis"] = {
                "status": "skipped",
                "reason": "Could not load results/stats.json"
            }
    else:
        results["observed_power_analysis"] = {
            "status": "skipped",
            "reason": f"Results file not found: {results_path}"
        }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Power analysis results written to {output_path}")
    logger.info(f"Detectable effect size (Cohen's d) for N={n_subjects}: {detectable_d:.3f}")
    logger.info(f"Detectable correlation (r) for N={n_subjects}: {detectable_r:.3f}")

    return results

def main():
    """Main entry point for power analysis script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting post-hoc power analysis for Dream Recall Frequency study")

    try:
        results = run_power_analysis(
            n_subjects=50,  # As per FR-009 and SC-001
            alpha=0.05,
            target_power=0.80
        )

        print("\n=== Power Analysis Summary ===")
        print(f"Sample Size (N): {results['study_parameters']['n_subjects']}")
        print(f"Detectable Cohen's d: {results['detectable_effect']['cohen_d']:.3f}")
        print(f"Detectable correlation (r): {results['detectable_effect']['correlation_r']:.3f}")
        
        if "observed_power_analysis" in results and results["observed_power_analysis"].get("status") != "skipped":
            summary = results["observed_power_analysis"]["summary"]
            print(f"\nObserved Power Statistics:")
            print(f"  Average Power: {summary['average_power']:.3f}")
            print(f"  Min Power: {summary['min_power']:.3f}")
            print(f"  Max Power: {summary['max_power']:.3f}")
        
        print(f"\nResults saved to: {Path(results['study_parameters'].get('output_path', 'results/power_analysis.json'))}")
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
