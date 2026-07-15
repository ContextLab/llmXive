import os
import json
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from code.analysis.validator import download_breast_cancer_dataset, download_wine_dataset, download_adult_dataset
from code.analysis.real_data_runner import run_ttest_on_dataset, run_anova_on_dataset, run_chi_squared_on_dataset
from code.simulation.output_writer import load_p_values_raw_safe
from code.simulation.logging_config import get_logger

logger = get_logger(__name__)

def load_real_data_pvalues(filepath: str) -> pd.DataFrame:
    """
    Load real data p-values from CSV.
    Expects columns: dataset_name, test_type, p_value, sample_size, hypothesis
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Real data p-values file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} real data p-value records from {filepath}")
    return df

def load_simulated_power_distribution(filepath: str) -> pd.DataFrame:
    """
    Load simulated power distribution data to compare against real data.
    Expects columns: test_type, effect_size, sample_size, power (binary 0/1 per iteration)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Simulated power distribution file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} simulated power records from {filepath}")
    return df

def bootstrap_power_estimate(p_values: np.ndarray, n_bootstrap: int = 1000, alpha: float = 0.05) -> Dict[str, float]:
    """
    Estimate power using bootstrapping on observed p-values.
    
    Power is estimated as the proportion of bootstrap samples where the
    null hypothesis would be rejected (p < alpha).
    
    Args:
        p_values: Array of observed p-values from the real dataset
        n_bootstrap: Number of bootstrap iterations
        alpha: Significance level
        
    Returns:
        Dictionary with bootstrap power estimate and confidence interval
    """
    n_obs = len(p_values)
    if n_obs == 0:
        return {"power_estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}
    
    rejections = []
    rng = np.random.default_rng(42)  # Fixed seed for reproducibility
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = rng.choice(p_values, size=n_obs, replace=True)
        # Calculate proportion of rejections in this bootstrap sample
        # (In real data context, we treat each p-value as a test result)
        rejections.append(np.mean(sample < alpha))
    
    rejections = np.array(rejections)
    power_estimate = np.mean(rejections)
    ci_lower = np.percentile(rejections, 2.5)
    ci_upper = np.percentile(rejections, 97.5)
    
    return {
        "power_estimate": float(power_estimate),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "n_bootstrap": n_bootstrap,
        "n_observations": n_obs
    }

def calculate_ks_distance(simulated_pvalues: np.ndarray, real_pvalues: np.ndarray) -> float:
    """
    Calculate Kolmogorov-Smirnov distance between simulated and real p-value distributions.
    
    Args:
        simulated_pvalues: Array of p-values from simulation
        real_pvalues: Array of p-values from real data
        
    Returns:
        KS statistic (distance between CDFs)
    """
    if len(simulated_pvalues) == 0 or len(real_pvalues) == 0:
        logger.warning("Empty p-value arrays for KS distance calculation")
        return 1.0  # Maximum distance for empty data
    
    ks_stat, _ = stats.ks_2samp(simulated_pvalues, real_pvalues)
    return float(ks_stat)

def run_bootstrapped_validation(
    real_pvalues_df: pd.DataFrame,
    simulated_pvalues_df: pd.DataFrame,
    alpha: float = 0.05,
    n_bootstrap: int = 1000
) -> Dict[str, Any]:
    """
    Run full bootstrapped validation pipeline:
    1. Calculate bootstrap power estimates for real data
    2. Calculate KS distance between real and simulated distributions
    3. Verify KS distance <= 0.10 (threshold from task description)
    
    Args:
        real_pvalues_df: DataFrame with real data p-values
        simulated_pvalues_df: DataFrame with simulated p-values
        alpha: Significance level
        n_bootstrap: Number of bootstrap iterations
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "validation_timestamp": str(pd.Timestamp.now()),
        "alpha": alpha,
        "n_bootstrap": n_bootstrap,
        "tests": {}
    }
    
    # Group by test type
    for test_type in real_pvalues_df['test_type'].unique():
        real_subset = real_pvalues_df[real_pvalues_df['test_type'] == test_type]
        real_pvalues = real_subset['p_value'].values
        
        # Get corresponding simulated p-values for same test type
        sim_subset = simulated_pvalues_df[simulated_pvalues_df['test_type'] == test_type]
        sim_pvalues = sim_subset['p_value'].values
        
        # Calculate bootstrap power
        power_results = bootstrap_power_estimate(real_pvalues, n_bootstrap, alpha)
        
        # Calculate KS distance
        ks_dist = calculate_ks_distance(sim_pvalues, real_pvalues)
        
        # Determine if validation passed (KS <= 0.10)
        ks_passed = ks_dist <= 0.10
        
        results["tests"][test_type] = {
            "n_real_observations": len(real_pvalues),
            "n_simulated_observations": len(sim_pvalues),
            "power_estimate": power_results["power_estimate"],
            "power_ci_lower": power_results["ci_lower"],
            "power_ci_upper": power_results["ci_upper"],
            "ks_distance": ks_dist,
            "ks_threshold": 0.10,
            "ks_passed": ks_passed
        }
        
        logger.info(f"Test {test_type}: Power={power_results['power_estimate']:.3f}, "
                   f"KS={ks_dist:.3f}, Passed={ks_passed}")
    
    # Overall validation status
    all_passed = all(t["ks_passed"] for t in results["tests"].values())
    results["overall_validation_passed"] = all_passed
    results["overall_ks_max"] = max(t["ks_distance"] for t in results["tests"].values())
    
    return results

def save_power_results(results: Dict[str, Any], filepath: str) -> None:
    """
    Save bootstrapped power estimation results to JSON.
    
    Args:
        results: Dictionary with validation results
        filepath: Output file path
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved power results to {filepath}")

def main():
    """
    Main entry point for bootstrapped power estimation task (T032).
    """
    # Paths
    real_pvalues_path = "data/simulation/real_data_pvalues.csv"
    simulated_pvalues_path = "data/simulation/p_values_raw.csv"
    output_path = "data/simulation/real_data_power.json"
    
    logger.info("Starting bootstrapped power estimation (T032)")
    
    # Load real data p-values
    try:
        real_df = load_real_data_pvalues(real_pvalues_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed without real data: {e}")
        raise
    
    # Load simulated p-values
    try:
        sim_df = load_p_values_raw_safe(simulated_pvalues_path)
        # Ensure simulated dataframe has 'p_value' column (might be named differently)
        if 'p_value' not in sim_df.columns:
            # Try to find the column that contains p-values
            p_col = [c for c in sim_df.columns if 'p' in c.lower() and 'value' in c.lower()]
            if p_col:
                sim_df = sim_df.rename(columns={p_col[0]: 'p_value'})
            else:
                raise ValueError(f"Cannot find p-value column in {simulated_pvalues_path}. Columns: {sim_df.columns.tolist()}")
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed without simulated data: {e}")
        raise
    
    # Run validation
    results = run_bootstrapped_validation(real_df, sim_df, alpha=0.05, n_bootstrap=1000)
    
    # Save results
    save_power_results(results, output_path)
    
    # Log summary
    logger.info("=" * 60)
    logger.info("BOOTSTRAPPED POWER ESTIMATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Overall Validation Passed: {results['overall_validation_passed']}")
    logger.info(f"Maximum KS Distance: {results['overall_ks_max']:.4f} (threshold: 0.10)")
    for test_type, metrics in results["tests"].items():
        status = "✓" if metrics["ks_passed"] else "✗"
        logger.info(f"  {test_type}: KS={metrics['ks_distance']:.4f} {status}, Power={metrics['power_estimate']:.3f}")
    logger.info("=" * 60)
    
    return results

if __name__ == "__main__":
    main()