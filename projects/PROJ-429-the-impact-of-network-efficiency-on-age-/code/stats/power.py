"""
Power Analysis Module for EEG Network Efficiency Study.

Implements Monte Carlo power simulation to verify minimum power >= 0.80
for a target effect size of r=0.3 (Spearman correlation).

Requirements:
- 1000 iterations
- seed=42
- Simulate datasets with effect size r=0.3
- Calculate proportion of significant results (power)
"""

import json
import logging
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import ensure_dirs, get_config_summary
from stats.correction import fdr_correction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_correlation_data(n: int, rho: float, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate bivariate normal data with a specific correlation coefficient.
    
    Args:
        n: Sample size
        rho: Target correlation coefficient
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (x, y) arrays
    """
    np.random.seed(seed)
    mean = [0, 0]
    cov = [[1, rho], [rho, 1]]
    data = np.random.multivariate_normal(mean, cov, size=n)
    return data[:, 0], data[:, 1]

def calculate_spearman_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate Spearman rank correlation coefficient.
    
    Args:
        x: First array
        y: Second array
        
    Returns:
        Spearman correlation coefficient
    """
    # Convert to ranks
    rank_x = np.argsort(np.argsort(x))
    rank_y = np.argsort(np.argsort(y))
    
    # Calculate Pearson correlation on ranks (equivalent to Spearman)
    n = len(x)
    mean_x = np.mean(rank_x)
    mean_y = np.mean(rank_y)
    
    numerator = np.sum((rank_x - mean_x) * (rank_y - mean_y))
    denominator = np.sqrt(np.sum((rank_x - mean_x)**2) * np.sum((rank_y - mean_y)**2))
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

def t_test_for_correlation(r: float, n: int) -> float:
    """
    Perform t-test for correlation coefficient.
    
    H0: rho = 0
    H1: rho != 0
    
    Args:
        r: Correlation coefficient
        n: Sample size
        
    Returns:
        Two-tailed p-value
    """
    if abs(r) >= 1.0:
        return 0.0 if r != 0 else 1.0
    
    # t-statistic
    t_stat = r * np.sqrt((n - 2) / (1 - r**2))
    
    # Two-tailed p-value using t-distribution
    # Approximation using normal distribution for large n, or scipy if available
    try:
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-2))
    except ImportError:
        # Fallback: Normal approximation
        p_value = 2 * (1 - 0.5 * (1 + np.erf(abs(t_stat) / np.sqrt(2))))
    
    return p_value

def run_monte_carlo_power_simulation(
    n_samples: int,
    target_rho: float,
    n_iterations: int,
    seed: int,
    alpha: float = 0.05
) -> Dict:
    """
    Run Monte Carlo power simulation.
    
    Args:
        n_samples: Number of subjects in the dataset
        target_rho: Target correlation coefficient (effect size)
        n_iterations: Number of simulation iterations
        seed: Random seed
        alpha: Significance level
        
    Returns:
        Dictionary with simulation results
    """
    logger.info(f"Starting Monte Carlo power simulation: n={n_samples}, rho={target_rho}, iterations={n_iterations}")
    
    significant_count = 0
    correlation_values = []
    p_values = []
    
    for i in range(n_iterations):
        # Simulate data
        x, y = simulate_correlation_data(n_samples, target_rho, seed + i)
        
        # Calculate correlation
        r = calculate_spearman_correlation(x, y)
        correlation_values.append(r)
        
        # Perform t-test
        p_val = t_test_for_correlation(r, n_samples)
        p_values.append(p_val)
        
        if p_val < alpha:
            significant_count += 1
    
    power = significant_count / n_iterations
    
    return {
        "power": power,
        "significant_count": significant_count,
        "total_iterations": n_iterations,
        "mean_correlation": float(np.mean(correlation_values)),
        "std_correlation": float(np.std(correlation_values)),
        "mean_p_value": float(np.mean(p_values)),
        "std_p_value": float(np.std(p_values))
    }

def load_sample_size_from_correlation_results() -> Optional[int]:
    """
    Load sample size from correlation results CSV.
    
    Returns:
        Sample size (n) or None if file not found
    """
    results_path = Path("data/results/correlation_results.csv")
    
    if not results_path.exists():
        logger.warning(f"Correlation results file not found: {results_path}")
        return None
    
    try:
        import pandas as pd
        df = pd.read_csv(results_path)
        
        # Get the maximum 'n' value from the results
        if 'n' in df.columns:
            n = int(df['n'].max())
            logger.info(f"Loaded sample size from correlation results: n={n}")
            return n
        else:
            logger.warning("Column 'n' not found in correlation results")
            return None
    except Exception as e:
        logger.error(f"Error loading correlation results: {e}")
        return None

def run_power_analysis(
    n_samples: Optional[int] = None,
    target_rho: float = 0.3,
    n_iterations: int = 1000,
    seed: int = 42,
    alpha: float = 0.05
) -> Dict:
    """
    Main function to run power analysis.
    
    Args:
        n_samples: Sample size (if None, loads from correlation results)
        target_rho: Target effect size
        n_iterations: Number of Monte Carlo iterations
        seed: Random seed
        alpha: Significance level
        
    Returns:
        Dictionary with power analysis results
    """
    # Determine sample size
    if n_samples is None:
        n_samples = load_sample_size_from_correlation_results()
    
    if n_samples is None or n_samples == 0:
        # Default to a reasonable sample size if not found
        logger.warning("Could not determine sample size, using default n=100")
        n_samples = 100
    
    # Run simulation
    results = run_monte_carlo_power_simulation(
        n_samples=n_samples,
        target_rho=target_rho,
        n_iterations=n_iterations,
        seed=seed,
        alpha=alpha
    )
    
    # Determine if power is sufficient
    is_sufficient = results["power"] >= 0.80
    
    # Prepare final output
    output = {
        "power_for_r03": results["power"],
        "is_sufficient": is_sufficient,
        "simulation_seed": seed,
        "simulation_log_path": "data/results/power_analysis_log.json",
        "sample_size_used": n_samples,
        "target_effect_size": target_rho,
        "iterations": n_iterations,
        "alpha": alpha,
        "detailed_results": {
            "mean_correlation": results["mean_correlation"],
            "std_correlation": results["std_correlation"],
            "mean_p_value": results["mean_p_value"],
            "std_p_value": results["std_p_value"],
            "significant_count": results["significant_count"],
            "total_iterations": results["total_iterations"]
        }
    }
    
    return output

def main():
    """Main entry point for power analysis script."""
    logger.info("Starting Power Analysis (T027)")
    
    # Ensure output directories exist
    ensure_dirs()
    
    # Run power analysis
    results = run_power_analysis(
        n_samples=None,  # Will try to load from correlation results
        target_rho=0.3,
        n_iterations=1000,
        seed=42,
        alpha=0.05
    )
    
    # Save results
    output_path = Path("data/results/power_analysis.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Power analysis results saved to: {output_path}")
    logger.info(f"Power for r=0.3: {results['power_for_r03']:.4f}")
    logger.info(f"Is sufficient (>= 0.80): {results['is_sufficient']}")
    
    # Print summary
    print("\n" + "="*50)
    print("POWER ANALYSIS SUMMARY (T027)")
    print("="*50)
    print(f"Sample Size: {results['sample_size_used']}")
    print(f"Target Effect Size (r): {results['target_effect_size']}")
    print(f"Monte Carlo Iterations: {results['iterations']}")
    print(f"Simulation Seed: {results['simulation_seed']}")
    print(f"Power for r=0.3: {results['power_for_r03']:.4f}")
    print(f"Is Sufficient (>= 0.80): {results['is_sufficient']}")
    print(f"Output File: {output_path}")
    print("="*50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
