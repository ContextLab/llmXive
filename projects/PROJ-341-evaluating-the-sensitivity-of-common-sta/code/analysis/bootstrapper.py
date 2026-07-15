"""
Bootstrapper module for T032: Implement bootstrapped power estimation on real datasets.

This module calculates the Kolmogorov-Smirnov (KS) distance between real data
p-value distributions and simulated predictions to validate the simulation findings.
"""
import json
import os
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Constants
REAL_DATA_PVALUES_PATH = "data/simulation/real_data_pvalues.csv"
SIMULATED_POWER_PATH = "data/simulation/error_rates_summary.csv"
OUTPUT_PATH = "data/simulation/real_data_power.json"
KS_THRESHOLD = 0.10

def load_real_data_pvalues() -> pd.DataFrame:
    """
    Load p-values from real datasets.
    
    Returns:
        DataFrame with columns: dataset_name, test_type, p_value
        
    Raises:
        FileNotFoundError: If the real data p-values file does not exist.
        ValueError: If the file is empty or has no valid p-values.
    """
    if not os.path.exists(REAL_DATA_PVALUES_PATH):
        raise FileNotFoundError(
            f"Real data p-values file not found: {REAL_DATA_PVALUES_PATH}. "
            "Run T031 (real_data_runner) first to generate this file."
        )
    
    df = pd.read_csv(REAL_DATA_PVALUES_PATH)
    
    if df.empty:
        raise ValueError(
            f"Real data p-values file is empty: {REAL_DATA_PVALUES_PATH}. "
            "The validation step (T031) did not produce any results."
        )
    
    if 'p_value' not in df.columns:
        raise ValueError(
            f"Missing 'p_value' column in {REAL_DATA_PVALUES_PATH}. "
            f"Available columns: {list(df.columns)}"
        )
    
    # Filter out non-numeric or NaN values
    valid_df = df.dropna(subset=['p_value'])
    valid_df = valid_df[pd.to_numeric(valid_df['p_value'], errors='coerce').notna()]
    
    if valid_df.empty:
        raise ValueError(
            f"No valid p-values found in {REAL_DATA_PVALUES_PATH}. "
            "All values are NaN or non-numeric."
        )
    
    return valid_df

def load_simulated_power_distribution() -> pd.DataFrame:
    """
    Load simulated error rates to compare against real data.
    
    Returns:
        DataFrame with simulated error rates.
        
    Raises:
        FileNotFoundError: If the simulated error rates file does not exist.
    """
    if not os.path.exists(SIMULATED_POWER_PATH):
        raise FileNotFoundError(
            f"Simulated power distribution file not found: {SIMULATED_POWER_PATH}. "
            "Run T017 (aggregator) first to generate this file."
        )
    
    df = pd.read_csv(SIMULATED_POWER_PATH)
    if df.empty:
        raise ValueError(
            f"Simulated power distribution file is empty: {SIMULATED_POWER_PATH}."
        )
    return df

def bootstrap_power_estimate(
    p_values: pd.Series, 
    n_bootstraps: int = 1000, 
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Calculate bootstrapped power estimate from a set of p-values.
    
    Power is estimated as the proportion of p-values < alpha.
    Bootstrapping provides confidence intervals for this estimate.
    
    Args:
        p_values: Series of p-values.
        n_bootstraps: Number of bootstrap iterations.
        alpha: Significance threshold.
        
    Returns:
        Dictionary with 'power_estimate', 'ci_lower', 'ci_upper'.
    """
    n = len(p_values)
    if n == 0:
        raise ValueError("Cannot bootstrap with zero p-values.")
    
    # Calculate observed power (proportion of p < alpha)
    observed_power = (p_values < alpha).mean()
    
    # Bootstrap confidence intervals
    bootstrap_powers = []
    for _ in range(n_bootstraps):
        sample = p_values.sample(n=n, replace=True, random_state=None)
        boot_power = (sample < alpha).mean()
        bootstrap_powers.append(boot_power)
    
    bootstrap_powers = np.array(bootstrap_powers)
    ci_lower = np.percentile(bootstrap_powers, 2.5)
    ci_upper = np.percentile(bootstrap_powers, 97.5)
    
    return {
        'power_estimate': float(observed_power),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'n_samples': n,
        'n_bootstraps': n_bootstraps
    }

def calculate_ks_distance(
    real_pvalues: pd.Series, 
    simulated_pvalues: np.ndarray
) -> float:
    """
    Calculate Kolmogorov-Smirnov distance between real and simulated p-value distributions.
    
    Args:
        real_pvalues: Series of observed p-values from real data.
        simulated_pvalues: Array of p-values from simulation (or derived distribution).
        
    Returns:
        KS statistic (distance).
    """
    if len(real_pvalues) == 0 or len(simulated_pvalues) == 0:
        raise ValueError("Cannot calculate KS distance with empty distributions.")
    
    ks_stat, _ = stats.ks_2samp(real_pvalues, simulated_pvalues)
    return float(ks_stat)

def run_bootstrapped_validation(
    real_data_df: pd.DataFrame,
    simulated_df: pd.DataFrame,
    alpha: float = 0.05,
    n_bootstraps: int = 1000
) -> Dict[str, Any]:
    """
    Run full bootstrapped validation: calculate power estimates and KS distances
    for each test type and dataset combination.
    
    Args:
        real_data_df: DataFrame with real data p-values.
        simulated_df: DataFrame with simulated error rates.
        alpha: Significance threshold.
        n_bootstraps: Number of bootstrap iterations.
        
    Returns:
        Dictionary with validation results per test type.
    """
    results = {}
    
    # Get unique test types
    test_types = real_data_df['test_type'].unique()
    
    for test_type in test_types:
        # Filter real data for this test type
        real_subset = real_data_df[real_data_df['test_type'] == test_type]
        
        if real_subset.empty:
            results[test_type] = {
                'status': 'skipped',
                'reason': 'No real data for this test type'
            }
            continue
        
        # Calculate bootstrapped power estimate
        power_stats = bootstrap_power_estimate(
            real_subset['p_value'], 
            n_bootstraps=n_bootstraps, 
            alpha=alpha
        )
        
        # Prepare simulated distribution for KS test
        # For KS test, we need a distribution of p-values. 
        # We simulate a uniform distribution under the null hypothesis for comparison,
        # or use the simulated error rates to reconstruct a synthetic distribution.
        # Here we use the simulated power rate to generate a synthetic p-value distribution
        # that matches the observed power for comparison.
        
        n_real = len(real_subset)
        simulated_power_rate = simulated_df[
            (simulated_df['test_type'] == test_type) & 
            (simulated_df['sample_size'] == real_subset['sample_size'].median())
        ]['power'].iloc[0] if not simulated_df.empty else 0.5
        
        # Generate synthetic p-values matching the simulated power
        # Under null: uniform(0,1) -> power = alpha
        # Under alt: p-values concentrated near 0 -> power > alpha
        # We approximate by mixing uniform and concentrated distributions
        n_alt = int(n_real * simulated_power_rate)
        n_null = n_real - n_alt
        
        # Simulate p-values: alt ~ Beta(0.5, 1) (concentrated near 0), null ~ Uniform(0,1)
        np.random.seed(42)  # Reproducibility
        alt_pvals = np.random.beta(0.5, 1, size=n_alt)
        null_pvals = np.random.uniform(0, 1, size=n_null)
        simulated_pvals = np.concatenate([alt_pvals, null_pvals]) if n_alt > 0 else null_pvals
        
        # Calculate KS distance
        ks_dist = calculate_ks_distance(real_subset['p_value'], simulated_pvals)
        
        results[test_type] = {
            'power_estimate': power_stats['power_estimate'],
            'power_ci_lower': power_stats['ci_lower'],
            'power_ci_upper': power_stats['ci_upper'],
            'ks_distance': ks_dist,
            'ks_threshold': KS_THRESHOLD,
            'ks_pass': ks_dist <= KS_THRESHOLD,
            'n_real_samples': n_real,
            'n_simulated_samples': len(simulated_pvals),
            'datasets_included': real_subset['dataset_name'].unique().tolist()
        }
    
    return results

def save_power_results(results: Dict[str, Any], output_path: str = OUTPUT_PATH) -> None:
    """
    Save bootstrapped power estimation results to JSON.
    
    Args:
        results: Dictionary of results.
        output_path: Path to output file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'alpha': 0.05,
        'ks_threshold': KS_THRESHOLD,
        'results_by_test_type': results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Bootstrapped power results saved to: {output_path}")

def main() -> None:
    """
    Main entry point for T032: Bootstrapped power estimation and KS distance calculation.
    """
    print("Starting bootstrapped power estimation (T032)...")
    
    try:
        # Load real data p-values
        print("Loading real data p-values...")
        real_data_df = load_real_data_pvalues()
        print(f"  Loaded {len(real_data_df)} p-values from real datasets.")
        
        # Load simulated power distribution
        print("Loading simulated power distribution...")
        simulated_df = load_simulated_power_distribution()
        print(f"  Loaded {len(simulated_df)} simulated records.")
        
        # Run validation
        print("Running bootstrapped validation...")
        results = run_bootstrapped_validation(real_data_df, simulated_df)
        
        # Check overall pass/fail
        all_passed = all(
            r.get('ks_pass', False) 
            for r in results.values() 
            if r.get('status') != 'skipped'
        )
        
        if all_passed:
            print("SUCCESS: All KS distances are within the threshold (<= 0.10).")
        else:
            failed_tests = [
                k for k, v in results.items() 
                if v.get('status') != 'skipped' and not v.get('ks_pass', False)
            ]
            print(f"WARNING: KS distance exceeded threshold for: {failed_tests}")
        
        # Save results
        save_power_results(results)
        
        print("T032 completed successfully.")
        
        # Print summary
        for detail in results.get("details", []):
            status = "PASS" if detail["passed_threshold"] else "FAIL"
            print(f"  [{status}] {detail['test_type']} (n={detail['sample_size']}): KS={detail['ks_distance']:.4f}, Power={detail['power_estimate']:.3f}")
            
    except FileNotFoundError as e:
        print(f"ERROR: Missing required data file: {e}")
        raise
    except ValueError as e:
        print(f"ERROR: Invalid data: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Unexpected error during bootstrapped validation: {e}")
        raise

if __name__ == "__main__":
    main()
