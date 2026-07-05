"""
Monte Carlo Validation Core.

Implements the core logic for generating null distributions and simulating
statistical tests to validate the accuracy of analytical p-values.
"""

import numpy as np
from typing import Tuple, List, Dict, Any, Optional

from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def set_seeds(seed: Optional[int] = None) -> None:
    """
    Wrapper to set RNG seeds for this module using the global config.

    Args:
        seed: Optional seed override. Uses config.SEED if None.
    """
    set_rng_seed(seed)
    logger.debug(f"RNG seeds set for Monte Carlo module (seed={seed})")

def generate_null_binary_data(n_control: int, n_treatment: int, p_control: float) -> Tuple[List[int], List[int]]:
    """
    Generate binary outcome data under the null hypothesis (equal proportions).

    Args:
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        p_control: Baseline probability of success for control (used for both groups under null).

    Returns:
        Tuple of (control_outcomes, treatment_outcomes) lists of 0s and 1s.
    """
    set_rng_seed() # Ensure reproducibility if not explicitly set by caller
    control = np.random.binomial(1, p_control, n_control).tolist()
    treatment = np.random.binomial(1, p_control, n_treatment).tolist()
    return control, treatment

def generate_null_continuous_data(n_control: int, n_treatment: int, mu: float, sigma: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate continuous outcome data under the null hypothesis (equal means).

    Args:
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        mu: Mean of the distribution.
        sigma: Standard deviation of the distribution.

    Returns:
        Tuple of (control_data, treatment_data) numpy arrays.
    """
    set_rng_seed()
    control = np.random.normal(mu, sigma, n_control)
    treatment = np.random.normal(mu, sigma, n_treatment)
    return control, treatment

def simulate_z_test_statistic(n_control: int, n_treatment: int, p_control: float, n_replicates: int) -> List[float]:
    """
    Simulate the z-test statistic for binary outcomes under the null.

    Args:
        n_control: Sample size control.
        n_treatment: Sample size treatment.
        p_control: Baseline probability.
        n_replicates: Number of Monte Carlo replicates.

    Returns:
        List of z-statistics.
    """
    stats = []
    for _ in range(n_replicates):
        c, t = generate_null_binary_data(n_control, n_treatment, p_control)
        # Simple z-statistic calculation
        p_hat_c = sum(c) / len(c)
        p_hat_t = sum(t) / len(t)
        p_pooled = (sum(c) + sum(t)) / (len(c) + len(t))
        
        if p_pooled == 0 or p_pooled == 1:
            stats.append(0.0)
            continue
        
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/len(c) + 1/len(t)))
        z = (p_hat_t - p_hat_c) / se
        stats.append(z)
    return stats

def simulate_fisher_exact_table(n_control: int, n_treatment: int, p_control: float, n_replicates: int) -> List[Tuple[int, int, int, int]]:
    """
    Simulate 2x2 contingency tables for Fisher's exact test under the null.

    Returns:
        List of tables as (a, b, c, d) where:
        [[a, b],
         [c, d]]
    """
    tables = []
    for _ in range(n_replicates):
        c, t = generate_null_binary_data(n_control, n_treatment, p_control)
        # a = success control, b = failure control
        # c = success treatment, d = failure treatment
        a = sum(c)
        b = n_control - a
        c_count = sum(t)
        d = n_treatment - c_count
        tables.append((a, b, c_count, d))
    return tables

def simulate_welch_t_statistic(n_control: int, n_treatment: int, mu: float, sigma: float, n_replicates: int) -> List[float]:
    """
    Simulate Welch's t-statistic for continuous outcomes under the null.

    Returns:
        List of t-statistics.
    """
    stats = []
    for _ in range(n_replicates):
        c, t = generate_null_continuous_data(n_control, n_treatment, mu, sigma)
        mean_c = np.mean(c)
        mean_t = np.mean(t)
        var_c = np.var(c, ddof=1)
        var_t = np.var(t, ddof=1)
        
        # Handle zero variance
        if var_c == 0 and var_t == 0:
            stats.append(0.0)
            continue
        
        se = np.sqrt(var_c/n_control + var_t/n_treatment)
        if se == 0:
            stats.append(0.0)
        else:
            t_stat = (mean_t - mean_c) / se
            stats.append(t_stat)
    return stats

def simulate_binomial_statistic(n: int, p: float, k: int, n_replicates: int) -> List[int]:
    """
    Simulate binomial counts under the null.

    Returns:
        List of observed successes.
    """
    return np.random.binomial(n, p, n_replicates).tolist()

def compute_empirical_p_value(simulated_stats: List[float], observed_stat: float, two_tailed: bool = True) -> float:
    """
    Compute empirical p-value from simulated statistics.

    Args:
        simulated_stats: List of statistics from null distribution.
        observed_stat: The observed statistic from real data.
        two_tailed: If True, use absolute values for two-tailed test.

    Returns:
        Empirical p-value.
    """
    if two_tailed:
        observed_abs = abs(observed_stat)
        simulated_abs = [abs(s) for s in simulated_stats]
        count = sum(1 for s in simulated_abs if s >= observed_abs)
    else:
        count = sum(1 for s in simulated_stats if s >= observed_stat)
    
    return count / len(simulated_stats)

def run_monte_carlo_validation_core(
    test_type: str,
    n_control: int,
    n_treatment: int,
    p_control: float,
    n_replicates: int
) -> Dict[str, Any]:
    """
    Run the core Monte Carlo simulation for a specific test type.

    Args:
        test_type: 'z_test', 'fisher', 'welch_t'.
        n_control: Sample size control.
        n_treatment: Sample size treatment.
        p_control: Baseline probability (for binary) or mu (for continuous if applicable).
        n_replicates: Number of replicates.

    Returns:
        Dictionary with simulation results.
    """
    logger.info(f"Running Monte Carlo validation for {test_type} with {n_replicates} replicates.")
    
    if test_type == 'z_test':
        stats = simulate_z_test_statistic(n_control, n_treatment, p_control, n_replicates)
    elif test_type == 'fisher':
        # Fisher returns tables, we need to compute p-values or stats later
        # For now, return the tables
        tables = simulate_fisher_exact_table(n_control, n_treatment, p_control, n_replicates)
        return {"tables": tables, "type": "fisher"}
    elif test_type == 'welch_t':
        stats = simulate_welch_t_statistic(n_control, n_treatment, p_control, n_replicates) # p_control used as mu here for simplicity in signature
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    return {
        "test_type": test_type,
        "statistics": stats,
        "n_replicates": n_replicates
    }
