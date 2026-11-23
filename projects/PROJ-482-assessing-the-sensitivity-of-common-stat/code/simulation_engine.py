import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, List, Optional, Callable
import logging
import os
import csv
import time
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from pathlib import Path
import json

from config import SimulationConfig, get_simulation_grid
from data_generator import generate_normal, generate_uniform, generate_log_normal
from utils.file_lock import file_lock, write_pvalue_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SimulationResult:
    sample_size: int
    distribution_type: str
    test_type: str
    hypothesis_type: str  # 'null' or 'alternative'
    p_value: float
    rejection: bool
    effect_size: float

@dataclass
class AdaptiveRunResult:
    sample_size: int
    distribution_type: str
    test_type: str
    hypothesis_type: str
    observed_error_rate: float
    ci_lower: float
    ci_upper: float
    n_replicates: int
    is_stable: bool

def bootstrap_ci(outcomes: List[int], n_resamples: int = 1000, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for binary outcomes.
    
    Args:
        outcomes: List of binary outcomes (0 or 1)
        n_resamples: Number of bootstrap resamples
        alpha: Significance level for CI (default 0.05 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if not outcomes:
        return (0.0, 0.0)
    
    n = len(outcomes)
    bootstrap_means = []
    
    for _ in range(n_resamples):
        resample = np.random.choice(outcomes, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    bootstrap_means.sort()
    lower_idx = int(alpha / 2 * n_resamples)
    upper_idx = int((1 - alpha / 2) * n_resamples)
    
    return (bootstrap_means[lower_idx], bootstrap_means[upper_idx])

def generate_scenario_data(sample_size: int, distribution_type: str, 
                            effect_size: float, hypothesis_type: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate data for a simulation scenario.
    
    Args:
        sample_size: Number of samples per group
        distribution_type: 'normal', 'uniform', or 'log_normal'
        effect_size: Effect size (0.0 for null, 0.5 for alternative)
        hypothesis_type: 'null' or 'alternative'
    
    Returns:
        Tuple of (group1, group2) arrays
    """
    # Adjust effect size based on hypothesis type
    if hypothesis_type == 'null':
        actual_effect = 0.0
    else:
        actual_effect = effect_size
    
    if distribution_type == 'normal':
        group1, group2 = generate_normal(sample_size, actual_effect)
    elif distribution_type == 'uniform':
        group1, group2 = generate_uniform(sample_size, actual_effect)
    elif distribution_type == 'log_normal':
        group1, group2 = generate_log_normal(sample_size, actual_effect)
    else:
        raise ValueError(f"Unknown distribution type: {distribution_type}")
    
    return group1, group2

def execute_t_test(group1: np.ndarray, group2: np.ndarray) -> float:
    """Execute independent t-test and return p-value."""
    _, p_value = stats.ttest_ind(group1, group2)
    return p_value

def execute_anova(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Execute one-way ANOVA and return p-value.
    
    NOTE: This function explicitly enforces equal group sizes to ensure
    validity of theoretical power curve comparisons (T027c-3).
    
    Args:
        group1: First group data
        group2: Second group data
    
    Returns:
        p-value from ANOVA test
    """
    # T040: Verify and enforce equal group sizes for ANOVA
    n1 = len(group1)
    n2 = len(group2)
    
    if n1 != n2:
        # Log warning and trim to equal sizes
        min_n = min(n1, n2)
        logger.warning(
            f"ANOVA detected unequal group sizes (n1={n1}, n2={n2}). "
            f"Trimming to equal size n={min_n} to ensure theoretical validity."
        )
        group1 = group1[:min_n]
        group2 = group2[:min_n]
    
    _, p_value = stats.f_oneway(group1, group2)
    return p_value

def execute_chi_squared(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Execute Chi-squared test (binarized data) and return p-value.
    Triggers Fisher's Exact for small expected counts.
    """
    # Binarize data based on median split for Chi-squared
    combined = np.concatenate([group1, group2])
    median_val = np.median(combined)
    
    group1_bin = (group1 > median_val).astype(int)
    group2_bin = (group2 > median_val).astype(int)
    
    # Create contingency table
    table = np.array([
        [np.sum(group1_bin), len(group1_bin) - np.sum(group1_bin)],
        [np.sum(group2_bin), len(group2_bin) - np.sum(group2_bin)]
    ])
    
    # Check expected counts for Fisher's Exact trigger
    chi2, p_value, dof, expected = stats.chi2_contingency(table, correction=False)
    
    if np.any(expected < 5):
        # Use Fisher's Exact for small counts
        _, p_value = stats.fisher_exact(table)
    
    return p_value

def run_single_test_replicate(sample_size: int, distribution_type: str, 
                               test_type: str, effect_size: float, 
                               hypothesis_type: str) -> SimulationResult:
    """Run a single replicate of a statistical test."""
    group1, group2 = generate_scenario_data(sample_size, distribution_type, 
                                             effect_size, hypothesis_type)
    
    if test_type == 't_test':
        p_value = execute_t_test(group1, group2)
    elif test_type == 'anova':
        p_value = execute_anova(group1, group2)
    elif test_type == 'chi_squared':
        p_value = execute_chi_squared(group1, group2)
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    rejection = p_value < 0.05
    
    return SimulationResult(
        sample_size=sample_size,
        distribution_type=distribution_type,
        test_type=test_type,
        hypothesis_type=hypothesis_type,
        p_value=p_value,
        rejection=rejection,
        effect_size=effect_size
    )

def count_type_i_and_type_ii_errors(results: List[SimulationResult], alpha: float = 0.05) -> Dict[str, int]:
    """Count Type I and Type II errors from simulation results."""
    type_i = 0
    type_ii = 0
    null_count = 0
    alt_count = 0
    
    for res in results:
        if res.hypothesis_type == 'null':
            null_count += 1
            if res.rejection:
                type_i += 1
        else:
            alt_count += 1
            if not res.rejection:
                type_ii += 1
    
    return {
        'type_i': type_i,
        'type_ii': type_ii,
        'null_count': null_count,
        'alt_count': alt_count,
        'type_i_rate': type_i / null_count if null_count > 0 else 0.0,
        'type_ii_rate': type_ii / alt_count if alt_count > 0 else 0.0
    }

def save_raw_pvalues(results: List[SimulationResult], output_path: str):
    """
    Stream and save raw p-values to CSV.
    
    Args:
        results: List of SimulationResult objects
        output_path: Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with file_lock(output_path, 'a') as f:
        # Write header if file is new
        if f.tell() == 0:
            writer = csv.writer(f)
            writer.writerow(['sample_size', 'distribution_type', 'test_type', 
                             'p_value', 'hypothesis_type'])
        
        writer = csv.writer(f)
        for res in results:
            writer.writerow([
                res.sample_size,
                res.distribution_type,
                res.test_type,
                res.p_value,
                res.hypothesis_type
            ])

def run_adaptive_simulation(sample_size: int, distribution_type: str, 
                             test_type: str, effect_size: float, 
                             hypothesis_type: str, 
                             min_replicates: int = 1000, 
                             max_replicates: int = 10000,
                             ci_width_threshold: float = 0.01) -> AdaptiveRunResult:
    """
    Run adaptive Monte Carlo simulation with bootstrap CI.
    
    Args:
        sample_size: Number of samples per group
        distribution_type: Distribution type
        test_type: Statistical test type
        effect_size: Effect size
        hypothesis_type: 'null' or 'alternative'
        min_replicates: Minimum number of replicates
        max_replicates: Maximum number of replicates
        ci_width_threshold: Target CI width for stability
    
    Returns:
        AdaptiveRunResult with error rate and CI
    """
    outcomes = []
    n_replicates = min_replicates
    
    logger.info(f"Starting adaptive simulation: n={sample_size}, dist={distribution_type}, "
               f"test={test_type}, hyp={hypothesis_type}")
    
    # Initial batch
    for _ in range(n_replicates):
        res = run_single_test_replicate(sample_size, distribution_type, test_type, 
                                         effect_size, hypothesis_type)
        outcomes.append(1 if res.rejection else 0)
    
    # Adaptive loop
    while n_replicates < max_replicates:
        ci_lower, ci_upper = bootstrap_ci(outcomes, n_resamples=1000)
        ci_width = ci_upper - ci_lower
        
        if ci_width <= ci_width_threshold:
            break
        
        # Add more replicates
        additional = min(1000, max_replicates - n_replicates)
        for _ in range(additional):
            res = run_single_test_replicate(sample_size, distribution_type, test_type, 
                                             effect_size, hypothesis_type)
            outcomes.append(1 if res.rejection else 0)
        n_replicates += additional
    
    # Final CI calculation
    ci_lower, ci_upper = bootstrap_ci(outcomes, n_resamples=1000)
    observed_rate = np.mean(outcomes)
    is_stable = (ci_upper - ci_lower) <= ci_width_threshold
    
    if not is_stable:
        logger.warning(f"UNSTABLE: CI width {(ci_upper - ci_lower):.4f} > {ci_width_threshold} "
                      f"after {n_replicates} replicates")
    
    return AdaptiveRunResult(
        sample_size=sample_size,
        distribution_type=distribution_type,
        test_type=test_type,
        hypothesis_type=hypothesis_type,
        observed_error_rate=observed_rate,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        n_replicates=n_replicates,
        is_stable=is_stable
    )

def validate_type_i_error_rates(results: List[AdaptiveRunResult], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """Validate observed Type I error rates against theoretical alpha."""
    validation_results = []
    
    for res in results:
        if res.hypothesis_type == 'null':
            diff = abs(res.observed_error_rate - alpha)
            validation_results.append({
                'sample_size': res.sample_size,
                'distribution_type': res.distribution_type,
                'test_type': res.test_type,
                'theoretical_alpha': alpha,
                'observed_rate': res.observed_error_rate,
                'difference': diff,
                'within_tolerance': diff < 0.01
            })
    
    return validation_results

def run_full_simulation_batch(config: SimulationConfig, output_dir: str = 'data/processed'):
    """Run full simulation batch across all configurations."""
    os.makedirs(output_dir, exist_ok=True)
    
    grid = get_simulation_grid(config)
    all_results = []
    raw_pvalues = []
    
    logger.info(f"Starting full simulation batch with {len(grid)} configurations")
    
    for scenario in grid:
        logger.info(f"Running scenario: {scenario}")
        
        result = run_adaptive_simulation(
            sample_size=scenario['sample_size'],
            distribution_type=scenario['distribution_type'],
            test_type=scenario['test_type'],
            effect_size=scenario['effect_size'],
            hypothesis_type=scenario['hypothesis_type'],
            min_replicates=config.min_replicates,
            max_replicates=config.max_replicates,
            ci_width_threshold=config.ci_width_threshold
        )
        
        all_results.append(result)
        
        # Generate raw p-values for this scenario
        pvalues = []
        for _ in range(result.n_replicates):
            sim_res = run_single_test_replicate(
                scenario['sample_size'],
                scenario['distribution_type'],
                scenario['test_type'],
                scenario['effect_size'],
                scenario['hypothesis_type']
            )
            pvalues.append(sim_res)
            raw_pvalues.append(sim_res)
        
        # Save raw p-values periodically
        if len(raw_pvalues) >= 10000:
            save_raw_pvalues(raw_pvalues, os.path.join(output_dir, 'raw_pvalues.csv'))
            raw_pvalues = []
    
    # Save remaining p-values
    if raw_pvalues:
        save_raw_pvalues(raw_pvalues, os.path.join(output_dir, 'raw_pvalues.csv'))
    
    # Save adaptive results
    results_df = pd.DataFrame([
        {
            'sample_size': r.sample_size,
            'distribution_type': r.distribution_type,
            'test_type': r.test_type,
            'hypothesis_type': r.hypothesis_type,
            'observed_error_rate': r.observed_error_rate,
            'ci_lower': r.ci_lower,
            'ci_upper': r.ci_upper,
            'n_replicates': r.n_replicates,
            'is_stable': r.is_stable
        }
        for r in all_results
    ])
    
    results_df.to_csv(os.path.join(output_dir, 'simulation_results.csv'), index=False)
    
    # Validate Type I error rates
    validation = validate_type_i_error_rates(all_results)
    validation_df = pd.DataFrame(validation)
    validation_df.to_csv(os.path.join(output_dir, 'validation_report.csv'), index=False)
    
    logger.info(f"Simulation batch complete. Results saved to {output_dir}")
    return all_results

def main():
    """Main entry point for simulation engine."""
    config = SimulationConfig(
        sample_sizes=[10, 20, 50, 100, 200, 500, 1000],
        distributions=['normal', 'uniform', 'log_normal'],
        test_types=['t_test', 'anova', 'chi_squared'],
        effect_sizes=[0.0, 0.5],
        hypothesis_types=['null', 'alternative'],
        min_replicates=1000,
        max_replicates=10000,
        ci_width_threshold=0.01,
        alpha=0.05
    )
    
    run_full_simulation_batch(config)

if __name__ == '__main__':
    main()