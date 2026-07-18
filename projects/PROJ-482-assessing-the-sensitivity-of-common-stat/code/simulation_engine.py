import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, List, Optional
import logging
import os
import csv
from config import SimulationConfig, get_simulation_grid, get_test_grid

logger = logging.getLogger(__name__)

def clopper_pearson_interval(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate the Clopper-Pearson exact confidence interval for a binomial proportion.
    
    Args:
        k: Number of successes
        n: Number of trials
        alpha: Significance level (default 0.05 for 95% CI)
        
    Returns:
        Tuple (lower_bound, upper_bound)
    """
    if n == 0:
        return (0.0, 0.0)
    if k == 0:
        lower = 0.0
    else:
        lower = stats.beta.ppf(alpha / 2, k, n - k + 1)
    if k == n:
        upper = 1.0
    else:
        upper = stats.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return (lower, upper)

def execute_t_test(group1: np.ndarray, group2: np.ndarray) -> float:
    """Execute an independent samples t-test."""
    _, p_value = stats.ttest_ind(group1, group2)
    return p_value

def execute_anova(groups: List[np.ndarray]) -> float:
    """Execute a one-way ANOVA."""
    if len(groups) < 2:
        return 1.0
    _, p_value = stats.f_oneway(*groups)
    return p_value

def execute_chi_squared(observed: np.ndarray) -> float:
    """Execute a Chi-squared test."""
    try:
        _, p_value, _, _ = stats.chi2_contingency(observed)
        return p_value
    except Exception:
        return 1.0

def execute_fisher_exact(observed: np.ndarray) -> float:
    """Execute Fisher's Exact test."""
    try:
        _, p_value = stats.fisher_exact(observed)
        return p_value
    except Exception:
        return 1.0

def execute_fisher_exact_from_table(table: List[List[int]]) -> float:
    """Execute Fisher's Exact test from a 2x2 contingency table."""
    try:
        _, p_value = stats.fisher_exact(table)
        return p_value
    except Exception:
        return 1.0

def generate_scenario_data(
    sample_size: int,
    distribution_type: str,
    effect_size: float,
    hypothesis_type: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate data for a specific scenario.
    
    Args:
        sample_size: Number of samples per group
        distribution_type: 'normal', 'uniform', or 'log_normal'
        effect_size: The ground truth effect size (0.0 for null, >0 for alternative)
        hypothesis_type: 'null' or 'alternative'
        
    Returns:
        Tuple of (group1, group2) arrays
    """
    from data_generator import generate_normal, generate_uniform, generate_log_normal
    
    # Determine the actual effect size based on hypothesis
    actual_effect = 0.0 if hypothesis_type == 'null' else effect_size
    
    if distribution_type == 'normal':
        g1, g2 = generate_normal(sample_size, actual_effect)
    elif distribution_type == 'uniform':
        g1, g2 = generate_uniform(sample_size, actual_effect)
    elif distribution_type == 'log_normal':
        g1, g2 = generate_log_normal(sample_size, actual_effect)
    else:
        raise ValueError(f"Unknown distribution type: {distribution_type}")
        
    return g1, g2

def run_single_test_replicate(
    sample_size: int,
    distribution_type: str,
    test_type: str,
    effect_size: float,
    hypothesis_type: str,
    config: SimulationConfig
) -> float:
    """
    Run a single replicate of a statistical test.
    
    Args:
        sample_size: Number of samples per group
        distribution_type: 'normal', 'uniform', or 'log_normal'
        test_type: 't_test', 'anova', 'chi_squared', 'fisher_exact'
        effect_size: Ground truth effect size
        hypothesis_type: 'null' or 'alternative'
        config: Simulation configuration
        
    Returns:
        p_value from the test
    """
    g1, g2 = generate_scenario_data(sample_size, distribution_type, effect_size, hypothesis_type)
    
    if test_type == 't_test':
        return execute_t_test(g1, g2)
    elif test_type == 'anova':
        # ANOVA expects multiple groups, but for 2 groups it's equivalent to t-test squared
        return execute_anova([g1, g2])
    elif test_type == 'chi_squared':
        # Convert continuous data to categorical for chi-squared
        # Bin into 2 categories: below/above median
        combined = np.concatenate([g1, g2])
        median_val = np.median(combined)
        counts_g1 = np.sum(g1 <= median_val)
        counts_g2 = np.sum(g2 <= median_val)
        # Create 2x2 table: [counts <= median, counts > median] for each group
        observed = np.array([
            [counts_g1, sample_size - counts_g1],
            [counts_g2, sample_size - counts_g2]
        ])
        return execute_chi_squared(observed)
    elif test_type == 'fisher_exact':
        # Similar binning for Fisher's Exact
        combined = np.concatenate([g1, g2])
        median_val = np.median(combined)
        counts_g1 = np.sum(g1 <= median_val)
        counts_g2 = np.sum(g2 <= median_val)
        observed = [
            [counts_g1, sample_size - counts_g1],
            [counts_g2, sample_size - counts_g2]
        ]
        return execute_fisher_exact_from_table(observed)
    else:
        raise ValueError(f"Unknown test type: {test_type}")

def save_raw_pvalues(
    p_values: List[Tuple[int, str, str, float, str]],
    output_path: str
) -> None:
    """
    Save raw p-values to a CSV file.
    
    Args:
        p_values: List of tuples (sample_size, distribution_type, test_type, p_value, hypothesis_type)
        output_path: Path to the output CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['sample_size', 'distribution_type', 'test_type', 'p_value', 'hypothesis_type'])
        for row in p_values:
            writer.writerow(row)
    
    logger.info(f"Saved {len(p_values)} raw p-values to {output_path}")

def count_type_i_and_type__errors(
    raw_pvalues_path: str,
    output_path: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Count Type I and Type II errors from raw p-values.
    
    Type I Error: Rejecting a true null hypothesis (p < alpha when hypothesis_type == 'null')
    Type II Error: Failing to reject a false null hypothesis (p >= alpha when hypothesis_type == 'alternative')
    
    Args:
        raw_pvalues_path: Path to the raw p-values CSV file
        output_path: Path to write the error counts CSV
        alpha: Significance level
        
    Returns:
        Dictionary with aggregated counts
    """
    import pandas as pd
    
    df = pd.read_csv(raw_pvalues_path)
    
    # Initialize counters
    counts = {}
    
    for (n, dist, test, hyp), group in df.groupby(['sample_size', 'distribution_type', 'test_type', 'hypothesis_type']):
        key = (n, dist, test, hyp)
        p_vals = group['p_value'].values
        total = len(p_vals)
        
        if hyp == 'null':
            # Type I error: reject true null (p < alpha)
            type_i = np.sum(p_vals < alpha)
            counts[key] = {
                'total_replicates': total,
                'type_i_errors': int(type_i),
                'type_ii_errors': 0,
                'observed_alpha': type_i / total if total > 0 else 0.0
            }
        else:  # hypothesis_type == 'alternative'
            # Type II error: fail to reject false null (p >= alpha)
            type_ii = np.sum(p_vals >= alpha)
            counts[key] = {
                'total_replicates': total,
                'type_i_errors': 0,
                'type_ii_errors': int(type_ii),
                'observed_power': 1.0 - (type_ii / total) if total > 0 else 0.0
            }
    
    # Write to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['sample_size', 'distribution_type', 'test_type', 'hypothesis_type', 
                       'total_replicates', 'type_i_errors', 'type_ii_errors', 'observed_rate'])
        
        for (n, dist, test, hyp), data in counts.items():
            if hyp == 'null':
                rate = data['observed_alpha']
                writer.writerow([n, dist, test, hyp, data['total_replicates'], 
                               data['type_i_errors'], 0, f"{rate:.6f}"])
            else:
                rate = data['observed_power']
                writer.writerow([n, dist, test, hyp, data['total_replicates'], 
                               0, data['type_ii_errors'], f"{rate:.6f}"])
    
    logger.info(f"Error counts written to {output_path}")
    return counts

def validate_type_i_error_rates(
    error_counts_path: str,
    output_path: str,
    alpha: float = 0.05
) -> None:
    """
    Validate observed Type I error rates against theoretical alpha.
    
    Args:
        error_counts_path: Path to the error counts CSV
        output_path: Path to write the validation report
        alpha: Theoretical significance level
    """
    import pandas as pd
    
    df = pd.read_csv(error_counts_path)
    null_df = df[df['hypothesis_type'] == 'null']
    
    report_data = []
    for _, row in null_df.iterrows():
        observed = float(row['observed_rate'])
        diff = abs(observed - alpha)
        report_data.append({
            'sample_size': row['sample_size'],
            'distribution_type': row['distribution_type'],
            'test_type': row['test_type'],
            'theoretical_alpha': alpha,
            'observed_rate': observed,
            'difference': diff
        })
    
    report_df = pd.DataFrame(report_data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    report_df.to_csv(output_path, index=False)
    
    logger.info(f"Validation report written to {output_path}")

def run_adaptive_simulation(
    scenario: Dict[str, Any],
    config: SimulationConfig
) -> Tuple[List[Tuple[int, str, str, float, str]], int]:
    """
    Run an adaptive simulation for a single scenario.
    
    Args:
        scenario: Dictionary with sample_size, distribution_type, test_type, effect_size, hypothesis_type
        config: Simulation configuration
        
    Returns:
        Tuple of (list of p-value records, total replicates)
    """
    sample_size = scenario['sample_size']
    distribution_type = scenario['distribution_type']
    test_type = scenario['test_type']
    effect_size = scenario['effect_size']
    hypothesis_type = scenario['hypothesis_type']
    
    p_values = []
    n_replicates = 0
    min_replicates = 1000
    max_replicates = config.MAX_REPLICATES
    target_ci_width = 0.01
    
    # Run initial batch
    while n_replicates < min_replicates and n_replicates < max_replicates:
        p_val = run_single_test_replicate(
            sample_size, distribution_type, test_type, effect_size, hypothesis_type, config
        )
        p_values.append((sample_size, distribution_type, test_type, p_val, hypothesis_type))
        n_replicates += 1
    
    # Check convergence if we have enough data
    if n_replicates >= min_replicates:
        # Convert to binary outcomes (1 = reject null, 0 = fail to reject)
        outcomes = np.array([1 if p < config.ALPHA else 0 for p in [r[3] for r in p_values]])
        
        # Calculate current proportion
        p_hat = np.mean(outcomes)
        
        # Bootstrap CI width calculation
        bootstrap_means = []
        n_bootstrap = 1000
        for _ in range(n_bootstrap):
            sample = np.random.choice(outcomes, size=len(outcomes), replace=True)
            bootstrap_means.append(np.mean(sample))
        
        sorted_means = np.sort(bootstrap_means)
        lower_idx = int(0.025 * n_bootstrap)
        upper_idx = int(0.975 * n_bootstrap)
        ci_width = sorted_means[upper_idx] - sorted_means[lower_idx]
        
        # Continue if width is too large
        while ci_width > target_ci_width and n_replicates < max_replicates:
            p_val = run_single_test_replicate(
                sample_size, distribution_type, test_type, effect_size, hypothesis_type, config
            )
            p_values.append((sample_size, distribution_type, test_type, p_val, hypothesis_type))
            n_replicates += 1
            
            outcomes = np.array([1 if p < config.ALPHA else 0 for p in [r[3] for r in p_values]])
            bootstrap_means = []
            for _ in range(n_bootstrap):
                sample = np.random.choice(outcomes, size=len(outcomes), replace=True)
                bootstrap_means.append(np.mean(sample))
            
            sorted_means = np.sort(bootstrap_means)
            ci_width = sorted_means[upper_idx] - sorted_means[lower_idx]
            
            if n_replicates >= max_replicates:
                logger.warning(f"Reached max replicates ({max_replicates}) for scenario {scenario}")
                break
    
    return p_values, n_replicates

def run_full_simulation_batch(
    config: SimulationConfig,
    output_dir: str
) -> None:
    """
    Run the full simulation batch for all scenarios.
    
    Args:
        config: Simulation configuration
        output_dir: Directory to save results
    """
    scenarios = get_simulation_grid(config)
    all_p_values = []
    
    raw_pvalues_path = os.path.join(output_dir, 'raw_pvalues.csv')
    error_counts_path = os.path.join(output_dir, 'error_counts.csv')
    validation_report_path = os.path.join(output_dir, 'validation_report.csv')
    
    # Clear previous results
    if os.path.exists(raw_pvalues_path):
        os.remove(raw_pvalues_path)
    
    for scenario in scenarios:
        logger.info(f"Running scenario: {scenario}")
        p_values, n_reps = run_adaptive_simulation(scenario, config)
        all_p_values.extend(p_values)
        logger.info(f"Completed {n_reps} replicates for scenario {scenario}")
    
    # Save raw p-values
    save_raw_pvalues(all_p_values, raw_pvalues_path)
    
    # Count errors
    count_type_i_and_type_ii_errors(raw_pvalues_path, error_counts_path, config.ALPHA)
    
    # Validate Type I error rates
    validate_type_i_error_rates(error_counts_path, validation_report_path, config.ALPHA)

def main():
    """Main entry point for the simulation engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical test sensitivity simulations')
    parser.add_argument('--output-dir', type=str, default='data/processed',
                      help='Directory to save results')
    parser.add_argument('--config', type=str, default=None,
                      help='Path to configuration file (optional)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config = SimulationConfig()
    if args.config:
        # Load custom config if provided
        pass
    
    run_full_simulation_batch(config, args.output_dir)
    
    logger.info("Simulation batch completed successfully")

if __name__ == '__main__':
    main()