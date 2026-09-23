"""
Pairwise comparison analysis module for PROJ-205.

This script performs pairwise t-tests between conditions (Professional, Minimalist,
Low-Quality, Neutral) with multiple comparison corrections (Bonferroni and FDR).

It supports command-line arguments to select the correction method.
"""

import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path
from scipy import stats

# Add project root to path for imports if running as script
def get_project_root():
    """Get the root directory of the project."""
    return Path(__file__).resolve().parent.parent.parent

def load_wide_data(input_path):
    """
    Load wide-format data for pairwise comparisons.

    Expected columns (wide format per participant):
    - participant_id
    - credibility_professional
    - credibility_minimalist
    - credibility_low_quality
    - credibility_neutral
    - professionalism_professional
    - professionalism_minimalist
    - professionalism_low_quality
    - professionalism_neutral
    """
    import pandas as pd
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = [
        'participant_id',
        'credibility_professional', 'credibility_minimalist', 
        'credibility_low_quality', 'credibility_neutral',
        'professionalism_professional', 'professionalism_minimalist',
        'professionalism_low_quality', 'professionalism_neutral'
    ]
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in wide data: {missing}")
    
    return df

def calculate_cohens_d(group1, group2):
    """
    Calculate Cohen's d effect size for two independent groups.
    
    Args:
        group1: Array of values for group 1
        group2: Array of values for group 2
        
    Returns:
        float: Cohen's d
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def apply_bonferroni(p_values, n_tests):
    """
    Apply Bonferroni correction to p-values.
    
    Args:
        p_values: List of uncorrected p-values
        n_tests: Number of tests performed
        
    Returns:
        List of corrected p-values (capped at 1.0)
    """
    return [min(p * n_tests, 1.0) for p in p_values]

def apply_fdr_bh(p_values):
    """
    Apply Benjamini-Hochberg (FDR) correction to p-values.
    
    Args:
        p_values: List of uncorrected p-values
        
    Returns:
        List of corrected p-values
    """
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # BH procedure
    rank = np.arange(1, n + 1)
    corrected = (sorted_p * n) / rank
    
    # Ensure monotonicity (cumulative min from right)
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    
    # Cap at 1.0
    corrected = np.minimum(corrected, 1.0)
    
    # Restore original order
    final_corrected = np.empty(n)
    final_corrected[sorted_indices] = corrected
    
    return final_corrected.tolist()

def run_pairwise_tests_with_effects(df, scale, correction_method='bonferroni'):
    """
    Run pairwise t-tests for a given scale (credibility or professionalism)
    with effect sizes and specified correction method.
    
    Args:
        df: Wide-format DataFrame
        scale: 'credibility' or 'professionalism'
        correction_method: 'bonferroni' or 'fdr'
        
    Returns:
        Dictionary containing test results
    """
    conditions = ['professional', 'minimalist', 'low_quality', 'neutral']
    pairs = [
        ('professional', 'minimalist'),
        ('professional', 'low_quality'),
        ('professional', 'neutral'),
        ('minimalist', 'low_quality'),
        ('minimalist', 'neutral'),
        ('low_quality', 'neutral')
    ]
    
    results = []
    p_values = []
    
    for cond1, cond2 in pairs:
        col1 = f"{scale}_{cond1}"
        col2 = f"{scale}_{cond2}"
        
        # Drop NaN values for this pair
        valid_mask = df[col1].notna() & df[col2].notna()
        group1 = df.loc[valid_mask, col1].values
        group2 = df.loc[valid_mask, col2].values
        
        if len(group1) < 2 or len(group2) < 2:
            continue
        
        # Independent samples t-test
        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
        
        # Calculate Cohen's d
        cohens_d = calculate_cohens_d(group1, group2)
        
        p_values.append(p_val)
        
        results.append({
            'comparison': f"{cond1} vs {cond2}",
            'condition_1': cond1,
            'condition_2': cond2,
            'n_1': len(group1),
            'n_2': len(group2),
            't_statistic': float(t_stat),
            'unadjusted_p': float(p_val),
            'cohens_d': float(cohens_d)
        })
    
    # Apply correction method
    if correction_method == 'bonferroni':
        n_tests = len(p_values)
        corrected_p = apply_bonferroni(p_values, n_tests)
    elif correction_method == 'fdr':
        corrected_p = apply_fdr_bh(p_values)
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    # Add corrected p-values to results
    for i, result in enumerate(results):
        result[f"{correction_method}_p"] = float(corrected_p[i])
        result['significant_at_0.05'] = corrected_p[i] < 0.05
    
    return {
        'scale': scale,
        'correction_method': correction_method,
        'n_comparisons': len(results),
        'tests': results
    }

def main():
    parser = argparse.ArgumentParser(description='Pairwise t-tests with effect sizes and multiple comparison corrections')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to wide-format CSV file')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output JSON file')
    parser.add_argument('--correction-method', type=str, 
                      choices=['bonferroni', 'fdr'],
                      default='bonferroni',
                      help='Multiple comparison correction method (default: bonferroni)')
    parser.add_argument('--compute-both', action='store_true',
                      help='Compute and output both Bonferroni and FDR corrected p-values')
    
    args = parser.parse_args()
    
    print(f"Loading data from {args.input}...")
    df = load_wide_data(args.input)
    
    print(f"Running pairwise tests for credibility with {args.correction_method} correction...")
    credibility_results = run_pairwise_tests_with_effects(df, 'credibility', args.correction_method)
    
    print(f"Running pairwise tests for professionalism with {args.correction_method} correction...")
    professionalism_results = run_pairwise_tests_with_effects(df, 'professionalism', args.correction_method)
    
    output_data = {
        'correction_method': args.correction_method,
        'n_participants': len(df),
        'credibility': credibility_results,
        'professionalism': professionalism_results
    }
    
    # If --compute-both is requested, also compute the other method
    if args.compute_both:
        other_method = 'fdr' if args.correction_method == 'bonferroni' else 'bonferroni'
        
        print(f"Computing {other_method} corrected p-values for comparison...")
        cred_other = run_pairwise_tests_with_effects(df, 'credibility', other_method)
        prof_other = run_pairwise_tests_with_effects(df, 'professionalism', other_method)
        
        # Merge results: add the other method's p-values to the primary results
        for i, test in enumerate(output_data['credibility']['tests']):
            test[f"{other_method}_p"] = cred_other['tests'][i][f"{other_method}_p"]
            test['significant_at_0.05_{other_method}'] = cred_other['tests'][i]['significant_at_0.05']
        
        for i, test in enumerate(output_data['professionalism']['tests']):
            test[f"{other_method}_p"] = prof_other['tests'][i][f"{other_method}_p"]
            test['significant_at_0.05_{other_method}'] = prof_other['tests'][i]['significant_at_0.05']
        
        output_data['additional_correction_method'] = other_method
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Results saved to {args.output}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Scale: credibility")
    print(f"    {args.correction_method} significant comparisons: {sum(1 for t in credibility_results['tests'] if t['significant_at_0.05'])}/{credibility_results['n_comparisons']}")
    print(f"  Scale: professionalism")
    print(f"    {args.correction_method} significant comparisons: {sum(1 for t in professionalism_results['tests'] if t['significant_at_0.05'])}/{professionalism_results['n_comparisons']}")

if __name__ == '__main__':
    main()