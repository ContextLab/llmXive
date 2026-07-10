"""
Monte-Carlo framework core for validating statistical test consistency.

This module provides the foundational functions for generating null distributions
and simulating test statistics to verify the validity of z-tests, Fisher's exact tests,
Welch's t-tests, and binomial tests used in the A/B test audit pipeline.
"""
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def set_seeds(seed: int = SEED) -> None:
    """
    Initialize the random number generator with a deterministic seed.
    
    Args:
        seed: The integer seed for reproducibility. Defaults to config.SEED.
    """
    set_rng_seed(seed)
    logger.info(f"Monte-Carlo seeds set to {seed}")

def generate_null_binary_data(
    n_control: int,
    n_treatment: int,
    p_control: float,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate binary outcome data under the null hypothesis (equal proportions).
    
    Args:
        n_control: Sample size for the control group.
        n_treatment: Sample size for the treatment group.
        p_control: The assumed common proportion under the null.
        seed: Optional seed for reproducibility.
        
    Returns:
        Tuple of (control_data, treatment_data) as numpy arrays of 0s and 1s.
    """
    if seed is not None:
        np.random.seed(seed)
    
    control_data = np.random.binomial(1, p_control, n_control)
    treatment_data = np.random.binomial(1, p_control, n_treatment)
    
    return control_data, treatment_data

def generate_null_continuous_data(
    n_control: int,
    n_treatment: int,
    mu: float,
    sigma: float,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate continuous outcome data under the null hypothesis (equal means).
    
    Args:
        n_control: Sample size for the control group.
        n_treatment: Sample size for the treatment group.
        mu: The assumed common mean under the null.
        sigma: The assumed common standard deviation.
        seed: Optional seed for reproducibility.
        
    Returns:
        Tuple of (control_data, treatment_data) as numpy arrays.
    """
    if seed is not None:
        np.random.seed(seed)
        
    control_data = np.random.normal(mu, sigma, n_control)
    treatment_data = np.random.normal(mu, sigma, n_treatment)
    
    return control_data, treatment_data

def simulate_z_test_statistic(
    control_data: np.ndarray,
    treatment_data: np.ndarray
) -> float:
    """
    Simulate the two-proportion z-test statistic.
    
    Args:
        control_data: Binary outcomes for control group.
        treatment_data: Binary outcomes for treatment group.
        
    Returns:
        The calculated z-statistic.
    """
    n1, n2 = len(control_data), len(treatment_data)
    p1 = np.mean(control_data)
    p2 = np.mean(treatment_data)
    
    if n1 + n2 == 0:
        return 0.0
        
    p_pooled = (np.sum(control_data) + np.sum(treatment_data)) / (n1 + n2)
    
    if p_pooled == 0 or p_pooled == 1:
        return 0.0
        
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    if se == 0:
        return 0.0
        
    z_stat = (p1 - p2) / se
    return float(z_stat)

def simulate_fisher_exact_table(
    control_data: np.ndarray,
    treatment_data: np.ndarray
) -> Tuple[int, int, int, int]:
    """
    Construct the 2x2 contingency table for Fisher's exact test.
    
    Args:
        control_data: Binary outcomes for control group.
        treatment_data: Binary outcomes for treatment group.
        
    Returns:
        Tuple (a, b, c, d) representing the contingency table:
        [[a, b],
         [c, d]]
        where a = successes in control, b = failures in control,
        c = successes in treatment, d = failures in treatment.
    """
    n_control = len(control_data)
    n_treatment = len(treatment_data)
    
    a = int(np.sum(control_data))
    b = n_control - a
    c = int(np.sum(treatment_data))
    d = n_treatment - c
    
    return a, b, c, d

def simulate_welch_t_statistic(
    control_data: np.ndarray,
    treatment_data: np.ndarray
) -> float:
    """
    Simulate the Welch's t-test statistic for continuous outcomes.
    
    Args:
        control_data: Continuous outcomes for control group.
        treatment_data: Continuous outcomes for treatment group.
        
    Returns:
        The calculated Welch's t-statistic.
    """
    n1, n2 = len(control_data), len(treatment_data)
    
    if n1 < 2 or n2 < 2:
        return 0.0
        
    mean1, mean2 = np.mean(control_data), np.mean(treatment_data)
    var1, var2 = np.var(control_data, ddof=1), np.var(treatment_data, ddof=1)
    
    if var1 == 0 and var2 == 0:
        return 0.0
        
    se_diff = np.sqrt(var1/n1 + var2/n2)
    
    if se_diff == 0:
        return 0.0
        
    t_stat = (mean1 - mean2) / se_diff
    return float(t_stat)

def simulate_binomial_statistic(
    successes: int,
    trials: int,
    p_null: float
) -> float:
    """
    Simulate the binomial test statistic (z-approximation).
    
    Args:
        successes: Number of observed successes.
        trials: Total number of trials.
        p_null: The null hypothesis proportion.
        
    Returns:
        The calculated z-statistic for the binomial test.
    """
    if trials == 0:
        return 0.0
        
    p_obs = successes / trials
    
    if p_null == 0 or p_null == 1:
        return 0.0
        
    se = np.sqrt(p_null * (1 - p_null) / trials)
    
    if se == 0:
        return 0.0
        
    z_stat = (p_obs - p_null) / se
    return float(z_stat)

def compute_empirical_p_value(
    simulated_stats: List[float],
    observed_stat: float,
    two_tailed: bool = True
) -> float:
    """
    Compute the empirical p-value from a list of simulated test statistics.
    
    Args:
        simulated_stats: List of test statistics from null simulations.
        observed_stat: The observed test statistic from real data.
        two_tailed: Whether to compute a two-tailed p-value.
        
    Returns:
        The empirical p-value.
    """
    if not simulated_stats:
        return 1.0
        
    n_sim = len(simulated_stats)
    
    if two_tailed:
        # Count how many simulated stats are as or more extreme than observed
        # in either direction
        extreme_count = sum(1 for s in simulated_stats if abs(s) >= abs(observed_stat))
    else:
        # One-tailed: count stats >= observed (for right-tailed)
        extreme_count = sum(1 for s in simulated_stats if s >= observed_stat)
        
    # Add 1 to numerator and denominator for a conservative estimate
    # (per standard Monte-Carlo p-value calculation)
    p_value = (extreme_count + 1) / (n_sim + 1)
    
    return float(p_value)

def run_monte_carlo_validation_core(
    test_type: str,
    n_replicates: int,
    params: Dict[str, Any],
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the core Monte-Carlo validation loop for a specific test type.
    
    Args:
        test_type: One of 'z_test', 'fisher', 'welch_t', 'binomial'.
        n_replicates: Number of Monte-Carlo replicates.
        params: Dictionary of parameters specific to the test type.
        seed: Optional seed for reproducibility.
        
    Returns:
        Dictionary containing simulation results including empirical p-values.
    """
    if seed is not None:
        set_seeds(seed)
    else:
        set_seeds()
        
    logger.info(f"Running {n_replicates} Monte-Carlo replicates for {test_type}")
    
    simulated_stats = []
    
    if test_type == 'z_test':
        # Parameters: n_control, n_treatment, p_common
        n1 = params.get('n_control', 100)
        n2 = params.get('n_treatment', 100)
        p = params.get('p_common', 0.5)
        
        for _ in range(n_replicates):
            ctrl, treat = generate_null_binary_data(n1, n2, p)
            stat = simulate_z_test_statistic(ctrl, treat)
            simulated_stats.append(stat)
            
    elif test_type == 'fisher':
        # Parameters: n_control, n_treatment, p_common
        n1 = params.get('n_control', 50)
        n2 = params.get('n_treatment', 50)
        p = params.get('p_common', 0.5)
        
        for _ in range(n_replicates):
            ctrl, treat = generate_null_binary_data(n1, n2, p)
            a, b, c, d = simulate_fisher_exact_table(ctrl, treat)
            # For Fisher's, we use the odds ratio or a simple count difference as statistic
            # Here we use the difference in proportions as a proxy for the simulation
            stat = (a / (a + b)) - (c / (c + d)) if (a + b) > 0 and (c + d) > 0 else 0.0
            simulated_stats.append(stat)
            
    elif test_type == 'welch_t':
        # Parameters: n_control, n_treatment, mu, sigma
        n1 = params.get('n_control', 50)
        n2 = params.get('n_treatment', 50)
        mu = params.get('mu', 0.0)
        sigma = params.get('sigma', 1.0)
        
        for _ in range(n_replicates):
            ctrl, treat = generate_null_continuous_data(n1, n2, mu, sigma)
            stat = simulate_welch_t_statistic(ctrl, treat)
            simulated_stats.append(stat)
            
    elif test_type == 'binomial':
        # Parameters: trials, p_null
        trials = params.get('trials', 100)
        p_null = params.get('p_null', 0.5)
        
        for _ in range(n_replicates):
            successes = np.random.binomial(trials, p_null)
            stat = simulate_binomial_statistic(successes, trials, p_null)
            simulated_stats.append(stat)
    else:
        raise ValueError(f"Unknown test type: {test_type}")
        
    # Compute summary statistics of the null distribution
    simulated_array = np.array(simulated_stats)
    
    result = {
        'test_type': test_type,
        'n_replicates': n_replicates,
        'mean_statistic': float(np.mean(simulated_array)),
        'std_statistic': float(np.std(simulated_array)),
        'min_statistic': float(np.min(simulated_array)),
        'max_statistic': float(np.max(simulated_array)),
        'simulated_stats': simulated_stats  # Return full list for p-value computation
    }
    
    logger.info(f"Monte-Carlo {test_type} completed. Mean stat: {result['mean_statistic']:.4f}")
    return result