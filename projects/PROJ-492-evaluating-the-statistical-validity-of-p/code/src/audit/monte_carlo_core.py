"""
Monte-Carlo framework core for statistical validation.

This module provides the core functions for generating null distributions
and simulating test statistics using Monte-Carlo methods.
"""
import numpy as np
from typing import Tuple, List, Dict, Any, Optional

from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)

def set_seeds(seed: int = 42) -> None:
    """
    Initialize random number generators with a deterministic seed.
    
    Args:
        seed: Random seed for reproducibility.
    """
    set_rng_seed(seed)
    np.random.seed(seed)
    logger.info(f"Monte-Carlo seeds initialized with seed={seed}")

def generate_null_binary_data(
    n_control: int,
    n_treatment: int,
    p_baseline: float,
    n_simulations: int = 10000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate null binary outcome data under the assumption of no effect.
    
    Args:
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        p_baseline: Baseline conversion rate.
        n_simulations: Number of simulation iterations.
        
    Returns:
        Tuple of (control_conversions, treatment_conversions) arrays.
    """
    if not 0 <= p_baseline <= 1:
        raise ValueError("p_baseline must be between 0 and 1")
    
    set_rng_seed(42)  # Ensure deterministic behavior per Principle I
    
    control_conversions = np.random.binomial(
        n=n_control,
        p=p_baseline,
        size=n_simulations
    )
    
    treatment_conversions = np.random.binomial(
        n=n_treatment,
        p=p_baseline,  # Null hypothesis: same probability
        size=n_simulations
    )
    
    logger.debug(f"Generated {n_simulations} binary null samples")
    return control_conversions, treatment_conversions

def generate_null_continuous_data(
    n_control: int,
    n_treatment: int,
    mean_baseline: float,
    std_dev: float,
    n_simulations: int = 10000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate null continuous outcome data under the assumption of no effect.
    
    Args:
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        mean_baseline: Baseline mean.
        std_dev: Standard deviation of the population.
        n_simulations: Number of simulation iterations.
        
    Returns:
        Tuple of (control_means, treatment_means) arrays of sample means.
    """
    if std_dev <= 0:
        raise ValueError("std_dev must be positive")
    
    set_rng_seed(42)
    
    # Generate raw samples and compute means
    control_samples = np.random.normal(
        loc=mean_baseline,
        scale=std_dev,
        size=(n_simulations, n_control)
    )
    treatment_samples = np.random.normal(
        loc=mean_baseline,  # Null hypothesis: same mean
        scale=std_dev,
        size=(n_simulations, n_treatment)
    )
    
    control_means = np.mean(control_samples, axis=1)
    treatment_means = np.mean(treatment_samples, axis=1)
    
    logger.debug(f"Generated {n_simulations} continuous null samples")
    return control_means, treatment_means

def simulate_z_test_statistic(
    control_conversions: np.ndarray,
    treatment_conversions: np.ndarray,
    n_control: int,
    n_treatment: int
) -> np.ndarray:
    """
    Simulate two-proportion z-test statistics from binary data.
    
    Args:
        control_conversions: Array of control group conversions.
        treatment_conversions: Array of treatment group conversions.
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        
    Returns:
        Array of z-statistics.
    """
    p_control = control_conversions / n_control
    p_treatment = treatment_conversions / n_treatment
    
    # Pooled proportion under null
    p_pooled = (control_conversions + treatment_conversions) / (n_control + n_treatment)
    
    # Standard error under null
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
    
    # Avoid division by zero
    se = np.where(se == 0, 1e-10, se)
    
    z_stats = (p_treatment - p_control) / se
    return z_stats

def simulate_fisher_exact_table(
    control_conversions: np.ndarray,
    treatment_conversions: np.ndarray,
    n_control: int,
    n_treatment: int,
    n_simulations: int
) -> np.ndarray:
    """
    Simulate Fisher's exact test p-values from binary data.
    
    For Monte-Carlo validation, we approximate the exact test by counting
    the proportion of simulated tables that are as or more extreme.
    
    Args:
        control_conversions: Array of control group conversions.
        treatment_conversions: Array of treatment group conversions.
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        n_simulations: Number of simulations for p-value estimation.
        
    Returns:
        Array of empirical p-values (one per simulation iteration if run in batches,
        but here we return a single aggregate p-value estimate for the observed data
        pattern, or if called in a loop, the p-value for each iteration).
        
    Note: This function is designed to be called within a validation loop where
    we compare simulated statistics to observed statistics.
    """
    # For the purpose of Monte-Carlo validation, we compute the empirical p-value
    # by counting how often the simulated difference is as extreme as the observed.
    # However, since this function is part of the core, we return the simulated
    # odds ratios or a proxy statistic that can be compared.
    
    # Create 2x2 tables for each simulation
    # Table: [success_control, failure_control; success_treatment, failure_treatment]
    failure_control = n_control - control_conversions
    failure_treatment = n_treatment - treatment_conversions
    
    # Calculate odds ratio for each simulation (proxy for Fisher's statistic)
    # Avoid division by zero
    epsilon = 1e-10
    odds_control = (control_conversions + epsilon) / (failure_control + epsilon)
    odds_treatment = (treatment_conversions + epsilon) / (failure_treatment + epsilon)
    
    odds_ratios = odds_treatment / odds_control
    return odds_ratios

def simulate_welch_t_statistic(
    control_means: np.ndarray,
    treatment_means: np.ndarray,
    control_samples: np.ndarray,
    treatment_samples: np.ndarray
) -> np.ndarray:
    """
    Simulate Welch's t-test statistics from continuous data.
    
    Args:
        control_means: Array of control group sample means.
        treatment_means: Array of treatment group sample means.
        control_samples: 2D array of control group raw samples (n_simulations x n_control).
        treatment_samples: 2D array of treatment group raw samples (n_simulations x n_treatment).
        
    Returns:
        Array of Welch's t-statistics.
    """
    n_simulations = len(control_means)
    n_control = control_samples.shape[1]
    n_treatment = treatment_samples.shape[1]
    
    # Calculate sample standard deviations
    control_stds = np.std(control_samples, axis=1, ddof=1)
    treatment_stds = np.std(treatment_samples, axis=1, ddof=1)
    
    # Avoid division by zero
    control_stds = np.where(control_stds == 0, 1e-10, control_stds)
    treatment_stds = np.where(treatment_stds == 0, 1e-10, treatment_stds)
    
    # Standard error for Welch's t-test
    se = np.sqrt((control_stds**2 / n_control) + (treatment_stds**2 / n_treatment))
    se = np.where(se == 0, 1e-10, se)
    
    t_stats = (treatment_means - control_means) / se
    return t_stats

def simulate_binomial_statistic(
    observed_conversions: int,
    n_trials: int,
    p_null: float,
    n_simulations: int = 10000
) -> float:
    """
    Simulate binomial test p-value.
    
    Args:
        observed_conversions: Observed number of successes.
        n_trials: Total number of trials.
        p_null: Null hypothesis probability of success.
        n_simulations: Number of Monte-Carlo simulations.
        
    Returns:
        Empirical p-value (two-tailed).
    """
    set_rng_seed(42)
    
    # Simulate under null
    simulated_conversions = np.random.binomial(n=n_trials, p=p_null, size=n_simulations)
    
    # Calculate two-tailed p-value
    # Count how many simulated values are as or more extreme than observed
    # Extreme means |simulated - expected| >= |observed - expected|
    expected = n_trials * p_null
    observed_deviation = abs(observed_conversions - expected)
    
    simulated_deviations = abs(simulated_conversions - expected)
    extreme_count = np.sum(simulated_deviations >= observed_deviation)
    
    p_value = extreme_count / n_simulations
    logger.debug(f"Binomial simulation: observed={observed_conversions}, p_value={p_value:.4f}")
    return p_value

def compute_empirical_p_value(
    simulated_statistics: np.ndarray,
    observed_statistic: float,
    two_tailed: bool = True
) -> float:
    """
    Compute empirical p-value from simulated statistics.
    
    Args:
        simulated_statistics: Array of simulated test statistics.
        observed_statistic: The observed test statistic.
        two_tailed: Whether to compute a two-tailed p-value.
        
    Returns:
        Empirical p-value.
    """
    if two_tailed:
        # Two-tailed: count values as or more extreme in either direction
        # Assume null distribution is centered at 0 for symmetric tests
        abs_observed = abs(observed_statistic)
        abs_simulated = np.abs(simulated_statistics)
        extreme_count = np.sum(abs_simulated >= abs_observed)
    else:
        # One-tailed (upper)
        extreme_count = np.sum(simulated_statistics >= observed_statistic)
    
    p_value = extreme_count / len(simulated_statistics)
    return p_value

def run_monte_carlo_validation_core(
    test_type: str,
    n_simulations: int = 10000,
    **kwargs
) -> Dict[str, Any]:
    """
    Run Monte-Carlo validation core for a specific test type.
    
    Args:
        test_type: One of 'z_test', 'fisher', 'welch_t', 'binomial'.
        n_simulations: Number of Monte-Carlo simulations.
        **kwargs: Test-specific parameters.
            
    Returns:
        Dictionary containing simulation results and empirical p-value.
    """
    logger.info(f"Running Monte-Carlo validation for {test_type} with {n_simulations} simulations")
    
    if test_type == 'z_test':
        n_control = kwargs.get('n_control', 1000)
        n_treatment = kwargs.get('n_treatment', 1000)
        p_baseline = kwargs.get('p_baseline', 0.1)
        
        control_conv, treatment_conv = generate_null_binary_data(
            n_control, n_treatment, p_baseline, n_simulations
        )
        
        z_stats = simulate_z_test_statistic(
            control_conv, treatment_conv, n_control, n_treatment
        )
        
        # For validation, we typically compare to a known theoretical value or
        # check that the distribution is centered at 0
        mean_stat = float(np.mean(z_stats))
        std_stat = float(np.std(z_stats))
        
        return {
            'test_type': test_type,
            'n_simulations': n_simulations,
            'mean_statistic': mean_stat,
            'std_statistic': std_stat,
            'empirical_p_value_null': float(compute_empirical_p_value(z_stats, 0.0)),
            'statistics': z_stats.tolist()
        }
        
    elif test_type == 'fisher':
        n_control = kwargs.get('n_control', 1000)
        n_treatment = kwargs.get('n_treatment', 1000)
        p_baseline = kwargs.get('p_baseline', 0.1)
        
        control_conv, treatment_conv = generate_null_binary_data(
            n_control, n_treatment, p_baseline, n_simulations
        )
        
        odds_ratios = simulate_fisher_exact_table(
            control_conv, treatment_conv, n_control, n_treatment, n_simulations
        )
        
        # Under null, odds ratio should be ~1
        mean_or = float(np.mean(odds_ratios))
        median_or = float(np.median(odds_ratios))
        
        return {
            'test_type': test_type,
            'n_simulations': n_simulations,
            'mean_odds_ratio': mean_or,
            'median_odds_ratio': median_or,
            'statistics': odds_ratios.tolist()
        }
        
    elif test_type == 'welch_t':
        n_control = kwargs.get('n_control', 1000)
        n_treatment = kwargs.get('n_treatment', 1000)
        mean_baseline = kwargs.get('mean_baseline', 50.0)
        std_dev = kwargs.get('std_dev', 10.0)
        
        control_means, treatment_means = generate_null_continuous_data(
            n_control, n_treatment, mean_baseline, std_dev, n_simulations
        )
        
        # Regenerate raw samples for t-stat calculation
        set_rng_seed(42)
        control_samples = np.random.normal(
            loc=mean_baseline, scale=std_dev, size=(n_simulations, n_control)
        )
        treatment_samples = np.random.normal(
            loc=mean_baseline, scale=std_dev, size=(n_simulations, n_treatment)
        )
        
        t_stats = simulate_welch_t_statistic(
            control_means, treatment_means, control_samples, treatment_samples
        )
        
        mean_stat = float(np.mean(t_stats))
        std_stat = float(np.std(t_stats))
        
        return {
            'test_type': test_type,
            'n_simulations': n_simulations,
            'mean_statistic': mean_stat,
            'std_statistic': std_stat,
            'empirical_p_value_null': float(compute_empirical_p_value(t_stats, 0.0)),
            'statistics': t_stats.tolist()
        }
        
    elif test_type == 'binomial':
        n_trials = kwargs.get('n_trials', 1000)
        p_null = kwargs.get('p_null', 0.1)
        observed = kwargs.get('observed', int(n_trials * p_null))
        
        p_value = simulate_binomial_statistic(
            observed, n_trials, p_null, n_simulations
        )
        
        return {
            'test_type': test_type,
            'n_simulations': n_simulations,
            'observed': observed,
            'n_trials': n_trials,
            'p_null': p_null,
            'empirical_p_value': p_value
        }
        
    else:
        raise ValueError(f"Unknown test type: {test_type}")