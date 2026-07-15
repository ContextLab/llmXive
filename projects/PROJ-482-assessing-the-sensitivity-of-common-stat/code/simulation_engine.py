import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, List, Optional
import logging
import os
import csv
import hashlib
from dataclasses import dataclass

from data_generator import generate_data

logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    sample_sizes: List[int]
    distributions: List[str]
    test_types: List[str]
    effect_sizes: List[float]
    hypothesis_types: List[str]
    alpha: float = 0.05
    min_replicates: int = 1000
    max_replicates: int = 50000
    ci_width_target: float = 0.01

def clopper_pearson_interval(successes: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Calculate Clopper-Pearson exact confidence interval for a binomial proportion."""
    if n == 0:
        return 0.0, 0.0
    if successes == 0:
        lower = 0.0
    else:
        lower = stats.beta.ppf(alpha / 2, successes, n - successes + 1)
    
    if successes == n:
        upper = 1.0
    else:
        upper = stats.beta.ppf(1 - alpha / 2, successes + 1, n - successes)
    
    return lower, upper

def execute_t_test(group1: np.ndarray, group2: np.ndarray) -> float:
    """Execute independent samples t-test and return p-value."""
    _, p_value = stats.ttest_ind(group1, group2)
    return p_value

def execute_anova(groups: List[np.ndarray]) -> float:
    """Execute one-way ANOVA and return p-value."""
    _, p_value = stats.f_oneway(*groups)
    return p_value

def execute_chi_squared(observed: np.ndarray) -> float:
    """Execute Chi-squared test and return p-value."""
    # Ensure observed is 2D for chi2_contingency
    if observed.ndim == 1:
        observed = observed.reshape(1, -1)
    _, p_value, _, _ = stats.chi2_contingency(observed)
    return p_value

def execute_fisher_exact(observed: np.ndarray) -> float:
    """Execute Fisher's Exact test and return p-value."""
    # Ensure observed is 2x2
    if observed.shape != (2, 2):
        raise ValueError("Fisher's Exact test requires a 2x2 contingency table")
    _, p_value = stats.fisher_exact(observed)
    return p_value

def execute_fisher_exact_from_table(counts: Dict[str, Dict[str, int]]) -> float:
    """Execute Fisher's Exact test from a dictionary representation of a 2x2 table."""
    table = np.array([
        [counts['group1']['success'], counts['group1']['failure']],
        [counts['group2']['success'], counts['group2']['failure']]
    ])
    return execute_fisher_exact(table)

def generate_scenario_data(
    sample_size: int,
    distribution_type: str,
    effect_size: float,
    hypothesis_type: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate data for a specific scenario."""
    # If hypothesis is null, effect_size should be 0
    if hypothesis_type == 'null':
        effect_size = 0.0
    
    group1, group2 = generate_data(
        n=sample_size,
        distribution_type=distribution_type,
        effect_size=effect_size
    )
    return group1, group2

def run_single_test_replicate(
    group1: np.ndarray,
    group2: np.ndarray,
    test_type: str
) -> float:
    """Run a single statistical test and return the p-value."""
    if test_type == 't_test':
        return execute_t_test(group1, group2)
    elif test_type == 'anova':
        # ANOVA expects multiple groups, but for 2-group comparison it's equivalent to t-test
        return execute_anova([group1, group2])
    elif test_type == 'chi_squared':
        # Convert continuous data to categorical for Chi-squared
        # Use median split to create 2x2 contingency table
        combined = np.concatenate([group1, group2])
        median_val = np.median(combined)
        
        # Create contingency table
        # Rows: Group 1, Group 2
        # Cols: Below Median, Above Median
        table = np.array([
            [np.sum(group1 <= median_val), np.sum(group1 > median_val)],
            [np.sum(group2 <= median_val), np.sum(group2 > median_val)]
        ])
        return execute_chi_squared(table)
    elif test_type == 'fisher_exact':
        # Similar to chi_squared but use Fisher's Exact for small counts
        combined = np.concatenate([group1, group2])
        median_val = np.median(combined)
        
        table = np.array([
            [np.sum(group1 <= median_val), np.sum(group1 > median_val)],
            [np.sum(group2 <= median_val), np.sum(group2 > median_val)]
        ])
        
        # Check expected cell counts
        row_totals = table.sum(axis=1)
        col_totals = table.sum(axis=0)
        total = table.sum()
        expected = np.outer(row_totals, col_totals) / total
        
        if np.any(expected < 5):
            return execute_fisher_exact(table)
        else:
            return execute_chi_squared(table)
    else:
        raise ValueError(f"Unknown test type: {test_type}")

def run_adaptive_simulation(
    config: SimulationConfig,
    sample_size: int,
    distribution_type: str,
    test_type: str,
    hypothesis_type: str,
    effect_size: float
) -> Dict[str, Any]:
    """Run adaptive Monte Carlo simulation for a single scenario."""
    logger.info(f"Running adaptive simulation: n={sample_size}, dist={distribution_type}, "
               f"test={test_type}, hyp={hypothesis_type}, effect={effect_size}")
    
    successes = 0
    total_reps = 0
    p_values = []
    
    # Adaptive loop
    current_replicates = config.min_replicates
    max_reps = config.max_replicates
    
    while total_reps < max_reps:
        # Run batch of replicates
        batch_size = min(1000, max_reps - total_reps)
        batch_p_values = []
        
        for _ in range(batch_size):
            group1, group2 = generate_scenario_data(
                sample_size, distribution_type, effect_size, hypothesis_type
            )
            p_val = run_single_test_replicate(group1, group2, test_type)
            batch_p_values.append(p_val)
            
            # Check if we reject null (p < alpha)
            if p_val < config.alpha:
                successes += 1
            
            total_reps += 1
        
        p_values.extend(batch_p_values)
        
        # Calculate CI width for adaptive control (using Clopper-Pearson)
        if total_reps >= config.min_replicates:
            prop = successes / total_reps
            lower, upper = clopper_pearson_interval(successes, total_reps, config.alpha)
            ci_width = upper - lower
            
            if ci_width <= config.ci_width_target:
                logger.info(f"CI width {ci_width:.4f} <= target {config.ci_width_target:.4f} "
                           f"at {total_reps} replicates. Stopping.")
                break
        
        # If we've reached minimum replicates and CI is still wide, continue
        if total_reps >= config.min_replicates and ci_width > config.ci_width_target:
            # Increase batch size for next iteration if needed
            pass
    
    # Calculate final error rate
    error_rate = successes / total_reps if total_reps > 0 else 0.0
    
    return {
        'sample_size': sample_size,
        'distribution_type': distribution_type,
        'test_type': test_type,
        'hypothesis_type': hypothesis_type,
        'effect_size': effect_size,
        'total_replicates': total_reps,
        'successes': successes,
        'error_rate': error_rate,
        'p_values': p_values
    }

def count_type_i_and_type_ii_errors(
    p_values: List[float],
    hypothesis_type: str,
    alpha: float = 0.05
) -> Tuple[int, int]:
    """
    Count Type I and Type II errors based on p-values and hypothesis type.
    
    Type I Error: Rejecting true null hypothesis (p < alpha when hypothesis is 'null')
    Type II Error: Failing to reject false null hypothesis (p >= alpha when hypothesis is 'alternative')
    """
    type_i_count = 0
    type_ii_count = 0
    
    for p_val in p_values:
        if hypothesis_type == 'null':
            # True null: rejection is Type I error
            if p_val < alpha:
                type_i_count += 1
        elif hypothesis_type == 'alternative':
            # False null: failure to reject is Type II error
            if p_val >= alpha:
                type_ii_count += 1
        else:
            raise ValueError(f"Unknown hypothesis type: {hypothesis_type}")
    
    return type_i_count, type_ii_count

def save_raw_pvalues(
    p_values_data: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save raw p-values to a CSV file.
    
    Args:
        p_values_data: List of dictionaries containing p-value information
        output_path: Path to the output CSV file
    """
    if not p_values_data:
        logger.warning("No p-values to save.")
        return
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define schema columns
    fieldnames = ['sample_size', 'distribution_type', 'test_type', 'p_value', 'hypothesis_type']
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in p_values_data:
            writer.writerow({
                'sample_size': row['sample_size'],
                'distribution_type': row['distribution_type'],
                'test_type': row['test_type'],
                'p_value': row['p_value'],
                'hypothesis_type': row['hypothesis_type']
            })
    
    logger.info(f"Saved {len(p_values_data)} raw p-values to {output_path}")

def save_error_counts(
    error_counts_data: List[Dict[str, Any]],
    output_path: str
) -> None:
    """Save aggregated error counts to a CSV file."""
    if not error_counts_data:
        logger.warning("No error counts to save.")
        return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['sample_size', 'distribution_type', 'test_type', 
                 'hypothesis_type', 'type_i_count', 'type_ii_count', 
                 'total_replicates', 'error_rate']
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in error_counts_data:
            writer.writerow(row)
    
    logger.info(f"Saved error counts to {output_path}")

def run_full_simulation_batch(
    config: SimulationConfig,
    output_dir: str = 'data/processed'
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Run the full simulation batch across all configurations.
    
    Returns:
        Tuple of (error_counts_data, p_values_data)
    """
    error_counts_data = []
    p_values_data = []
    
    for sample_size in config.sample_sizes:
        for distribution_type in config.distributions:
            for test_type in config.test_types:
                for hypothesis_type in config.hypothesis_types:
                    # Determine effect size based on hypothesis type
                    if hypothesis_type == 'null':
                        effect_size = 0.0
                    else:
                        # Use the first effect size from config for alternative
                        effect_size = config.effect_sizes[0] if config.effect_sizes else 0.5
                    
                    # Run simulation
                    result = run_adaptive_simulation(
                        config, sample_size, distribution_type, 
                        test_type, hypothesis_type, effect_size
                    )
                    
                    # Count errors
                    type_i, type_ii = count_type_i_and_type_ii_errors(
                        result['p_values'], hypothesis_type, config.alpha
                    )
                    
                    # Prepare error counts record
                    error_record = {
                        'sample_size': result['sample_size'],
                        'distribution_type': result['distribution_type'],
                        'test_type': result['test_type'],
                        'hypothesis_type': result['hypothesis_type'],
                        'type_i_count': type_i,
                        'type_ii_count': type_ii,
                        'total_replicates': result['total_replicates'],
                        'error_rate': result['error_rate']
                    }
                    error_counts_data.append(error_record)
                    
                    # Prepare raw p-values records
                    for p_val in result['p_values']:
                        p_values_data.append({
                            'sample_size': result['sample_size'],
                            'distribution_type': result['distribution_type'],
                            'test_type': result['test_type'],
                            'p_value': p_val,
                            'hypothesis_type': result['hypothesis_type']
                        })
    
    # Save results
    error_counts_path = os.path.join(output_dir, 'error_counts.csv')
    raw_pvalues_path = os.path.join(output_dir, 'raw_pvalues.csv')
    
    save_error_counts(error_counts_data, error_counts_path)
    save_raw_pvalues(p_values_data, raw_pvalues_path)
    
    return error_counts_data, p_values_data

def main():
    """Main entry point for simulation engine."""
    logging.basicConfig(level=logging.INFO)
    
    # Create a sample configuration for testing
    config = SimulationConfig(
        sample_sizes=[10, 50, 100],
        distributions=['normal', 'uniform', 'log_normal'],
        test_types=['t_test', 'anova', 'chi_squared'],
        effect_sizes=[0.5],
        hypothesis_types=['null', 'alternative'],
        alpha=0.05,
        min_replicates=100,  # Reduced for testing
        max_replicates=1000,
        ci_width_target=0.01
    )
    
    # Run simulation
    error_counts, p_values = run_full_simulation_batch(config)
    
    logger.info(f"Simulation complete. Processed {len(p_values)} p-values.")

if __name__ == '__main__':
    main()
