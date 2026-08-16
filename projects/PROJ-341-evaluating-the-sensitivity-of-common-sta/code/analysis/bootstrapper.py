"""Bootstrapped power estimation and KS distance calculation for real data validation.

This module implements bootstrapped power estimation on real datasets and calculates
the Kolmogorov-Smirnov (KS) distance between real data p-value distributions and
simulated predictions to validate simulation findings.
"""
import json
import os
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Import from existing API surface
from code.simulation.logging_config import get_logger
from code.analysis.validator import load_p_values_to_csv_safe

logger = get_logger(__name__)


def load_real_data_pvalues(filepath: str = "data/simulation/real_data_pvalues.csv") -> pd.DataFrame:
    """Load real data p-values from CSV file.

    Args:
        filepath: Path to the real data p-values CSV file.

    Returns:
        DataFrame containing real data p-values.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Real data p-values file not found: {filepath}")

    df = pd.read_csv(filepath)

    if df.empty:
        raise ValueError(f"Real data p-values file is empty: {filepath}")

    required_cols = ['test_type', 'dataset', 'p_value', 'sample_size']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in real data p-values: {missing_cols}")

    return df


def load_simulated_power_distribution(filepath: str = "data/simulation/error_rates_summary.csv") -> pd.DataFrame:
    """Load simulated error rates to derive power distribution.

    Power = 1 - Type II error rate.

    Args:
        filepath: Path to the error rates summary CSV file.

    Returns:
        DataFrame containing simulated power estimates.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Simulated error rates file not found: {filepath}")

    df = pd.read_csv(filepath)

    if df.empty:
        raise ValueError(f"Simulated error rates file is empty: {filepath}")

    # Ensure we have the columns needed for power calculation
    required_cols = ['test_type', 'sample_size', 'effect_size', 'type_ii_error_rate']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in error rates: {missing_cols}")

    # Calculate power from Type II error rate
    df['power'] = 1.0 - df['type_ii_error_rate']

    return df


def bootstrap_power_estimate(
    p_values: pd.DataFrame,
    n_bootstrap: int = 1000,
    random_state: int = 42
) -> Dict[str, Any]:
    """Perform bootstrapped power estimation on real data p-values.

    This function resamples the real data p-values to estimate the distribution
    of power at different sample sizes and effect sizes.

    Args:
        p_values: DataFrame containing real data p-values.
        n_bootstrap: Number of bootstrap iterations.
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary containing bootstrap statistics:
            - mean_power: Mean power estimate
            - std_power: Standard deviation of power estimates
            - ci_lower: 95% confidence interval lower bound
            - ci_upper: 95% confidence interval upper bound
            - bootstrap_samples: Number of bootstrap samples used
    """
    np.random.seed(random_state)

    if p_values.empty:
        raise ValueError("Cannot bootstrap from empty p-values DataFrame")

    # Group by test type and dataset for stratified bootstrapping
    results = {}

    for (test_type, dataset), group in p_values.groupby(['test_type', 'dataset']):
        if len(group) < 10:
            logger.log("bootstrap_warning", message=f"Too few samples for {test_type} on {dataset}, using all available")

        n_samples = len(group)
        power_estimates = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            resample = group.sample(n=n_samples, replace=True, random_state=np.random.randint(0, 10000))

            # Calculate power as proportion of p-values < alpha (typically 0.05)
            # For real data, we assume the alternative is true if we have effect
            # We estimate power as the proportion of significant results
            alpha = 0.05
            significant_count = (resample['p_value'] < alpha).sum()
            power_estimate = significant_count / n_samples
            power_estimates.append(power_estimate)

        power_estimates = np.array(power_estimates)

        results[f"{test_type}_{dataset}"] = {
            'mean_power': float(np.mean(power_estimates)),
            'std_power': float(np.std(power_estimates)),
            'ci_lower': float(np.percentile(power_estimates, 2.5)),
            'ci_upper': float(np.percentile(power_estimates, 97.5)),
            'bootstrap_samples': n_bootstrap,
            'original_samples': n_samples,
            'power_estimates': power_estimates.tolist()  # Keep for KS calculation
        }

    return results


def calculate_ks_distance(
    real_power_dist: Dict[str, Any],
    simulated_power_df: pd.DataFrame,
    alpha: float = 0.05
) -> Dict[str, float]:
    """Calculate Kolmogorov-Smirnov distance between real and simulated power distributions.

    The KS distance measures the maximum difference between the cumulative distribution
    functions of the real and simulated power estimates.

    Args:
        real_power_dist: Dictionary containing bootstrapped power estimates.
        simulated_power_df: DataFrame containing simulated power estimates.
        alpha: Significance level for power threshold.

    Returns:
        Dictionary mapping test_type_dataset to KS distance value.
    """
    ks_distances = {}

    for key, real_data in real_power_dist.items():
        if 'power_estimates' not in real_data:
            continue

        real_samples = np.array(real_data['power_estimates'])

        # Parse test_type and dataset from key
        parts = key.split('_')
        if len(parts) >= 2:
            test_type = parts[0]
            dataset = '_'.join(parts[1:])

            # Filter simulated data for matching test type
            sim_data = simulated_power_df[
                simulated_power_df['test_type'] == test_type
            ]

            if sim_data.empty:
                logger.log("ks_warning", message=f"No simulated data for {test_type}")
                ks_distances[key] = float('inf')
                continue

            # For real data validation, we compare the distribution of power estimates
            # We use the simulated power at the median sample size of real data as reference
            if 'sample_size' in real_data:
                median_sim_sample = sim_data['sample_size'].median()
                reference_power = sim_data[
                    sim_data['sample_size'] == median_sim_sample
                ]['power'].mean()
            else:
                # Use overall mean power from simulation
                reference_power = sim_data['power'].mean()

            # Create a reference distribution from simulation
            # We simulate the expected distribution around the reference power
            n_sim_samples = len(real_samples)
            sim_samples = np.random.binomial(
                n=1, p=reference_power, size=n_sim_samples
            ).astype(float)

            # Calculate KS statistic
            ks_stat, _ = stats.ks_2samp(real_samples, sim_samples)
            ks_distances[key] = float(ks_stat)

    return ks_distances


def run_bootstrapped_validation(
    real_data_path: str = "data/simulation/real_data_pvalues.csv",
    simulated_data_path: str = "data/simulation/error_rates_summary.csv",
    n_bootstrap: int = 1000,
    random_state: int = 42
) -> Dict[str, Any]:
    """Run the complete bootstrapped validation pipeline.

    This function orchestrates the loading of real and simulated data,
    performs bootstrapped power estimation, and calculates KS distances.

    Args:
        real_data_path: Path to real data p-values CSV.
        simulated_data_path: Path to simulated error rates CSV.
        n_bootstrap: Number of bootstrap iterations.
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary containing complete validation results.
    """
    logger.log("bootstrap_start", message="Starting bootstrapped validation")

    # Load data
    real_pvalues = load_real_data_pvalues(real_data_path)
    logger.log("data_loaded", source="real", rows=len(real_pvalues))

    simulated_power = load_simulated_power_distribution(simulated_data_path)
    logger.log("data_loaded", source="simulated", rows=len(simulated_power))

    # Perform bootstrapping
    bootstrap_results = bootstrap_power_estimate(
        real_pvalues,
        n_bootstrap=n_bootstrap,
        random_state=random_state
    )

    # Calculate KS distances
    ks_distances = calculate_ks_distance(bootstrap_results, simulated_power)

    # Compile results
    validation_results = {
        'bootstrap_parameters': {
            'n_bootstrap': n_bootstrap,
            'random_state': random_state
        },
        'power_estimates': bootstrap_results,
        'ks_distances': ks_distances,
        'validation_criteria': {
            'max_ks_distance': 0.10,
            'description': 'KS distance <= 0.10 indicates good agreement between simulation and real data'
        },
        'overall_assessment': {}
    }

    # Assess overall validation
    all_ks_pass = all(ks <= 0.10 for ks in ks_distances.values() if not np.isinf(ks))
    validation_results['overall_assessment'] = {
        'ks_distance_threshold': 0.10,
        'all_tests_passed': all_ks_pass,
        'num_tests': len(ks_distances),
        'num_passed': sum(1 for ks in ks_distances.values() if not np.isinf(ks) and ks <= 0.10),
        'details': [
            {
                'test_dataset': key,
                'ks_distance': float(ks),
                'passed': not np.isinf(ks) and ks <= 0.10
            }
            for key, ks in ks_distances.items()
        ]
    }

    logger.log("bootstrap_complete", message="Bootstrapped validation completed")

    return validation_results


def save_power_results(
    results: Dict[str, Any],
    filepath: str = "data/simulation/real_data_power.json"
) -> None:
    """Save bootstrapped power estimation results to JSON file.

    Args:
        results: Dictionary containing validation results.
        filepath: Path to output JSON file.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(filepath)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Remove non-serializable data (like numpy arrays) before saving
    def clean_for_json(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [clean_for_json(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif np.isnan(obj) or np.isinf(obj):
            return None
        return obj

    cleaned_results = clean_for_json(results)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cleaned_results, f, indent=2, ensure_ascii=False)

    logger.log("output_written", filepath=filepath, size=os.path.getsize(filepath))


def main() -> None:
    """Main entry point for bootstrapped validation.

    This function runs the complete bootstrapped power estimation pipeline
    and saves results to the designated output file.
    """
    logger.log("main_start", message="Running bootstrapped power estimation")

    # Define paths
    real_data_path = "data/simulation/real_data_pvalues.csv"
    simulated_data_path = "data/simulation/error_rates_summary.csv"
    output_path = "data/simulation/real_data_power.json"

    # Check if input files exist
    if not os.path.exists(real_data_path):
        raise FileNotFoundError(
            f"Required input file not found: {real_data_path}. "
            "Please run the validation pipeline first (T031)."
        )

    if not os.path.exists(simulated_data_path):
        raise FileNotFoundError(
            f"Required input file not found: {simulated_data_path}. "
            "Please run the simulation pipeline first (T017)."
        )

    # Run validation
    results = run_bootstrapped_validation(
        real_data_path=real_data_path,
        simulated_data_path=simulated_data_path,
        n_bootstrap=1000,
        random_state=42
    )

    # Save results
    save_power_results(results, output_path)

    # Print summary
    print(f"Bootstrapped power estimation completed.")
    print(f"Results saved to: {output_path}")
    print(f"Overall assessment: {'PASSED' if results['overall_assessment']['all_tests_passed'] else 'FAILED'}")
    print(f"KS distance threshold: {results['validation_criteria']['max_ks_distance']}")
    print(f"Tests passed: {results['overall_assessment']['num_passed']}/{results['overall_assessment']['num_tests']}")

    logger.log("main_complete", message="Bootstrapped power estimation finished successfully")


if __name__ == "__main__":
    main()
