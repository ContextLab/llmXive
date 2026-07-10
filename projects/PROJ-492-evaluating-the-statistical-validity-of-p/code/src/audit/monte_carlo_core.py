"""
Monte-Carlo Framework Core
Provides functions to simulate null distributions and compute empirical p-values
for various statistical tests used in A/B test validation.
"""
import numpy as np
from typing import Tuple, List, Dict, Any, Optional

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def set_seeds(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.
    Uses the global SEED from config if no specific seed is provided.
    """
    if seed is None:
        seed = SEED
    set_rng_seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_null_binary_data(
    n_control: int,
    n_treatment: int,
    p_baseline: float,
    rng: Optional[np.random.Generator] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate binary outcome data under the null hypothesis (no effect).
    Both groups share the same baseline probability p_baseline.

    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        p_baseline: Baseline conversion rate
        rng: Optional numpy random generator

    Returns:
        Tuple of (control_data, treatment_data) as 1D arrays of 0s and 1s
    """
    if rng is None:
        rng = np.random.default_rng()
    
    control_data = rng.binomial(1, p_baseline, n_control)
    treatment_data = rng.binomial(1, p_baseline, n_treatment)
    
    return control_data, treatment_data

def generate_null_continuous_data(
    n_control: int,
    n_treatment: int,
    mu: float,
    sigma: float,
    rng: Optional[np.random.Generator] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate continuous outcome data under the null hypothesis (no effect).
    Both groups share the same mean mu and standard deviation sigma.

    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        mu: Population mean
        sigma: Population standard deviation
        rng: Optional numpy random generator

    Returns:
        Tuple of (control_data, treatment_data) as 1D arrays
    """
    if rng is None:
        rng = np.random.default_rng()
    
    control_data = rng.normal(mu, sigma, n_control)
    treatment_data = rng.normal(mu, sigma, n_treatment)
    
    return control_data, treatment_data

def simulate_z_test_statistic(
    control_data: np.ndarray,
    treatment_data: np.ndarray
) -> float:
    """
    Compute the two-proportion z-test statistic for binary data.
    
    Args:
        control_data: Binary outcomes for control group
        treatment_data: Binary outcomes for treatment group
        
    Returns:
        Z-statistic value
    """
    n1, x1 = len(control_data), np.sum(control_data)
    n2, x2 = len(treatment_data), np.sum(treatment_data)
    
    p1 = x1 / n1
    p2 = x2 / n2
    
    p_pooled = (x1 + x2) / (n1 + n2)
    
    if p_pooled == 0 or p_pooled == 1:
        return 0.0
        
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    if se == 0:
        return 0.0
        
    z_stat = (p1 - p2) / se
    return z_stat

def simulate_fisher_exact_table(
    control_data: np.ndarray,
    treatment_data: np.ndarray
) -> float:
    """
    Compute Fisher's exact test p-value (two-sided) for binary data.
    Returns the p-value directly as it is the statistic of interest.
    
    Args:
        control_data: Binary outcomes for control group
        treatment_data: Binary outcomes for treatment group
        
    Returns:
        Two-sided p-value from Fisher's exact test
    """
    from scipy import stats
    
    n1, x1 = len(control_data), np.sum(control_data)
    n2, x2 = len(treatment_data), np.sum(treatment_data)
    
    # Create contingency table
    # [[x1, n1-x1], [x2, n2-x2]]
    table = [[x1, n1 - x1], [x2, n2 - x2]]
    
    try:
        _, p_value = stats.fisher_exact(table, alternative='two-sided')
        return p_value
    except Exception as e:
        logger.warning(f"Fisher exact test failed: {e}. Returning 1.0.")
        return 1.0

def simulate_welch_t_statistic(
    control_data: np.ndarray,
    treatment_data: np.ndarray
) -> float:
    """
    Compute Welch's t-test statistic for continuous data.
    
    Args:
        control_data: Continuous outcomes for control group
        treatment_data: Continuous outcomes for treatment group
        
    Returns:
        T-statistic value
    """
    n1 = len(control_data)
    n2 = len(treatment_data)
    
    if n1 < 2 or n2 < 2:
        return 0.0
        
    mean1 = np.mean(control_data)
    mean2 = np.mean(treatment_data)
    var1 = np.var(control_data, ddof=1)
    var2 = np.var(treatment_data, ddof=1)
    
    # Avoid division by zero
    if var1 == 0 and var2 == 0:
        return 0.0
        
    se_diff = np.sqrt(var1 / n1 + var2 / n2)
    
    if se_diff == 0:
        return 0.0
        
    t_stat = (mean1 - mean2) / se_diff
    return t_stat

def simulate_binomial_statistic(
    n: int,
    k: int,
    p_null: float
) -> float:
    """
    Compute the probability of observing k or more successes in n trials
    under the null hypothesis p_null (one-sided upper tail).
    
    Args:
        n: Number of trials
        k: Number of successes observed
        p_null: Null hypothesis probability of success
        
    Returns:
        One-sided p-value (P(X >= k))
    """
    from scipy import stats
    
    if n <= 0 or p_null <= 0 or p_null >= 1:
        return 1.0
        
    # P(X >= k) = 1 - P(X <= k-1)
    p_value = 1.0 - stats.binom.cdf(k - 1, n, p_null)
    return p_value

def compute_empirical_p_value(
    simulated_statistics: List[float],
    observed_statistic: float,
    alternative: str = 'two-sided'
) -> float:
    """
    Compute the empirical p-value from a list of simulated statistics.
    
    Args:
        simulated_statistics: List of statistics from null distribution
        observed_statistic: The actual observed statistic
        alternative: 'two-sided', 'greater', or 'less'
        
    Returns:
        Empirical p-value
    """
    if not simulated_statistics:
        logger.error("No simulated statistics provided.")
        return 1.0
        
    simulated_array = np.array(simulated_statistics)
    
    if alternative == 'two-sided':
        # For two-sided, we look at the absolute value
        abs_obs = np.abs(observed_statistic)
        abs_sim = np.abs(simulated_array)
        count = np.sum(abs_sim >= abs_obs)
    elif alternative == 'greater':
        count = np.sum(simulated_array >= observed_statistic)
    elif alternative == 'less':
        count = np.sum(simulated_array <= observed_statistic)
    else:
        logger.warning(f"Unknown alternative '{alternative}', defaulting to two-sided.")
        abs_obs = np.abs(observed_statistic)
        abs_sim = np.abs(simulated_array)
        count = np.sum(abs_sim >= abs_obs)
        
    # Add 1 to numerator and denominator for unbiased estimation
    # (as if we included the observed statistic in the null distribution)
    n_sim = len(simulated_statistics)
    empirical_p = (count + 1) / (n_sim + 1)
    
    return empirical_p

def run_monte_carlo_validation_core(
    n_replicates: int,
    test_type: str,
    n_control: int,
    n_treatment: int,
    baseline_param: float,
    scale_param: Optional[float] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the core Monte-Carlo simulation for a specific test type.
    
    Args:
        n_replicates: Number of simulation replicates
        test_type: 'z_test', 'fisher', 'welch_t', or 'binomial'
        n_control: Control group sample size
        n_treatment: Treatment group sample size
        baseline_param: For binary: p_baseline; for continuous: mu
        scale_param: For continuous: sigma; for binomial: p_null (if different)
        seed: Random seed (optional, uses global if None)
        
    Returns:
        Dictionary with results including empirical p-value distribution stats
    """
    if seed is not None:
        set_seeds(seed)
    else:
        set_seeds()
        
    logger.info(f"Running {n_replicates} Monte-Carlo replicates for {test_type}")
    
    simulated_stats = []
    
    # Use a dedicated RNG for the loop to ensure reproducibility
    rng = np.random.default_rng()
    
    for i in range(n_replicates):
        if test_type == 'z_test' or test_type == 'fisher':
            # Binary data simulation
            ctrl, treat = generate_null_binary_data(
                n_control, n_treatment, baseline_param, rng
            )
            
            if test_type == 'z_test':
                stat = simulate_z_test_statistic(ctrl, treat)
            else:
                stat = simulate_fisher_exact_table(ctrl, treat)
                
        elif test_type == 'welch_t':
            # Continuous data simulation
            if scale_param is None:
                scale_param = 1.0
            ctrl, treat = generate_null_continuous_data(
                n_control, n_treatment, baseline_param, scale_param, rng
            )
            stat = simulate_welch_t_statistic(ctrl, treat)
            
        elif test_type == 'binomial':
            # Binomial test simulation
            p_null = scale_param if scale_param is not None else baseline_param
            n = n_control + n_treatment
            # Generate successes under null
            k = rng.binomial(n, p_null)
            stat = simulate_binomial_statistic(n, k, p_null)
        else:
            raise ValueError(f"Unknown test_type: {test_type}")
            
        simulated_stats.append(stat)
        
    # Compute summary statistics of the null distribution
    stats_array = np.array(simulated_stats)
    
    result = {
        "test_type": test_type,
        "n_replicates": n_replicates,
        "mean_statistic": float(np.mean(stats_array)),
        "std_statistic": float(np.std(stats_array)),
        "min_statistic": float(np.min(stats_array)),
        "max_statistic": float(np.max(stats_array)),
        "median_statistic": float(np.median(stats_array)),
        "simulated_statistics": simulated_stats
    }
    
    logger.info(f"Monte-Carlo simulation complete for {test_type}. "
                f"Mean: {result['mean_statistic']:.4f}, Std: {result['std_statistic']:.4f}")
                
    return result