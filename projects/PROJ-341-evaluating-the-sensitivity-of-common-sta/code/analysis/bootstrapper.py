import os
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats
import pandas as pd

# Import from existing API surface
from code.simulation.output_writer import load_p_values_raw
from code.analysis.real_data_runner import load_prepared_data

def bootstrap_power_estimate(
    p_values: np.ndarray,
    alpha: float = 0.05,
    n_bootstrap: int = 1000,
    rng: Optional[np.random.Generator] = None
) -> Dict[str, Any]:
    """
    Perform bootstrapped power estimation on a set of p-values.
    
    Args:
        p_values: Array of p-values from real data analysis (e.g., from T031).
        alpha: Significance threshold.
        n_bootstrap: Number of bootstrap iterations.
        rng: Random number generator for reproducibility.
        
    Returns:
        Dictionary containing:
            - 'estimated_power': Mean power estimate
            - 'ci_lower': Lower bound of 95% CI
            - 'ci_upper': Upper bound of 95% CI
            - 'bootstrap_distribution': The distribution of power estimates
    """
    if rng is None:
        rng = np.random.default_rng(42)
        
    n = len(p_values)
    if n == 0:
        return {
            'estimated_power': 0.0,
            'ci_lower': 0.0,
            'ci_upper': 0.0,
            'bootstrap_distribution': []
        }
    
    # Calculate observed power (proportion of rejections)
    observed_power = np.mean(p_values < alpha)
    
    bootstrap_powers = []
    for _ in range(n_bootstrap):
        # Resample with replacement
        resample_indices = rng.choice(n, size=n, replace=True)
        resampled_p_values = p_values[resample_indices]
        resampled_power = np.mean(resampled_p_values < alpha)
        bootstrap_powers.append(resampled_power)
    
    bootstrap_powers = np.array(bootstrap_powers)
    
    return {
        'estimated_power': float(np.mean(bootstrap_powers)),
        'ci_lower': float(np.percentile(bootstrap_powers, 2.5)),
        'ci_upper': float(np.percentile(bootstrap_powers, 97.5)),
        'bootstrap_distribution': bootstrap_powers.tolist(),
        'observed_power': float(observed_power),
        'n_samples': n,
        'n_bootstrap': n_bootstrap
    }

def calculate_ks_distance(
    simulated_power_dist: List[float],
    real_power_dist: List[float]
) -> float:
    """
    Calculate the Kolmogorov-Smirnov distance between two distributions.
    
    Args:
        simulated_power_dist: Power distribution from simulation (T018/T020).
        real_power_dist: Bootstrapped power distribution from real data.
        
    Returns:
        KS statistic (distance between CDFs).
    """
    if not simulated_power_dist or not real_power_dist:
        return float('nan')
        
    ks_stat, _ = stats.ks_2samp(simulated_power_dist, real_power_dist)
    return float(ks_stat)

def load_simulated_power_distribution(
    error_rates_file: str = "data/simulation/error_rates_summary.csv",
    test_type: str = "t_test",
    effect_size: float = 0.5
) -> List[float]:
    """
    Load simulated power distribution from the aggregated error rates.
    Power = 1 - Type II error rate.
    
    Args:
        error_rates_file: Path to error_rates_summary.csv.
        test_type: Type of test (t_test, anova, chi_squared).
        effect_size: Effect size filter.
        
    Returns:
        List of power values across sample sizes for the specified condition.
    """
    df = pd.read_csv(error_rates_file)
    
    # Filter by test type and effect size
    mask = (df['test_type'] == test_type) & (np.isclose(df['effect_size'], effect_size))
    filtered_df = df[mask]
    
    if filtered_df.empty:
        return []
        
    # Power = 1 - Type II error rate
    # Note: In the simulation, Type II error is calculated when H1 is true.
    # We assume the 'type_ii_error_rate' column exists from T017/T018.
    if 'type_ii_error_rate' not in filtered_df.columns:
        # Fallback: if only Type I is present and we are under H1, 
        # we might need to infer. But per spec, T017 calculates both.
        return []
        
    power_values = 1.0 - filtered_df['type_ii_error_rate'].values
    return power_values.tolist()

def run_bootstrapped_validation(
    real_data_pvalues_file: str = "data/simulation/real_data_pvalues.csv",
    simulated_error_rates_file: str = "data/simulation/error_rates_summary.csv",
    alpha: float = 0.05,
    n_bootstrap: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Main orchestration function for T032.
    
    1. Loads real data p-values (from T031).
    2. Bootstraps power estimates for each test type in real data.
    3. Loads corresponding simulated power distributions.
    4. Calculates KS distance.
    5. Verifies KS <= 0.10.
    
    Args:
        real_data_pvalues_file: Output from T031.
        simulated_error_rates_file: Output from T018.
        alpha: Significance level.
        n_bootstrap: Bootstrap iterations.
        seed: Random seed.
        
    Returns:
        Dictionary of results for all test types.
    """
    rng = np.random.default_rng(seed)
    
    # Load real data p-values
    if not os.path.exists(real_data_pvalues_file):
        raise FileNotFoundError(f"Real data p-values file not found: {real_data_pvalues_file}")
        
    real_df = pd.read_csv(real_data_pvalues_file)
    
    results = {}
    test_types = real_df['test_type'].unique()
    
    for test_type in test_types:
        # Filter real p-values for this test type
        # Note: real_data_pvalues.csv might contain multiple datasets.
        # We aggregate all p-values for this test type to estimate overall power
        # in the context of the validation datasets.
        # However, power is typically defined per effect size. 
        # Since real data has "unknown" effect size, we treat the observed rejection rate
        # as the empirical power estimate for the specific dataset conditions.
        
        test_df = real_df[real_df['test_type'] == test_type]
        p_values = test_df['p_value'].values
        
        if len(p_values) == 0:
            continue
            
        # Bootstrap power estimate
        boot_result = bootstrap_power_estimate(
            p_values, 
            alpha=alpha, 
            n_bootstrap=n_bootstrap, 
            rng=rng
        )
        
        # Load simulated power distribution for comparison
        # We need to pick a representative effect size. 
        # For validation, we often compare against a medium effect size (0.5) 
        # or the one most similar to the real data's implicit effect.
        # Here we use 0.5 as a standard reference from the simulation grid.
        sim_power_dist = load_simulated_power_distribution(
            simulated_error_rates_file,
            test_type=test_type,
            effect_size=0.5
        )
        
        # If simulated distribution is empty (maybe no data for this effect size),
        # we try to find any available power distribution for this test type
        if not sim_power_dist:
            # Try to load from a range of effect sizes or just skip if no sim data
            # For this task, we assume the simulation ran for effect_size=0.5
            pass
        
        # Calculate KS distance
        ks_dist = calculate_ks_distance(sim_power_dist, boot_result['bootstrap_distribution'])
        
        # Verification
        is_valid = ks_dist <= 0.10 if not np.isnan(ks_dist) else False
        
        results[test_type] = {
            'bootstrap_power': boot_result,
            'simulated_power_distribution': sim_power_dist,
            'ks_distance': ks_dist,
            'is_valid': is_valid,
            'threshold': 0.10
        }
        
    return results

def save_power_results(
    results: Dict[str, Any],
    output_path: str = "data/simulation/real_data_power.json"
) -> None:
    """
    Save the bootstrapped power estimation and KS distance results.
    
    Args:
        results: Output from run_bootstrapped_validation.
        output_path: Path to the JSON output file.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Prepare serializable output
    # Convert numpy types and handle large lists if necessary
    serializable_results = {}
    for test_type, data in results.items():
        serializable_results[test_type] = {
            'bootstrap_power': {
                'estimated_power': data['bootstrap_power']['estimated_power'],
                'ci_lower': data['bootstrap_power']['ci_lower'],
                'ci_upper': data['bootstrap_power']['ci_upper'],
                'observed_power': data['bootstrap_power']['observed_power'],
                'n_samples': data['bootstrap_power']['n_samples'],
                'n_bootstrap': data['bootstrap_power']['n_bootstrap']
            },
            'ks_distance': data['ks_distance'],
            'is_valid': data['is_valid'],
            'threshold': data['threshold'],
            # Truncate distribution for readability if too large, 
            # but keep the stats. The prompt asks for the file, not necessarily the full array if huge.
            # We'll keep the full array as it's the 'distribution' but JSON handles it.
            'simulated_power_distribution_sample': data['simulated_power_distribution'][:100] if len(data['simulated_power_distribution']) > 100 else data['simulated_power_distribution']
        }
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)

def main():
    """
    Entry point for T032 execution.
    """
    print("Starting T032: Bootstrapped Power Estimation and KS Distance Validation")
    
    # Configuration
    real_data_file = "data/simulation/real_data_pvalues.csv"
    sim_error_rates_file = "data/simulation/error_rates_summary.csv"
    output_file = "data/simulation/real_data_power.json"
    alpha = 0.05
    n_bootstrap = 1000
    seed = 42
    
    try:
        results = run_bootstrapped_validation(
            real_data_pvalues_file=real_data_file,
            simulated_error_rates_file=sim_error_rates_file,
            alpha=alpha,
            n_bootstrap=n_bootstrap,
            seed=seed
        )
        
        save_power_results(results, output_file)
        
        print(f"Results saved to {output_file}")
        
        # Print summary
        for test_type, data in results.items():
            status = "PASS" if data['is_valid'] else "FAIL"
            print(f"Test: {test_type}, KS Distance: {data['ks_distance']:.4f} (Threshold: 0.10) -> {status}")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure T031 (real_data_pvalues.csv) and T018 (error_rates_summary.csv) have been completed.")
        raise
    except Exception as e:
        print(f"An error occurred during validation: {e}")
        raise

if __name__ == "__main__":
    main()