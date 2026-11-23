"""
Empirical Power Calculation Module

Implements bootstrap simulation for power estimation and the Synthetic Ground Truth test.
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats
import logging
import os

from config import RANDOM_SEED, BOOTSTRAP_ITERATIONS

logger = logging.getLogger(__name__)

def generate_synthetic_data(
    n1: int = 50,
    n2: int = 50,
    true_effect_size: float = 0.5,
    true_std: float = 1.0,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, float, float]:
    """
    Generate two groups of synthetic data with a known true effect size (Cohen's d).
    
    Args:
        n1: Sample size for group 1
        n2: Sample size for group 2
        true_effect_size: The known Cohen's d (difference in means / std)
        true_std: The known standard deviation for both groups
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (group1_data, group2_data, true_mean1, true_mean2)
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Group 1: Mean = 0
    mean1 = 0.0
    data1 = np.random.normal(loc=mean1, scale=true_std, size=n1)
    
    # Group 2: Mean = true_effect_size * true_std
    mean2 = true_effect_size * true_std
    data2 = np.random.normal(loc=mean2, scale=true_std, size=n2)
    
    return data1, data2, mean1, mean2

def run_bootstrap_power_simulation(
    data1: np.ndarray,
    data2: np.ndarray,
    n_iterations: int = 1000,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> float:
    """
    Run bootstrap simulation to estimate statistical power.
    
    This function resamples the data with replacement, performs a t-test,
    and calculates the proportion of times the null hypothesis is rejected.
    
    Args:
        data1: Data for group 1
        data2: Data for group 2
        n_iterations: Number of bootstrap iterations
        alpha: Significance level
        seed: Random seed
        
    Returns:
        Estimated power (proportion of significant results)
    """
    if seed is not None:
        np.random.seed(seed)
    
    n1 = len(data1)
    n2 = len(data2)
    significant_count = 0
    
    for _ in range(n_iterations):
        # Resample with replacement
        boot_data1 = np.random.choice(data1, size=n1, replace=True)
        boot_data2 = np.random.choice(data2, size=n2, replace=True)
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(boot_data1, boot_data2, equal_var=True)
        
        if p_value < alpha:
            significant_count += 1
    
    return significant_count / n_iterations

def run_synthetic_ground_truth_test(
    n1: int = 100,
    n2: int = 100,
    true_effect_size: float = 0.5,
    true_std: float = 1.0,
    n_iterations: int = BOOTSTRAP_ITERATIONS,
    tolerance: float = 0.05,
    seed: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Execute the Synthetic Ground Truth test (T031a).
    
    1. Generate synthetic data with known parameters (true_effect_size).
    2. Calculate theoretical power using the known parameters.
    3. Run bootstrap simulation to estimate empirical power.
    4. Compare empirical power to true power.
    5. Return results including pass/fail status based on tolerance.
    
    FR-008: Verify recovery rate matches true power within 5%.
    """
    logger.info(f"Running Synthetic Ground Truth Test with n1={n1}, n2={n2}, effect={true_effect_size}")
    
    # 1. Generate synthetic data
    data1, data2, _, _ = generate_synthetic_data(
        n1=n1, n2=n2, true_effect_size=true_effect_size, 
        true_std=true_std, seed=seed
    )
    
    # 2. Calculate theoretical power
    # Cohen's d = (mean1 - mean2) / std
    # We use the known parameters to calculate theoretical power
    # For a two-sample t-test, we can use statsmodels or manual calculation
    # Here we use a manual approximation based on non-central t-distribution
    
    # Standard error of the difference
    se = true_std * np.sqrt(1/n1 + 1/n2)
    # Non-centrality parameter
    ncp = true_effect_size / np.sqrt(1/n1 + 1/n2)
    
    # Critical t-value for two-tailed test
    df = n1 + n2 - 2
    t_crit = stats.t.ppf(1 - 0.05/2, df)
    
    # Theoretical power: P(|T| > t_crit | H1 is true)
    # Using non-central t-distribution
    power_lower = stats.nct.cdf(-t_crit, df, ncp)
    power_upper = 1 - stats.nct.cdf(t_crit, df, ncp)
    theoretical_power = power_lower + power_upper
    
    # 3. Run bootstrap simulation
    empirical_power = run_bootstrap_power_simulation(
        data1, data2, n_iterations=n_iterations, seed=seed + 1
    )
    
    # 4. Calculate error and check tolerance
    absolute_error = abs(empirical_power - theoretical_power)
    passed = absolute_error <= tolerance
    
    result = {
        "true_power": theoretical_power,
        "empirical_power": empirical_power,
        "absolute_error": absolute_error,
        "recovery_rate": 1.0 if passed else 0.0, # 1.0 if within tolerance, 0.0 otherwise
        "passed": passed,
        "message": f"Recovery within {tolerance*100}%: {'Yes' if passed else 'No'}"
    }
    
    logger.info(f"Theoretical Power: {theoretical_power:.4f}")
    logger.info(f"Empirical Power: {empirical_power:.4f}")
    logger.info(f"Absolute Error: {absolute_error:.4f}")
    logger.info(f"Test Result: {'PASSED' if passed else 'FAILED'}")
    
    return result

def main():
    """Entry point for running the synthetic ground truth test."""
    result = run_synthetic_ground_truth_test()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    import json
    main()
