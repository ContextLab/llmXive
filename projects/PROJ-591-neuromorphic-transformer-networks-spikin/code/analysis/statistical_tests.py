import os
import sys
import json
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any

def load_metrics_data(baseline_path: str, spiking_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load baseline and spiking metrics from CSV files.
    
    Args:
        baseline_path: Path to baseline_metrics.csv
        spiking_path: Path to spiking_metrics.csv
        
    Returns:
        Tuple of (baseline_df, spiking_df)
        
    Raises:
        FileNotFoundError: If required CSV files do not exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline metrics file not found: {baseline_path}")
    if not os.path.exists(spiking_path):
        raise FileNotFoundError(f"Spiking metrics file not found: {spiking_path}")
        
    baseline_df = pd.read_csv(baseline_path)
    spiking_df = pd.read_csv(spiking_path)
    
    required_cols = ['seed', 'epoch', 'perplexity', 'energy_per_token_kWh']
    for col in required_cols:
        if col not in baseline_df.columns:
            raise ValueError(f"Missing column '{col}' in baseline metrics")
        if col not in spiking_df.columns:
            raise ValueError(f"Missing column '{col}' in spiking metrics")
            
    return baseline_df, spiking_df

def prepare_paired_data(baseline_df: pd.DataFrame, spiking_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare paired data for statistical testing by matching on seed and epoch.
    
    Args:
        baseline_df: Baseline metrics DataFrame
        spiking_df: Spiking metrics DataFrame
        
    Returns:
        DataFrame with paired rows (baseline and spiking metrics side-by-side)
    """
    # Merge on seed and epoch to create paired data
    paired_df = pd.merge(
        baseline_df[['seed', 'epoch', 'perplexity', 'energy_per_token_kWh']],
        spiking_df[['seed', 'epoch', 'perplexity', 'energy_per_token_kWh']],
        on=['seed', 'epoch'],
        suffixes=('_baseline', '_spiking')
    )
    return paired_df

def run_paired_ttest(paired_df: pd.DataFrame, metric: str) -> Dict[str, Any]:
    """
    Perform paired t-test on a specific metric.
    
    Args:
        paired_df: DataFrame with paired baseline and spiking metrics
        metric: Name of the metric column (e.g., 'perplexity', 'energy_per_token_kWh')
        
    Returns:
        Dictionary with t-statistic, p-value, and confidence interval
    """
    baseline_vals = paired_df[f'{metric}_baseline'].values
    spiking_vals = paired_df[f'{metric}_spiking'].values
    
    # Remove any NaN values
    mask = ~(np.isnan(baseline_vals) | np.isnan(spiking_vals))
    baseline_clean = baseline_vals[mask]
    spiking_clean = spiking_vals[mask]
    
    if len(baseline_clean) < 2:
        return {
            't_statistic': None,
            'p_value': None,
            'mean_diff': None,
            'confidence_interval': None,
            'n_samples': len(baseline_clean)
        }
        
    t_stat, p_val = stats.ttest_rel(baseline_clean, spiking_clean)
    mean_diff = np.mean(baseline_clean - spiking_clean)
    
    # 95% confidence interval for the mean difference
    se = np.std(baseline_clean - spiking_clean, ddof=1) / np.sqrt(len(baseline_clean))
    ci_low = mean_diff - 1.96 * se
    ci_high = mean_diff + 1.96 * se
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val),
        'mean_diff': float(mean_diff),
        'confidence_interval': [float(ci_low), float(ci_high)],
        'n_samples': int(len(baseline_clean))
    }

def apply_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Bonferroni correction for multiple hypothesis testing.
    
    Args:
        p_values: List of raw p-values from hypothesis tests
        
    Returns:
        List of corrected p-values
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
        
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def apply_holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction (step-down method) for multiple hypothesis testing.
    
    This is more powerful than Bonferroni while still controlling family-wise error rate.
    
    Args:
        p_values: List of raw p-values from hypothesis tests
        
    Returns:
        List of corrected p-values
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
        
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = [p_values[i] for i in sorted_indices]
    
    corrected_sorted = []
    for i, p in enumerate(sorted_p):
        # Holm-Bonferroni: p * (n - i)
        corrected_p = min(p * (n_tests - i), 1.0)
        corrected_sorted.append(corrected_p)
        
    # Reorder to original sequence
    corrected = [0.0] * n_tests
    for i, orig_idx in enumerate(sorted_indices):
        corrected[orig_idx] = corrected_sorted[i]
        
    return corrected

def generate_statistical_report(
    baseline_path: str,
    spiking_path: str,
    output_path: str,
    correction_method: str = 'holm_bonferroni'
) -> Dict[str, Any]:
    """
    Generate a comprehensive statistical analysis report.
    
    Args:
        baseline_path: Path to baseline_metrics.csv
        spiking_path: Path to spiking_metrics.csv
        output_path: Path to save the report JSON
        correction_method: 'bonferroni' or 'holm_bonferroni'
        
    Returns:
        Dictionary containing the full statistical analysis results
    """
    # Load and prepare data
    baseline_df, spiking_df = load_metrics_data(baseline_path, spiking_path)
    paired_df = prepare_paired_data(baseline_df, spiking_df)
    
    # Run paired t-tests
    perplexity_result = run_paired_ttest(paired_df, 'perplexity')
    energy_result = run_paired_ttest(paired_df, 'energy_per_token_kWh')
    
    # Collect raw p-values
    raw_p_values = []
    test_names = []
    
    if perplexity_result['p_value'] is not None:
        raw_p_values.append(perplexity_result['p_value'])
        test_names.append('perplexity')
    if energy_result['p_value'] is not None:
        raw_p_values.append(energy_result['p_value'])
        test_names.append('energy_per_token_kWh')
        
    # Apply correction
    if correction_method == 'bonferroni':
        corrected_p_values = apply_bonferroni_correction(raw_p_values)
    elif correction_method == 'holm_bonferroni':
        corrected_p_values = apply_holm_bonferroni_correction(raw_p_values)
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
        
    # Build report
    report = {
        'correction_method': correction_method,
        'n_tests': len(raw_p_values),
        'n_samples': perplexity_result['n_samples'],
        'tests': {}
    }
    
    for i, (name, raw_p, corrected_p) in enumerate(zip(test_names, raw_p_values, corrected_p_values)):
        result = perplexity_result if name == 'perplexity' else energy_result
        report['tests'][name] = {
            'raw_p_value': raw_p,
            'corrected_p_value': corrected_p,
            't_statistic': result['t_statistic'],
            'mean_diff': result['mean_diff'],
            'confidence_interval': result['confidence_interval'],
            'significant_at_0.05': corrected_p < 0.05,
            'significant_at_0.01': corrected_p < 0.01
        }
        
    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    return report

def main():
    """Main entry point for statistical analysis with multiple testing correction."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Statistical analysis with multiple testing correction')
    parser.add_argument('--baseline', type=str, default='data/processed/baseline_metrics.csv',
                      help='Path to baseline metrics CSV')
    parser.add_argument('--spiking', type=str, default='data/processed/spiking_metrics.csv',
                      help='Path to spiking metrics CSV')
    parser.add_argument('--output', type=str, default='data/results/statistical_correction_report.json',
                      help='Path to save correction report')
    parser.add_argument('--method', type=str, choices=['bonferroni', 'holm_bonferroni'],
                      default='holm_bonferroni', help='Correction method to use')
                      
    args = parser.parse_args()
    
    print(f"Loading data from {args.baseline} and {args.spiking}")
    try:
        report = generate_statistical_report(
            args.baseline,
            args.spiking,
            args.output,
            args.method
        )
        print(f"Statistical correction report saved to {args.output}")
        print(f"Correction method: {args.method}")
        print(f"Number of tests: {report['n_tests']}")
        print(f"Number of samples: {report['n_samples']}")
        
        for test_name, test_result in report['tests'].items():
            print(f"\n{test_name}:")
            print(f"  Raw p-value: {test_result['raw_p_value']:.6f}")
            print(f"  Corrected p-value: {test_result['corrected_p_value']:.6f}")
            print(f"  Significant (α=0.05): {test_result['significant_at_0.05']}")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()