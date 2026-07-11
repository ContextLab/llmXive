"""
Task T034: Theory Comparison via Monte Carlo Simulation

Performs a Monte Carlo simulation to compare the measured slope distribution
against theoretical distributions (Photoevaporation and Core-Powered Mass Loss).
Calculates overlap area and p-values with Bonferroni correction.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Tuple, List, Any

import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from theory.scaling_laws import load_theoretical_laws, TheoreticalDistribution
from utils.logging_config import get_logger, setup_logging
from utils.config import load_config

# Constants
BONFERRONI_ALPHA = 0.025  # 0.05 / 2 tests
N_MC_SAMPLES = 50000      # Number of Monte Carlo samples

logger = get_logger(__name__)


def load_regression_results() -> Tuple[float, float]:
    """
    Loads the measured slope and its standard error from the regression output.
    Expects data/processed/regression_results.csv with columns: slope, slope_stderr.
    """
    results_path = project_root / "data" / "processed" / "regression_results.csv"
    
    if not results_path.exists():
        raise FileNotFoundError(f"Regression results file not found at {results_path}. "
                                "Ensure T032 has been executed successfully.")
    
    df = pd.read_csv(results_path)
    
    if 'slope' not in df.columns or 'slope_stderr' not in df.columns:
        raise ValueError(f"Regression results file missing required columns. "
                         f"Found: {df.columns.tolist()}")
    
    # Assuming single row summary or taking the mean if multiple
    slope = df['slope'].mean()
    slope_stderr = df['slope_stderr'].mean()
    
    logger.info(f"Loaded measured slope: {slope:.4f} +/- {slope_stderr:.4f}")
    return slope, slope_stderr


def load_theoretical_distributions() -> Dict[str, TheoreticalDistribution]:
    """
    Loads theoretical distributions from config.
    """
    return load_theoretical_laws()


def calculate_overlap_area(dist1_mean: float, dist1_std: float,
                           dist2_mean: float, dist2_std: float) -> float:
    """
    Calculates the area of overlap between two Gaussian distributions.
    Uses the formula involving the error function (erf).
    """
    # If standard deviations are zero, no overlap unless means are identical
    if dist1_std == 0 or dist2_std == 0:
        return 0.0 if abs(dist1_mean - dist2_mean) > 1e-9 else 1.0

    # Calculate the intersection point(s)
    # For two Gaussians, there are generally two intersection points, but for overlap area,
    # we integrate the minimum of the two PDFs.
    # A common approximation for overlap coefficient (OVL) is:
    # OVL = 2 * Phi( - |mu1 - mu2| / sqrt(sigma1^2 + sigma2^2) )
    # where Phi is the CDF of the standard normal distribution.
    # This formula is exact for the overlap of two normal distributions.
    
    sigma_diff = np.sqrt(dist1_std**2 + dist2_std**2)
    z = abs(dist1_mean - dist2_mean) / sigma_diff
    
    # Overlap area is 2 * Phi(-z) = 2 * (1 - Phi(z)) = 2 * (0.5 - 0.5 * erf(z/sqrt(2)))
    # Actually, Phi(-z) = 0.5 * (1 - erf(z/sqrt(2)))
    # So 2 * Phi(-z) = 1 - erf(z/sqrt(2))
    
    overlap = 1.0 - stats.norm.cdf(z) + stats.norm.cdf(-z) # This is 2 * Phi(-z)
    # Simplified: 2 * (1 - stats.norm.cdf(z))
    overlap = 2 * (1 - stats.norm.cdf(z))
    
    return max(0.0, min(1.0, overlap))


def perform_monte_carlo_comparison(
    measured_slope: float, 
    measured_slope_err: float,
    theoretical_dists: Dict[str, TheoreticalDistribution],
    n_samples: int = N_MC_SAMPLES
) -> Dict[str, Any]:
    """
    Performs Monte Carlo simulation to compare measured slope against theories.
    
    Returns a dictionary containing overlap areas and p-values for each theory.
    """
    logger.info(f"Starting Monte Carlo simulation with {n_samples} samples...")
    
    # 1. Sample from the measured distribution (Measurement uncertainty)
    # We assume the measured slope follows a Gaussian distribution centered at the
    # measured value with the measured standard error.
    measured_samples = np.random.normal(
        loc=measured_slope, 
        scale=measured_slope_err, 
        size=n_samples
    )
    
    results = {}
    
    for theory_name, theory_dist in theoretical_dists.items():
        # 2. Sample from the theoretical distribution (Theory uncertainty)
        # theory_dist is a Gaussian distribution representing the theory's prediction
        theory_samples = np.random.normal(
            loc=theory_dist.mean, 
            scale=theory_dist.std, 
            size=n_samples
        )
        
        # 3. Calculate p-value
        # We test if the measured slope is significantly different from the theory.
        # Since we are comparing two distributions, we can use the difference distribution.
        # Or simpler: Count how often the theoretical sample is "more extreme" than the measured sample?
        # Standard approach for "consistency": 
        # p-value = P(|Measured - Theory| > |Observed Difference|) under the null hypothesis?
        # Actually, the task asks for "overlap area and p-value".
        # Let's compute the p-value for the hypothesis: "The measured slope comes from the theoretical distribution".
        # Since both have uncertainties, we look at the difference distribution:
        # Diff ~ N(mu_meas - mu_theory, sqrt(se_meas^2 + se_theory^2))
        # We check if 0 is within the confidence interval of the difference.
        
        # Alternative interpretation for p-value in this context:
        # Probability that a random draw from Theory is <= a random draw from Measured (or vice versa)
        # But standard scientific reporting usually wants a p-value for the difference being non-zero.
        # Let's calculate the z-score of the difference between means, accounting for both uncertainties.
        
        diff_mean = measured_slope - theory_dist.mean
        diff_std = np.sqrt(measured_slope_err**2 + theory_dist.std**2)
        
        if diff_std == 0:
            p_val = 1.0 if diff_mean == 0 else 0.0
        else:
            z_score = diff_mean / diff_std
            # Two-tailed p-value
            p_val = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # 4. Calculate Overlap Area
        overlap = calculate_overlap_area(
            measured_slope, measured_slope_err,
            theory_dist.mean, theory_dist.std
        )
        
        # 5. Determine Consistency (Bonferroni corrected)
        is_consistent = p_val > BONFERRONI_ALPHA
        
        results[theory_name] = {
            "theoretical_mean": theory_dist.mean,
            "theoretical_std": theory_dist.std,
            "measured_mean": measured_slope,
            "measured_std": measured_slope_err,
            "overlap_area": float(overlap),
            "p_value": float(p_val),
            "is_consistent": bool(is_consistent),
            "threshold": BONFERRONI_ALPHA
        }
        
        logger.info(f"Theory '{theory_name}': Overlap={overlap:.4f}, p-value={p_val:.4f}, Consistent={is_consistent}")
    
    return results


def save_results(results: Dict[str, Any], output_path: str):
    """Saves the comparison results to a JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")


def main():
    """Main entry point for T034."""
    # Setup logging
    setup_logging(level=logging.INFO)
    
    try:
        # 1. Load Data
        logger.info("Loading regression results...")
        measured_slope, measured_slope_err = load_regression_results()
        
        logger.info("Loading theoretical distributions...")
        theoretical_dists = load_theoretical_distributions()
        
        if not theoretical_dists:
            raise ValueError("No theoretical distributions loaded. Check config.yaml.")
        
        # 2. Perform Monte Carlo Comparison
        comparison_results = perform_monte_carlo_comparison(
            measured_slope, 
            measured_slope_err, 
            theoretical_dists
        )
        
        # 3. Save Results
        output_path = project_root / "data" / "processed" / "theory_comparison.json"
        save_results(comparison_results, output_path)
        
        # 4. Print Summary
        print("\n" + "="*60)
        print("THEORY COMPARISON SUMMARY (Bonferroni Corrected Alpha = 0.025)")
        print("="*60)
        print(f"Measured Slope: {measured_slope:.4f} +/- {measured_slope_err:.4f}")
        print("-"*60)
        print(f"{'Theory':<25} {'Overlap':<10} {'P-Value':<10} {'Consistent':<10}")
        print("-"*60)
        
        for name, res in comparison_results.items():
            print(f"{name:<25} {res['overlap_area']:<10.4f} {res['p_value']:<10.4f} {str(res['is_consistent']):<10}")
        
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during theory comparison: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())