"""Bootstrapped power estimation and KS distance calculation for real data validation."""
import json
import os
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from code.simulation.output_writer import load_p_values_raw
from code.analysis.validator import load_p_values_to_csv_safe

# Constants for file paths
REAL_DATA_PVALUES_PATH = "data/simulation/real_data_pvalues.csv"
SIMULATED_PVALUES_PATH = "data/simulation/p_values_raw.csv"
OUTPUT_PATH = "data/simulation/real_data_power.json"


def load_real_data_pvalues(filepath: str = REAL_DATA_PVALUES_PATH) -> pd.DataFrame:
    """Load observed p-values from real dataset analysis."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Real data p-values file not found: {filepath}")
    return pd.read_csv(filepath)


def load_simulated_power_distribution(
    sample_size: int,
    test_type: str,
    effect_size: float = 0.0,  # Default to null hypothesis for Type I check, or specific for power
    filepath: str = SIMULATED_PVALUES_PATH
) -> np.ndarray:
    """
    Load simulated p-values from the raw CSV filtered by sample size and test type.
    
    This constructs the 'simulated distribution' against which we compare real data.
    For power estimation (Type II), we typically look at the distribution under the alternative.
    For this task, we filter by the specific sample size of the real dataset and the test type.
    We assume the 'effect_size' in the raw CSV corresponds to the alternative hypothesis 
    if we are checking power, or 0.0 for Type I.
    
    Since the task asks for 'power estimation', we look for the simulated distribution 
    that matches the alternative hypothesis (effect_size > 0) for that sample size.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Simulated p-values file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Filter by sample size and test type
    mask = (df['sample_size'] == sample_size) & (df['test_type'] == test_type)
    
    # If we are estimating power, we want the distribution under the alternative hypothesis.
    # The raw CSV contains p-values for various effect sizes. 
    # We need to identify which effect_size corresponds to the 'power' scenario.
    # Typically, power is calculated at a specific effect size (e.g., 0.5).
    # If the file has multiple effect sizes, we might need to pick one or aggregate.
    # For this implementation, we assume the presence of a non-zero effect_size 
    # representing the alternative hypothesis. If multiple exist, we might take the 
    # one closest to a standard value or the first non-zero one.
    # However, the task description implies a direct comparison. 
    # Let's filter for non-zero effect sizes to represent the alternative hypothesis.
    
    alternative_mask = mask & (df['effect_size'] > 0)
    if alternative_mask.any():
        # If there are multiple effect sizes, we might need to handle them.
        # For now, let's assume we use the first non-zero effect size found or 
        # aggregate if the task implies a specific one.
        # Given the ambiguity, we'll select the row(s) where effect_size > 0.
        # If the simulation ran for multiple effect sizes, the 'power' distribution 
        # is the collection of p-values where H1 is true.
        subset = df[alternative_mask]
    else:
        # Fallback: if no alternative hypothesis data exists (e.g. only null simulated),
        # we can't calculate power in the traditional sense, but we can check the null distribution.
        # However, the task asks for power estimation. We'll raise if strictly needed,
        # but let's try to proceed with whatever is available if the user wants a check.
        # Actually, for power, we MUST have the alternative distribution.
        raise ValueError(f"No simulated p-values found for test_type='{test_type}', sample_size={sample_size} with effect_size > 0.")
    
    p_values = subset['p_value'].values
    return p_values


def bootstrap_power_estimate(p_values: np.ndarray, alpha: float = 0.05) -> float:
    """
    Estimate power as the proportion of p-values < alpha.
    This is the empirical power based on the simulated distribution.
    """
    if len(p_values) == 0:
        return 0.0
    return float(np.mean(p_values < alpha))


def calculate_ks_distance(observed_p_values: np.ndarray, simulated_p_values: np.ndarray) -> float:
    """
    Calculate the Kolmogorov-Smirnov distance between observed and simulated p-value distributions.
    """
    if len(observed_p_values) == 0 or len(simulated_p_values) == 0:
        return float('nan')
    
    ks_stat, _ = stats.ks_2samp(observed_p_values, simulated_p_values)
    return float(ks_stat)


def run_bootstrapped_validation(
    dataset_id: str,
    sample_size: int,
    test_type: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run the full bootstrapped validation for a specific dataset and test configuration.
    
    1. Load observed p-values for the dataset.
    2. Load simulated p-values for the same sample size and test type (under H1).
    3. Calculate KS distance.
    4. Estimate power.
    """
    # Load real data p-values
    real_df = load_real_data_pvalues()
    # Filter for the specific dataset_id and test_type
    # The real_data_pvalues.csv might have multiple rows per dataset if multiple tests were run.
    # We assume the task implies comparing the aggregate or specific subset.
    # Let's filter by dataset_id and test_type.
    mask = (real_df['dataset_id'] == dataset_id) & (real_df['test_type'] == test_type)
    if not mask.any():
        raise ValueError(f"No real data p-values found for dataset_id={dataset_id}, test_type={test_type}")
    
    observed_p_vals = real_df.loc[mask, 'p_value'].values
    
    # Load simulated distribution
    simulated_p_vals = load_simulated_power_distribution(
        sample_size=sample_size,
        test_type=test_type,
        # We don't filter by effect_size here because load_simulated_power_distribution 
        # handles finding the alternative hypothesis distribution.
    )
    
    # Calculate metrics
    ks_dist = calculate_ks_distance(observed_p_vals, simulated_p_vals)
    power_est = bootstrap_power_estimate(simulated_p_vals, alpha)
    
    return {
        "dataset_id": dataset_id,
        "test_type": test_type,
        "sample_size": sample_size,
        "ks_distance": ks_dist,
        "power_estimate": power_est,
        "alpha": alpha,
        "n_observed": len(observed_p_vals),
        "n_simulated": len(simulated_p_vals)
    }


def save_power_results(results: List[Dict[str, Any]], filepath: str = OUTPUT_PATH) -> None:
    """Save the validation results to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    """
    Main entry point for T032: Bootstrapped power estimation and KS distance.
    
    This function assumes that:
    1. data/simulation/p_values_raw.csv exists (from T016)
    2. data/simulation/real_data_pvalues.csv exists (from T031)
    
    It iterates through the unique dataset_ids and test_types found in the real data,
    matches them with the sample size (if available in real data or inferred),
    and computes the metrics.
    
    Note: The real_data_pvalues.csv might not have a 'sample_size' column if the 
    real datasets have fixed sizes. We need to know the sample size of the real 
    dataset to filter the simulation. 
    
    Strategy:
    - The real datasets (Breast Cancer, Wine, Adult) have fixed sizes.
    - We need to map dataset_id to its actual sample size.
    - If 'sample_size' is not in real_data_pvalues.csv, we must derive it.
    - For this implementation, we assume the real_data_pvalues.csv contains the 
      actual p-values from the full dataset. The 'sample_size' used in simulation 
      should match the full dataset size.
    - We will attempt to read the sample size from the real data metadata or 
      infer it from the number of observations if the real data was processed 
      with a specific n.
    - Since the task description says "filtered by the specific sample size of the real dataset",
      we need that size. Let's assume the real_data_pvalues.csv has a 'sample_size' column
      if subsets were used, OR we hardcode the known sizes for the standard datasets 
      if not present.
      
    Known sizes (approximate or full):
    - Breast Cancer (Wisconsin Diagnostic): ~569 samples
    - Wine: 178 samples
    - Adult: ~48k samples (likely downsampled or split in T031?)
    
    If T031 processed the full dataset, the sample size is the full count.
    If T031 used subsets, we need that info.
    
    Assumption: The 'real_data_pvalues.csv' contains a 'sample_size' column 
    reflecting the n used for that specific test run. If not, we will try to 
    infer or raise an error.
    """
    print("Starting bootstrapped power estimation (T032)...")
    
    # Load real data p-values to get dataset IDs and sample sizes
    real_df = load_real_data_pvalues()
    
    # Ensure sample_size column exists. If not, we might need to handle it.
    # For the standard datasets downloaded in T029, the sizes are known.
    # Let's check if the column exists.
    if 'sample_size' not in real_df.columns:
        # Fallback: Map known dataset IDs to their known full sizes.
        # This is a heuristic if the CSV doesn't track it.
        known_sizes = {
            "breast_cancer": 569,
            "wine": 178,
            "adult": 48842 # Or the specific n used in T031
        }
        # We'll need to apply this mapping. But first, let's see if we can 
        # determine the n from the data itself if the column is missing.
        # For now, we'll assume the T031 implementation added this column.
        # If not, we raise an error to be safe.
        raise ValueError("real_data_pvalues.csv must contain a 'sample_size' column.")
    
    results = []
    
    # Iterate over unique combinations of dataset_id, test_type, and sample_size
    grouped = real_df.groupby(['dataset_id', 'test_type', 'sample_size'])
    
    for (dataset_id, test_type, sample_size), group in grouped:
        try:
            print(f"Processing: dataset={dataset_id}, test={test_type}, n={sample_size}")
            result = run_bootstrapped_validation(
                dataset_id=dataset_id,
                sample_size=sample_size,
                test_type=test_type
            )
            results.append(result)
        except Exception as e:
            print(f"Error processing {dataset_id}/{test_type}/{sample_size}: {e}")
            # Continue to next to avoid total failure, but log the error
            results.append({
                "dataset_id": dataset_id,
                "test_type": test_type,
                "sample_size": sample_size,
                "error": str(e)
            })
    
    save_power_results(results)
    print(f"Results saved to {OUTPUT_PATH}")
    print(f"Processed {len(results)} configurations.")


if __name__ == "__main__":
    main()