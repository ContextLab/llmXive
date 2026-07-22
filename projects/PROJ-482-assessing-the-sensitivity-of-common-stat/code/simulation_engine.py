import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, List, Optional, Callable
import logging
import os
import csv
from dataclasses import dataclass
import time

from config import SimulationConfig, get_simulation_grid
from data_generator import generate_data, validate_sample_statistics
from utils.file_lock import file_lock, write_pvalue_batch

logger = logging.getLogger(__name__)

@dataclass
class SimulationResult:
    """Result of a single simulation replicate."""
    sample_size: int
    distribution_type: str
    test_type: str
    p_value: float
    hypothesis_type: str
    is_rejection: bool
    replicate_id: int

@dataclass
class AdaptiveRunResult:
    """Result of an adaptive simulation run for a specific configuration."""
    sample_size: int
    distribution_type: str
    test_type: str
    hypothesis_type: str
    total_replicates: int
    type_i_errors: int
    type_ii_errors: int
    observed_alpha: float
    observed_power: float
    ci_lower: float
    ci_upper: float
    ci_width: float
    converged: bool
    raw_pvalues_file: str

def bootstrap_ci(
    outcomes: List[int], 
    n_bootstrap: int = 1000, 
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for binary outcomes.
    
    Args:
        outcomes: List of binary outcomes (0 or 1)
        n_bootstrap: Number of bootstrap samples
        alpha: Significance level for CI
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if not outcomes:
        return (0.0, 0.0)
    
    n = len(outcomes)
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(outcomes, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))
    
    bootstrap_means.sort()
    lower_idx = int(alpha / 2 * n_bootstrap)
    upper_idx = int((1 - alpha / 2) * n_bootstrap)
    
    return (bootstrap_means[lower_idx], bootstrap_means[upper_idx])

def execute_t_test(data1: np.ndarray, data2: np.ndarray) -> float:
    """Execute independent t-test and return p-value."""
    _, p_value = stats.ttest_ind(data1, data2)
    return p_value

def execute_anova(data1: np.ndarray, data2: np.ndarray) -> float:
    """Execute ANOVA and return p-value."""
    _, p_value = stats.f_oneway(data1, data2)
    return p_value

def execute_chi_squared(data1: np.ndarray, data2: np.ndarray) -> float:
    """
    Execute Chi-squared test on binned data.
    Bins data into 2 groups (low/high) for each distribution.
    """
    # Bin the data into 2 categories for Chi-squared test
    threshold = np.median(np.concatenate([data1, data2]))
    group1 = (data1 < threshold).astype(int)
    group2 = (data2 < threshold).astype(int)
    
    # Create contingency table
    contingency = np.array([
        [np.sum(group1), len(data1) - np.sum(group1)],
        [np.sum(group2), len(data2) - np.sum(group2)]
    ])
    
    _, p_value, _, _ = stats.chi2_contingency(contingency)
    return p_value

def execute_fisher_exact_from_table(contingency: np.ndarray) -> float:
    """Execute Fisher's Exact test from a contingency table."""
    _, p_value = stats.fisher_exact(contingency)
    return p_value

def execute_fisher_exact(data1: np.ndarray, data2: np.ndarray) -> float:
    """
    Execute Fisher's Exact test on binned data.
    Used when expected cell counts < 5.
    """
    threshold = np.median(np.concatenate([data1, data2]))
    group1 = (data1 < threshold).astype(int)
    group2 = (data2 < threshold).astype(int)
    
    contingency = np.array([
        [np.sum(group1), len(data1) - np.sum(group1)],
        [np.sum(group2), len(data2) - np.sum(group2)]
    ])
    
    _, p_value = stats.fisher_exact(contingency)
    return p_value

def generate_scenario_data(
    config: SimulationConfig,
    sample_size: int,
    distribution_type: str,
    effect_size: float
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate data for a specific scenario."""
    data1, data2 = generate_data(
        n=sample_size,
        distribution=distribution_type,
        effect_size=effect_size
    )
    return data1, data2

def run_single_test_replicate(
    data1: np.ndarray,
    data2: np.ndarray,
    test_type: str
) -> float:
    """Run a single test replicate and return p-value."""
    if test_type == 't_test':
        return execute_t_test(data1, data2)
    elif test_type == 'anova':
        return execute_anova(data1, data2)
    elif test_type == 'chi_squared':
        # Check expected counts for Chi-squared validity
        threshold = np.median(np.concatenate([data1, data2]))
        group1 = (data1 < threshold).astype(int)
        group2 = (data2 < threshold).astype(int)
        contingency = np.array([
            [np.sum(group1), len(data1) - np.sum(group1)],
            [np.sum(group2), len(data2) - np.sum(group2)]
        ])
        
        expected = stats.chi2_contingency(contingency)[3]
        if np.any(expected < 5):
            return execute_fisher_exact_from_table(contingency)
        return execute_chi_squared(data1, data2)
    else:
        raise ValueError(f"Unknown test type: {test_type}")

def save_raw_pvalues(
    file_path: str,
    pvalues: List[float],
    sample_size: int,
    distribution_type: str,
    test_type: str,
    hypothesis_type: str,
    start_replicate: int
):
    """
    Save raw p-values to CSV with proper schema and locking.
    """
    records = []
    for i, p in enumerate(pvalues):
        records.append({
            'sample_size': sample_size,
            'distribution_type': distribution_type,
            'test_type': test_type,
            'p_value': p,
            'hypothesis_type': hypothesis_type
        })
    
    write_pvalue_batch(file_path, records, {})

def count_type_i_and_type_II_errors(
    pvalues: List[float],
    hypothesis_type: str,
    alpha: float
) -> Tuple[int, int]:
    """Count Type I and Type II errors based on hypothesis type."""
    rejections = sum(1 for p in pvalues if p < alpha)
    
    if hypothesis_type == 'null':
        # Type I error: rejecting null when it's true
        return rejections, 0
    else:
        # Type II error: failing to reject null when alternative is true
        return 0, len(pvalues) - rejections

def validate_type_i_error_rates(
    observed_rate: float,
    theoretical_alpha: float,
    tolerance: float = 0.01
) -> bool:
    """Validate if observed Type I error rate is within tolerance of theoretical."""
    return abs(observed_rate - theoretical_alpha) <= tolerance

def run_adaptive_simulation(
    config: SimulationConfig,
    sample_size: int,
    distribution_type: str,
    test_type: str,
    hypothesis_type: str,
    output_dir: str
) -> AdaptiveRunResult:
    """
    Run adaptive Monte Carlo simulation with bootstrap CI.
    """
    effect_size = 0.0 if hypothesis_type == 'null' else 0.5
    pvalues = []
    all_outcomes = []
    replicate_id = 0
    converged = False
    ci_width = float('inf')
    
    # Output file for raw p-values
    raw_pvalues_file = os.path.join(
        output_dir, 'raw_pvalues.csv'
    )
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if file exists to determine starting point
    file_exists = os.path.exists(raw_pvalues_file)
    
    while replicate_id < config.max_replicates:
        # Generate data
        data1, data2 = generate_scenario_data(
            config, sample_size, distribution_type, effect_size
        )
        
        # Run test
        p_value = run_single_test_replicate(data1, data2, test_type)
        
        # Store result
        pvalues.append(p_value)
        outcome = 1 if p_value < config.alpha else 0
        all_outcomes.append(outcome)
        replicate_id += 1
        
        # Batch write every 100 replicates
        if replicate_id % 100 == 0:
            save_raw_pvalues(
                raw_pvalues_file,
                pvalues[-100:],
                sample_size,
                distribution_type,
                test_type,
                hypothesis_type,
                replicate_id - 100
            )
        
        # Check convergence after minimum replicates
        if replicate_id >= config.min_replicates:
            # Calculate bootstrap CI
            lower, upper = bootstrap_ci(all_outcomes, n_bootstrap=1000, alpha=0.05)
            ci_width = upper - lower
            
            if ci_width <= config.ci_width_threshold:
                converged = True
                break
    
    # Final write
    if pvalues:
        save_raw_pvalues(
            raw_pvalues_file,
            pvalues,
            sample_size,
            distribution_type,
            test_type,
            hypothesis_type,
            0
        )
    
    # Calculate final statistics
    observed_alpha = np.mean(all_outcomes) if hypothesis_type == 'null' else 0.0
    observed_power = np.mean(all_outcomes) if hypothesis_type == 'alternative' else 0.0
    
    if len(all_outcomes) > 0:
        lower, upper = bootstrap_ci(all_outcomes, n_bootstrap=1000, alpha=0.05)
    else:
        lower, upper = 0.0, 0.0
    
    return AdaptiveRunResult(
        sample_size=sample_size,
        distribution_type=distribution_type,
        test_type=test_type,
        hypothesis_type=hypothesis_type,
        total_replicates=replicate_id,
        type_i_errors=sum(1 for o in all_outcomes if o == 1) if hypothesis_type == 'null' else 0,
        type_ii_errors=sum(1 for o in all_outcomes if o == 0) if hypothesis_type == 'alternative' else 0,
        observed_alpha=observed_alpha,
        observed_power=observed_power,
        ci_lower=lower,
        ci_upper=upper,
        ci_width=ci_width,
        converged=converged,
        raw_pvalues_file=raw_pvalues_file
    )

def run_full_simulation_batch(
    config: SimulationConfig,
    output_dir: str
) -> List[AdaptiveRunResult]:
    """Run full simulation batch for all configurations."""
    grid = get_simulation_grid(config)
    results = []
    
    for scenario in grid:
        logger.info(f"Running: {scenario}")
        result = run_adaptive_simulation(
            config,
            scenario['sample_size'],
            scenario['distribution_type'],
            scenario['test_type'],
            scenario['hypothesis_type'],
            output_dir
        )
        results.append(result)
        
        # Log validation for null hypothesis
        if scenario['hypothesis_type'] == 'null':
            valid = validate_type_i_error_rates(
                result.observed_alpha,
                config.alpha,
                tolerance=0.01
            )
            logger.info(f"Type I error validation: {'PASS' if valid else 'FAIL'} "
                      f"(observed={result.observed_alpha:.4f}, expected={config.alpha})")
    
    return results

def main():
    """Main entry point for simulation engine."""
    logging.basicConfig(level=logging.INFO)
    config = SimulationConfig()
    output_dir = 'data/processed'
    
    logger.info("Starting full simulation batch...")
    results = run_full_simulation_batch(config, output_dir)
    
    logger.info(f"Completed {len(results)} simulation configurations")
    for r in results:
        logger.info(f"  {r.test_type} ({r.distribution_type}, n={r.sample_size}): "
                  f"alpha={r.observed_alpha:.4f}, power={r.observed_power:.4f}")

if __name__ == '__main__':
    main()
