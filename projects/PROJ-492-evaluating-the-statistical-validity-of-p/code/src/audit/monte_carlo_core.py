"""
Monte-Carlo framework core for statistical validation.
Implements simulation functions for z-test, Fisher's exact, Welch's t-test, and binomial tests.
"""
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def set_seeds(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across numpy and python random modules.
    """
    set_rng_seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_null_binary_data(
    n_control: int, n_treatment: int, p_baseline: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate binary outcome data under the null hypothesis (no difference).
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        p_baseline: Baseline conversion rate (used for both groups under null)
        
    Returns:
        Tuple of (control_data, treatment_data) as numpy arrays of 0s and 1s
    """
    if not (0.0 < p_baseline < 1.0):
        raise ValueError(f"p_baseline must be between 0 and 1, got {p_baseline}")
        
    control_data = np.random.binomial(1, p_baseline, n_control)
    treatment_data = np.random.binomial(1, p_baseline, n_treatment)
    return control_data, treatment_data

def generate_null_continuous_data(
    n_control: int, n_treatment: int, mu: float, sigma: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate continuous outcome data under the null hypothesis.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        mu: Mean of the distribution (same for both groups under null)
        sigma: Standard deviation of the distribution
        
    Returns:
        Tuple of (control_data, treatment_data) as numpy arrays
    """
    if sigma <= 0:
        raise ValueError(f"sigma must be positive, got {sigma}")
        
    control_data = np.random.normal(mu, sigma, n_control)
    treatment_data = np.random.normal(mu, sigma, n_treatment)
    return control_data, treatment_data

def simulate_z_test_statistic(
    n_control: int, n_treatment: int, p_baseline: float
) -> float:
    """
    Simulate a two-proportion z-test statistic under the null hypothesis.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        p_baseline: Baseline conversion rate
        
    Returns:
        The computed z-statistic
    """
    control_data, treatment_data = generate_null_binary_data(
        n_control, n_treatment, p_baseline
    )
    
    p_hat_control = np.mean(control_data)
    p_hat_treatment = np.mean(treatment_data)
    
    # Pooled proportion
    p_pooled = (np.sum(control_data) + np.sum(treatment_data)) / (n_control + n_treatment)
    
    # Standard error under null
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
    
    if se == 0:
        return 0.0
        
    z_stat = (p_hat_treatment - p_hat_control) / se
    return float(z_stat)

def simulate_fisher_exact_table(
    n_control: int, n_treatment: int, p_baseline: float
) -> Tuple[int, int, int, int]:
    """
    Simulate a 2x2 contingency table for Fisher's exact test under the null.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        p_baseline: Baseline conversion rate
        
    Returns:
        Tuple (a, b, c, d) representing the contingency table:
        [[a, b],
         [c, d]]
        where a=successes_control, b=failures_control, c=successes_treatment, d=failures_treatment
    """
    control_data, treatment_data = generate_null_binary_data(
        n_control, n_treatment, p_baseline
    )
    
    a = int(np.sum(control_data))
    b = n_control - a
    c = int(np.sum(treatment_data))
    d = n_treatment - c
    
    return a, b, c, d

def simulate_welch_t_statistic(
    n_control: int, n_treatment: int, mu: float, sigma: float
) -> float:
    """
    Simulate a Welch's t-test statistic under the null hypothesis.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        mu: Mean of the distribution
        sigma: Standard deviation of the distribution
        
    Returns:
        The computed Welch's t-statistic
    """
    control_data, treatment_data = generate_null_continuous_data(
        n_control, n_treatment, mu, sigma
    )
    
    mean_control = np.mean(control_data)
    mean_treatment = np.mean(treatment_data)
    var_control = np.var(control_data, ddof=1)
    var_treatment = np.var(treatment_data, ddof=1)
    
    # Handle edge case where variance is zero
    if var_control == 0 and var_treatment == 0:
        return 0.0
        
    se = np.sqrt(var_control / n_control + var_treatment / n_treatment)
    
    if se == 0:
        return 0.0
        
    t_stat = (mean_treatment - mean_control) / se
    return float(t_stat)

def simulate_binomial_statistic(
    n: int, k: int, p_null: float
) -> float:
    """
    Simulate a binomial test statistic under the null hypothesis.
    
    Args:
        n: Total number of trials
        k: Observed number of successes
        p_null: Null hypothesis probability of success
        
    Returns:
        The z-statistic for the binomial test
    """
    if not (0.0 < p_null < 1.0):
        raise ValueError(f"p_null must be between 0 and 1, got {p_null}")
    if k < 0 or k > n:
        raise ValueError(f"k must be between 0 and n, got k={k}, n={n}")
        
    # Under null, expected successes
    expected = n * p_null
    variance = n * p_null * (1 - p_null)
    
    if variance == 0:
        return 0.0
        
    z_stat = (k - expected) / np.sqrt(variance)
    return float(z_stat)

def compute_empirical_p_value(
    simulated_stats: List[float], observed_stat: float, two_tailed: bool = True
) -> float:
    """
    Compute empirical p-value from simulated statistics.
    
    Args:
        simulated_stats: List of simulated test statistics under null
        observed_stat: The observed test statistic from real data
        two_tailed: Whether to compute two-tailed p-value
        
    Returns:
        Empirical p-value
    """
    if not simulated_stats:
        raise ValueError("simulated_stats cannot be empty")
        
    simulated_array = np.array(simulated_stats)
    
    if two_tailed:
        # Two-tailed: count how many simulated stats are as extreme or more extreme
        extreme_count = np.sum(np.abs(simulated_array) >= np.abs(observed_stat))
    else:
        # One-tailed (right): count how many simulated stats are >= observed
        extreme_count = np.sum(simulated_array >= observed_stat)
        
    p_value = (extreme_count + 1) / (len(simulated_stats) + 1)
    return float(p_value)

def run_monte_carlo_validation_core(
    test_type: str,
    n_simulations: int,
    n_control: int = 1000,
    n_treatment: int = 1000,
    p_baseline: float = 0.1,
    mu: float = 0.0,
    sigma: float = 1.0,
    observed_stat: Optional[float] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run Monte-Carlo validation core for a specific test type.
    
    Args:
        test_type: One of 'z_test', 'fisher', 'welch_t', 'binomial'
        n_simulations: Number of Monte-Carlo simulations to run
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        p_baseline: Baseline conversion rate for binary tests
        mu: Mean for continuous tests
        sigma: Standard deviation for continuous tests
        observed_stat: Optional observed statistic to compute empirical p-value
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with simulation results including stats, p-value estimate, and metadata
    """
    set_seeds(seed)
    logger.info(f"Running {n_simulations} Monte-Carlo simulations for {test_type}")
    
    simulated_stats = []
    
    if test_type == 'z_test':
        for _ in range(n_simulations):
            stat = simulate_z_test_statistic(n_control, n_treatment, p_baseline)
            simulated_stats.append(stat)
    elif test_type == 'fisher':
        for _ in range(n_simulations):
            # For Fisher, we simulate the table and compute the statistic (e.g., odds ratio log)
            a, b, c, d = simulate_fisher_exact_table(n_control, n_treatment, p_baseline)
            # Compute log odds ratio as the statistic
            if a > 0 and b > 0 and c > 0 and d > 0:
                odds_ratio = (a * d) / (b * c)
                stat = np.log(odds_ratio)
            else:
                stat = 0.0
            simulated_stats.append(stat)
    elif test_type == 'welch_t':
        for _ in range(n_simulations):
            stat = simulate_welch_t_statistic(n_control, n_treatment, mu, sigma)
            simulated_stats.append(stat)
    elif test_type == 'binomial':
        # For binomial, we need a fixed n and p_null
        n_trials = n_control + n_treatment
        p_null = p_baseline
        for _ in range(n_simulations):
            k = np.random.binomial(n_trials, p_null)
            stat = simulate_binomial_statistic(n_trials, k, p_null)
            simulated_stats.append(stat)
    else:
        raise ValueError(f"Unknown test_type: {test_type}")
    
    # Compute summary statistics
    simulated_array = np.array(simulated_stats)
    mean_stat = float(np.mean(simulated_array))
    std_stat = float(np.std(simulated_array))
    min_stat = float(np.min(simulated_array))
    max_stat = float(np.max(simulated_array))
    
    result = {
        "test_type": test_type,
        "n_simulations": n_simulations,
        "mean_statistic": mean_stat,
        "std_statistic": std_stat,
        "min_statistic": min_stat,
        "max_statistic": max_stat,
        "distribution_stats": {
            "skewness": float(np.mean(((simulated_array - mean_stat) / std_stat) ** 3)) if std_stat > 0 else 0.0,
            "kurtosis": float(np.mean(((simulated_array - mean_stat) / std_stat) ** 4) - 3) if std_stat > 0 else 0.0
        }
    }
    
    if observed_stat is not None:
        empirical_p = compute_empirical_p_value(simulated_stats, observed_stat)
        result["observed_statistic"] = observed_stat
        result["empirical_p_value"] = empirical_p
        logger.info(f"Empirical p-value for observed stat {observed_stat}: {empirical_p}")
    
    logger.info(f"Monte-Carlo simulation completed for {test_type}")
    return result

# Ensure module is importable with all public functions
__all__ = [
    'set_seeds',
    'generate_null_binary_data',
    'generate_null_continuous_data',
    'simulate_z_test_statistic',
    'simulate_fisher_exact_table',
    'simulate_welch_t_statistic',
    'simulate_binomial_statistic',
    'compute_empirical_p_value',
    'run_monte_carlo_validation_core'
]