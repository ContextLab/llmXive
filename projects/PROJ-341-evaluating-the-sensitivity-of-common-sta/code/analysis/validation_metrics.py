import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

from code.analysis.bootstrapper import calculate_ks_distance, load_simulated_power_distribution
from code.analysis.validator import load_prepared_data

def load_real_data_pvalues(filepath: str = "data/simulation/real_data_pvalues.csv") -> List[Dict[str, Any]]:
    """Load real data p-values from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Real data p-values file not found: {filepath}")
    
    results = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'dataset': row['dataset'],
                'test_type': row['test_type'],
                'p_value': float(row['p_value']),
                'sample_size': int(row['sample_size']),
                'degrees_of_freedom': float(row['df']) if row['df'] != 'nan' else None
            })
    return results

def load_simulated_pvalues_for_comparison(test_type: str, sample_size: int, filepath: str = "data/simulation/p_values_raw.csv") -> List[float]:
    """Load simulated p-values for a specific test type and sample size."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Simulated p-values file not found: {filepath}")
    
    p_values = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['test_type'] == test_type and int(row['sample_size']) == sample_size:
                p_values.append(float(row['p_value']))
    return p_values

def calculate_real_data_power(real_pvalues: List[float], alpha: float = 0.05) -> Dict[str, float]:
    """
    Calculate empirical power from real data p-values.
    Since we don't have ground truth for real data, we estimate power
    as the proportion of p-values < alpha (assuming most effects are real).
    """
    if not real_pvalues:
        return {'power_estimate': 0.0, 'confidence_interval': (0.0, 0.0)}
    
    significant_count = sum(1 for p in real_pvalues if p < alpha)
    power_estimate = significant_count / len(real_pvalues)
    
    # Wilson score interval for power estimate
    n = len(real_pvalues)
    z = 1.96  # 95% confidence
    phat = power_estimate
    
    denominator = 1 + z**2/n
    centre_adjusted_probability = phat + z**2/(2*n)
    adjusted_standard_deviation = np.sqrt((phat*(1-phat) + z**2/(4*n))/n)
    
    lower = (centre_adjusted_probability - z*adjusted_standard_deviation) / denominator
    upper = (centre_adjusted_probability + z*adjusted_standard_deviation) / denominator
    
    return {
        'power_estimate': float(power_estimate),
        'confidence_interval': (float(max(0, lower)), float(min(1, upper))),
        'n_observations': n,
        'significant_count': significant_count
    }

def calculate_validation_metrics(simulated_pvalues: List[float], real_pvalues: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate validation metrics comparing simulated and real data p-value distributions.
    Includes KS distance, power comparison, and distribution similarity measures.
    """
    if not simulated_pvalues or not real_pvalues:
        return {
            'ks_distance': None,
            'ks_pvalue': None,
            'simulated_power': None,
            'real_power': None,
            'validation_status': 'insufficient_data',
            'message': 'Need both simulated and real p-values for comparison'
        }
    
    # KS distance between distributions
    ks_stat, ks_pvalue = stats.ks_2samp(simulated_pvalues, real_pvalues)
    
    # Calculate power for both
    simulated_power = sum(1 for p in simulated_pvalues if p < alpha) / len(simulated_pvalues)
    real_power = sum(1 for p in real_pvalues if p < alpha) / len(real_pvalues)
    
    # Validation status based on KS distance threshold (FR-006: KS <= 0.10)
    if ks_stat <= 0.10:
        status = 'passed'
        message = f'KS distance ({ks_stat:.4f}) within threshold (0.10). Simulation validates real data behavior.'
    else:
        status = 'failed'
        message = f'KS distance ({ks_stat:.4f}) exceeds threshold (0.10). Significant deviation detected.'
    
    return {
        'ks_distance': float(ks_stat),
        'ks_pvalue': float(ks_pvalue),
        'simulated_power': float(simulated_power),
        'real_power': float(real_power),
        'power_difference': float(abs(simulated_power - real_power)),
        'validation_status': status,
        'message': message,
        'simulated_n': len(simulated_pvalues),
        'real_n': len(real_pvalues)
    }

def save_validation_metrics(metrics: Dict[str, Any], output_path: str = "data/simulation/validation_metrics.json") -> None:
    """Save validation metrics to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """
    Main function to calculate and save validation metrics.
    This task (T034) specifically saves validation metrics and KS statistics.
    """
    print("Starting validation metrics calculation (T034)...")
    
    # Load real data p-values
    try:
        real_data = load_real_data_pvalues()
        print(f"Loaded {len(real_data)} real data p-value records")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        # Create empty metrics if data is missing
        metrics = {
            'validation_status': 'data_missing',
            'message': 'Real data p-values file not found. Run validation mode first.',
            'timestamp': str(datetime.now())
        }
        save_validation_metrics(metrics)
        return
    
    # Group real data by test type and sample size for comparison
    from collections import defaultdict
    real_data_by_condition = defaultdict(list)
    for record in real_data:
        key = (record['test_type'], record['sample_size'])
        real_data_by_condition[key].append(record['p_value'])
    
    # Calculate metrics for each condition
    all_metrics = []
    overall_ks_distances = []
    
    for (test_type, sample_size), real_pvals in real_data_by_condition.items():
        # Load corresponding simulated p-values
        sim_pvals = load_simulated_pvalues_for_comparison(test_type, sample_size)
        
        if not sim_pvals:
            print(f"Warning: No simulated p-values found for {test_type} at n={sample_size}")
            continue
        
        # Calculate metrics
        metrics = calculate_validation_metrics(sim_pvals, real_pvals)
        metrics['test_type'] = test_type
        metrics['sample_size'] = sample_size
        all_metrics.append(metrics)
        
        if metrics['ks_distance'] is not None:
            overall_ks_distances.append(metrics['ks_distance'])
    
    # Aggregate results
    if overall_ks_distances:
        avg_ks = np.mean(overall_ks_distances)
        max_ks = np.max(overall_ks_distances)
        min_ks = np.min(overall_ks_distances)
        
        # Determine overall validation status
        if max_ks <= 0.10:
            overall_status = 'passed'
            overall_message = f'All conditions passed KS threshold (max KS={max_ks:.4f}).'
        else:
            overall_status = 'failed'
            overall_message = f'Some conditions exceeded KS threshold (max KS={max_ks:.4f}).'
    else:
        avg_ks = None
        max_ks = None
        min_ks = None
        overall_status = 'no_comparisons'
        overall_message = 'No valid comparisons could be made.'
    
    # Final metrics summary
    final_metrics = {
        'summary': {
            'total_conditions_tested': len(all_metrics),
            'average_ks_distance': float(avg_ks) if avg_ks is not None else None,
            'max_ks_distance': float(max_ks) if max_ks is not None else None,
            'min_ks_distance': float(min_ks) if min_ks is not None else None,
            'validation_status': overall_status,
            'message': overall_message
        },
        'detailed_results': all_metrics,
        'timestamp': str(datetime.now())
    }
    
    # Save to file
    output_path = "data/simulation/validation_metrics.json"
    save_validation_metrics(final_metrics, output_path)
    print(f"Validation metrics saved to {output_path}")
    print(f"Overall validation status: {overall_status}")
    
    return final_metrics

if __name__ == "__main__":
    main()
