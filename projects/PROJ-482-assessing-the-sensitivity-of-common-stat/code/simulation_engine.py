"""
Monte Carlo Simulation Engine.

Executes statistical tests on generated data, classifies errors,
and manages adaptive replication loops.

Refactored to separate data generation logic from test execution logic.
Data generation is now handled by the external `data_generator` module.
"""
import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, List, Optional
import logging
import os
import csv

# Import data generation logic from the dedicated module (T011)
from data_generator import generate_data, validate_sample_statistics

logger = logging.getLogger(__name__)

def clopper_pearson_interval(
    successes: int,
    n_trials: int,
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate the Clopper-Pearson exact confidence interval for a proportion.
    
    Args:
        successes: Number of successes (e.g., rejections).
        n_trials: Total number of trials.
        alpha: Significance level (1 - confidence level).
        
    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    if successes == 0:
        lower = 0.0
    else:
        lower = stats.beta.ppf(alpha / 2, successes, n_trials - successes + 1)
        
    if successes == n_trials:
        upper = 1.0
    else:
        upper = stats.beta.ppf(1 - alpha / 2, successes + 1, n_trials - successes)
        
    return lower, upper

def execute_t_test(sample1: np.ndarray, sample2: np.ndarray) -> float:
    """Run independent t-test and return p-value."""
    _, p_val = stats.ttest_ind(sample1, sample2)
    return p_val

def execute_anova(sample1: np.ndarray, sample2: np.ndarray) -> float:
    """Run one-way ANOVA and return p-value."""
    _, p_val = stats.f_oneway(sample1, sample2)
    return p_val

def execute_chi_squared(sample1: np.ndarray, sample2: np.ndarray) -> float:
    """
    Run Chi-squared test on binned data.
    Bins are created based on the combined range of both samples.
    """
    # Bin the data
    min_val = min(np.min(sample1), np.min(sample2))
    max_val = max(np.max(sample1), np.max(sample2))
    bins = np.linspace(min_val, max_val, 10) # 9 intervals
    
    hist1, _ = np.histogram(sample1, bins=bins)
    hist2, _ = np.histogram(sample2, bins=bins)
    
    contingency = np.array([hist1, hist2])
    _, p_val, _, _ = stats.chi2_contingency(contingency)
    return p_val

def execute_fisher_exact(sample1: np.ndarray, sample2: np.ndarray) -> float:
    """
    Run Fisher's Exact test on 2x2 contingency table.
    Splits data at the median of the combined sample.
    """
    combined = np.concatenate([sample1, sample2])
    median = np.median(combined)
    
    # Create 2x2 table: [count < median, count >= median]
    a = np.sum(sample1 < median)
    b = np.sum(sample1 >= median)
    c = np.sum(sample2 < median)
    d = np.sum(sample2 >= median)
    
    table = [[a, b], [c, d]]
    _, p_val = stats.fisher_exact(table)
    return p_val

def execute_fisher_exact_from_table(table: np.ndarray) -> float:
    """Run Fisher's exact test given a 2x2 contingency table."""
    _, p_val = stats.fisher_exact(table)
    return p_val

def run_single_test_replicate(
    sample1: np.ndarray,
    sample2: np.ndarray,
    test_type: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Execute a single statistical test replicate.
    
    Args:
        sample1, sample2: Data arrays.
        test_type: 't-test', 'anova', 'chi-squared', 'fisher-exact'.
        alpha: Significance threshold.
        
    Returns:
        Dictionary with 'p_value' and 'rejected' (boolean).
    """
    if test_type == "t-test":
        p_val = execute_t_test(sample1, sample2)
    elif test_type == "anova":
        p_val = execute_anova(sample1, sample2)
    elif test_type == "chi-squared":
        p_val = execute_chi_squared(sample1, sample2)
    elif test_type == "fisher-exact":
        p_val = execute_fisher_exact(sample1, sample2)
    else:
        raise ValueError(f"Unknown test type: {test_type}")
        
    return {
        "p_value": p_val,
        "rejected": p_val < alpha
    }

def run_adaptive_simulation(
    sample1: np.ndarray,
    sample2: np.ndarray,
    test_type: str,
    alpha: float = 0.05,
    min_reps: int = 1000,
    max_reps: int = 10000,
    target_ci_width: float = 0.01
) -> Dict[str, Any]:
    """
    Run adaptive Monte Carlo simulation until CI width is sufficient.
    
    Args:
        sample1, sample2: Data arrays (fixed for this scenario).
        test_type: Statistical test to run.
        alpha: Significance level.
        min_reps: Minimum replicates.
        max_reps: Maximum replicates cap.
        target_ci_width: Desired width of the 95% CI.
        
    Returns:
        Dictionary with 'error_rate', 'ci_lower', 'ci_upper', 'n_reps', 'p_values'.
    """
    rejections = 0
    p_values = []
    n = 0
    
    # Initial batch
    batch_size = 100
    current_reps = 0
    
    while current_reps < max_reps:
        batch_reps = min(batch_size, max_reps - current_reps)
        
        for _ in range(batch_reps):
            result = run_single_test_replicate(sample1, sample2, test_type, alpha)
            if result['rejected']:
                rejections += 1
            p_values.append(result['p_value'])
            
        current_reps += batch_reps
        n = current_reps
        
        # Check stopping condition after minimum reps
        if n >= min_reps:
            rate = rejections / n
            lower, upper = clopper_pearson_interval(rejections, n, 0.05)
            width = upper - lower
            
            if width <= target_ci_width:
                logger.info(f"Adaptive loop converged at n={n}, width={width:.4f}")
                break
                
        # Optional: increase batch size for efficiency if far from convergence
        if n > min_reps and width > target_ci_width * 2:
            batch_size = min(batch_size * 2, 500)
            
    rate = rejections / n
    lower, upper = clopper_pearson_interval(rejections, n, 0.05)
    
    return {
        "error_rate": rate,
        "ci_lower": lower,
        "ci_upper": upper,
        "n_reps": n,
        "p_values": p_values
    }

def generate_scenario_data(
    n: int,
    distribution: str,
    effect_size: float,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate sample data for a specific scenario using the data_generator module.
    
    This function encapsulates the data generation logic, separating it from
    the test execution logic in this file.
    
    Args:
        n: Sample size per group.
        distribution: Distribution type ('normal', 'uniform', 'log-normal').
        effect_size: Effect size for the alternative hypothesis (0 for null).
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (sample1, sample2) as numpy arrays.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Map distribution string to the appropriate generator
    if distribution == 'normal':
        sample1, sample2 = generate_data(
            n=n,
            dist_type='normal',
            effect_size=effect_size,
            seed=seed
        )
    elif distribution == 'uniform':
        sample1, sample2 = generate_data(
            n=n,
            dist_type='uniform',
            effect_size=effect_size,
            seed=seed
        )
    elif distribution == 'log-normal':
        sample1, sample2 = generate_data(
            n=n,
            dist_type='log-normal',
            effect_size=effect_size,
            seed=seed
        )
    else:
        raise ValueError(f"Unsupported distribution: {distribution}")
        
    return sample1, sample2