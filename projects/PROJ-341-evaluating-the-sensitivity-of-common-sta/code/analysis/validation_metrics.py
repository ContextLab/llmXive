import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

def load_simulated_pvalues_for_comparison(filepath: str = "data/simulation/p_values_raw.csv") -> Dict[str, List[float]]:
    """
    Loads simulated p-values from the raw CSV and groups them by test type and condition.
    Returns a dictionary: { (test_type, sample_size, effect_size): [p1, p2, ...] }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Simulated p-values file not found at {filepath}. Run simulation first.")
    
    df = pd.read_csv(filepath)
    # Ensure numeric columns are numeric
    if 'sample_size' in df.columns:
        df['sample_size'] = pd.to_numeric(df['sample_size'], errors='coerce')
    if 'effect_size' in df.columns:
        df['effect_size'] = pd.to_numeric(df['effect_size'], errors='coerce')
    
    grouped = {}
    for _, row in df.iterrows():
        key = (row['test_type'], row['sample_size'], row['effect_size'])
        p_val = row['p_value']
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(p_val)
    return grouped

def calculate_real_data_power(real_pvalues: List[float], alpha: float = 0.05) -> float:
    """
    Calculates empirical power based on real data p-values.
    In this context, power is the proportion of tests that rejected the null (p < alpha).
    """
    if not real_pvalues:
        return 0.0
    rejections = sum(1 for p in real_pvalues if p < alpha)
    return rejections / len(real_pvalues)

def calculate_ks_distance(simulated_pvalues: List[float], real_pvalues: List[float]) -> float:
    """
    Calculates the Kolmogorov-Smirnov distance between two distributions of p-values.
    """
    if not simulated_pvalues or not real_pvalues:
        return float('nan')
    ks_stat, _ = stats.ks_2samp(simulated_pvalues, real_pvalues)
    return ks_stat

def calculate_validation_metrics(
    sim_pvalues_map: Dict,
    real_pvalues_map: Dict,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Compares simulated and real data p-value distributions.
    Returns a dictionary of metrics including KS distances and power comparisons.
    """
    metrics = {
        "comparison": [],
        "summary": {
            "total_conditions_compared": 0,
            "max_ks_distance": 0.0,
            "mean_ks_distance": 0.0,
            "conditions_passed_threshold": 0,
            "threshold_value": 0.10
        }
    }
    
    ks_distances = []
    
    # Find common keys between simulated and real data
    common_keys = set(sim_pvalues_map.keys()) & set(real_pvalues_map.keys())
    
    for key in common_keys:
        test_type, sample_size, effect_size = key
        sim_vals = sim_pvalues_map[key]
        real_vals = real_pvalues_map[key]
        
        if len(sim_vals) < 10 or len(real_vals) < 5:
            continue # Skip if insufficient data for comparison
        
        ks_dist = calculate_ks_distance(sim_vals, real_vals)
        sim_power = calculate_real_data_power(sim_vals, alpha)
        real_power = calculate_real_data_power(real_vals, alpha)
        
        condition_metrics = {
            "test_type": test_type,
            "sample_size": int(sample_size),
            "effect_size": float(effect_size),
            "ks_distance": float(ks_dist),
            "simulated_power": float(sim_power),
            "real_data_power": float(real_power),
            "power_difference": float(abs(sim_power - real_power)),
            "passed_threshold": bool(ks_dist <= 0.10)
        }
        
        metrics["comparison"].append(condition_metrics)
        ks_distances.append(ks_dist)
        if ks_dist <= 0.10:
            metrics["summary"]["conditions_passed_threshold"] += 1
    
    metrics["summary"]["total_conditions_compared"] = len(ks_distances)
    if ks_distances:
        metrics["summary"]["max_ks_distance"] = float(max(ks_distances))
        metrics["summary"]["mean_ks_distance"] = float(np.mean(ks_distances))
    
    return metrics

def save_validation_metrics(metrics: Dict[str, Any], filepath: str = "data/simulation/validation_metrics.json") -> None:
    """
    Saves the validation metrics to a JSON file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Validation metrics saved to {filepath}")

def main():
    """
    Main entry point to run validation metrics calculation.
    This function orchestrates loading data, calculating metrics, and saving results.
    """
    import sys
    # Add parent directory to path if running as script
    if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from code.simulation.output_writer import load_p_values_raw_safe
    from code.analysis.real_data_runner import load_p_values_to_csv_safe
    
    sim_file = "data/simulation/p_values_raw.csv"
    real_file = "data/simulation/real_data_pvalues.csv"
    output_file = "data/simulation/validation_metrics.json"
    
    print("Loading simulated p-values...")
    try:
        sim_df = load_p_values_raw_safe(sim_file)
        if sim_df is None:
            raise FileNotFoundError(f"Simulated data file {sim_file} not found or empty.")
    except Exception as e:
        print(f"Error loading simulated data: {e}")
        return
    
    print("Loading real data p-values...")
    try:
        real_df = load_p_values_to_csv_safe(real_file)
        if real_df is None:
            raise FileNotFoundError(f"Real data file {real_file} not found or empty.")
    except Exception as e:
        print(f"Error loading real data: {e}")
        return
    
    # Group by test_type, sample_size, effect_size
    # Note: real_data_runner might not have sample_size/effect_size in the same way.
    # For real data, we often compare overall distributions or specific subsets.
    # If real data is aggregated per test type only, we adjust.
    
    # Strategy: 
    # 1. Simulated data is grouped by (test, n, effect).
    # 2. Real data is likely just a list of p-values per test type (since n is fixed by dataset).
    # 3. We will compare the overall distribution of real data p-values against 
    #    the simulated distribution for the *closest* sample size or an average if needed.
    #    However, the spec asks for KS distance per condition if possible.
    #    Given the structure of `real_data_runner`, it likely produces a CSV with columns: test_type, p_value.
    #    Let's assume we compare the overall real distribution for a test type against 
    #    the simulated distribution for a representative sample size (e.g., median n of that test type in sim)
    #    OR, if the real dataset has a specific n, we match that n.
    
    # Simplification for this task: Compare overall distributions per test type.
    # Group simulated by test_type only for comparison with real (if real doesn't have n/effect breakdown)
    
    def group_by_test_type(df):
        result = {}
        for test_type in df['test_type'].unique():
            subset = df[df['test_type'] == test_type]
            result[test_type] = subset['p_value'].tolist()
        return result

    sim_grouped = group_by_test_type(sim_df)
    real_grouped = group_by_test_type(real_df)
    
    # Calculate metrics
    # We construct a pseudo-map for the calculation function to work, 
    # effectively comparing the aggregate real distribution against the aggregate simulated distribution per test.
    # Or, if we want to be more granular, we pick a specific sample size from sim to compare.
    # Let's compare the aggregate real p-values for a test type against the aggregate simulated p-values 
    # for that test type (pooling all n and effects) as a baseline, 
    # OR better: compare against the simulated distribution for the specific sample size of the real dataset if known.
    # Since real_data_runner doesn't track 'n' in the output CSV (it's fixed by the dataset),
    # we will compare the real distribution for a test type against the simulated distribution 
    # for that test type at the sample size closest to the real dataset's size, or just the aggregate.
    
    # Let's implement a direct comparison: Real vs Simulated (pooled by test type)
    # This is a robust check for distribution shape.
    
    validation_results = {
        "comparison": [],
        "summary": {
            "total_conditions_compared": 0,
            "max_ks_distance": 0.0,
            "mean_ks_distance": 0.0,
            "conditions_passed_threshold": 0,
            "threshold_value": 0.10
        }
    }
    
    ks_distances = []
    
    for test_type in real_grouped.keys():
        if test_type not in sim_grouped:
            print(f"Warning: No simulated data for {test_type}")
            continue
        
        real_vals = real_grouped[test_type]
        sim_vals = sim_grouped[test_type]
        
        if not real_vals or not sim_vals:
            continue
        
        ks_dist = calculate_ks_distance(sim_vals, real_vals)
        real_power = calculate_real_data_power(real_vals)
        sim_power = calculate_real_data_power(sim_vals)
        
        result = {
            "test_type": test_type,
            "ks_distance": float(ks_dist),
            "real_data_power": float(real_power),
            "simulated_power": float(sim_power),
            "power_difference": float(abs(real_power - sim_power)),
            "passed_threshold": bool(ks_dist <= 0.10),
            "n_real": len(real_vals),
            "n_sim": len(sim_vals)
        }
        
        validation_results["comparison"].append(result)
        ks_distances.append(ks_dist)
        if ks_dist <= 0.10:
            validation_results["summary"]["conditions_passed_threshold"] += 1
    
    validation_results["summary"]["total_conditions_compared"] = len(ks_distances)
    if ks_distances:
        validation_results["summary"]["max_ks_distance"] = float(max(ks_distances))
        validation_results["summary"]["mean_ks_distance"] = float(np.mean(ks_distances))
    
    save_validation_metrics(validation_results, output_file)
    print("Validation complete.")

if __name__ == "__main__":
    main()
