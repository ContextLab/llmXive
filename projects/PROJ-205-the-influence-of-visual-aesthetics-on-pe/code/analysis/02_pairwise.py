import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_wide_data(input_path):
    """
    Load the wide-format data for analysis.
    Expected columns: participant_id, professional_cred, minimalist_cred, 
    low_quality_cred, neutral_cred, professional_prof, minimalist_prof, 
    low_quality_prof, neutral_prof, age, education.
    """
    import pandas as pd
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = [
        'participant_id', 
        'professional_cred', 'minimalist_cred', 'low_quality_cred', 'neutral_cred',
        'professional_prof', 'minimalist_prof', 'low_quality_prof', 'neutral_prof'
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def calculate_cohens_d(group1, group2):
    """
    Calculate Cohen's d effect size for two independent groups.
    For paired data (within-subject), we use the standard deviation of the differences.
    """
    n1, n2 = len(group1), len(group2)
    mean_diff = np.mean(group1) - np.mean(group2)
    
    # For paired t-test context, we calculate d based on the standard deviation of differences
    # This is the appropriate effect size for within-subject designs
    if len(group1) == len(group2):
        # Paired design
        diffs = group1 - group2
        std_diff = np.std(diffs, ddof=1)
        if std_diff == 0:
            return 0.0
        cohens_d = mean_diff / std_diff
    else:
        # Independent design (fallback)
        pooled_std = np.sqrt(((n1 - 1) * np.std(group1, ddof=1)**2 + 
                             (n2 - 1) * np.std(group2, ddof=1)**2) / (n1 + n2 - 2))
        if pooled_std == 0:
            return 0.0
        cohens_d = mean_diff / pooled_std
        
    return cohens_d

def apply_bonferroni(p_values, alpha=0.05):
    """
    Apply Bonferroni correction to p-values.
    Returns corrected p-values and whether each is significant.
    """
    n_tests = len(p_values)
    corrected_p = [min(p * n_tests, 1.0) for p in p_values]
    significant = [p < alpha for p in corrected_p]
    return corrected_p, significant

def apply_fdr_bh(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg (FDR) correction to p-values.
    Returns corrected p-values and whether each is significant.
    """
    # Use statsmodels for robust FDR implementation
    reject, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    return pvals_corrected.tolist(), reject.tolist()

def run_pairwise_tests_with_effects(df, conditions, alpha=0.05, correction_method='bonferroni'):
    """
    Run pairwise t-tests between all condition pairs with effect sizes.
    
    Args:
        df: Wide-format DataFrame with condition columns
        conditions: List of condition names (e.g., ['professional', 'minimalist', 'low_quality', 'neutral'])
        alpha: Significance threshold
        correction_method: 'bonferroni' or 'fdr'
    
    Returns:
        Dictionary with test results
    """
    results = {
        'alpha': alpha,
        'correction_method': correction_method,
        'comparisons': []
    }
    
    # Collect all p-values for correction
    all_p_values = []
    comparisons_data = []
    
    # Generate all unique pairs
    from itertools import combinations
    pairs = list(combinations(conditions, 2))
    
    for cond1, cond2 in pairs:
        # Get data for both conditions (using credibility ratings)
        col1 = f"{cond1}_cred"
        col2 = f"{cond2}_cred"
        
        data1 = df[col1].dropna().values
        data2 = df[col2].dropna().values
        
        if len(data1) == 0 or len(data2) == 0:
            continue
        
        # Run paired t-test (within-subject design)
        t_stat, p_value = stats.ttest_rel(data1, data2)
        
        # Calculate Cohen's d for paired design
        cohens_d = calculate_cohens_d(data1, data2)
        
        comparisons_data.append({
            'condition_1': cond1,
            'condition_2': cond2,
            't_statistic': float(t_stat),
            'unadjusted_p': float(p_value),
            'cohens_d': float(cohens_d),
            'n_observations': len(data1)
        })
        all_p_values.append(p_value)
    
    # Apply correction method
    if correction_method == 'bonferroni':
        corrected_p, significant = apply_bonferroni(all_p_values, alpha)
    elif correction_method == 'fdr':
        corrected_p, significant = apply_fdr_bh(all_p_values, alpha)
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    # Attach corrected p-values and significance to results
    for i, comp in enumerate(comparisons_data):
        comp['corrected_p'] = float(corrected_p[i])
        comp['is_significant'] = significant[i]
        results['comparisons'].append(comp)
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Run pairwise comparisons with effect sizes')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to wide-format CSV file')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output JSON file')
    parser.add_argument('--alpha', type=float, default=0.05,
                      help='Significance threshold')
    parser.add_argument('--correction-method', type=str, 
                      choices=['bonferroni', 'fdr'],
                      default='bonferroni',
                      help='P-value correction method (default: bonferroni)')
    
    args = parser.parse_args()
    
    print(f"Loading data from {args.input}...")
    df = load_wide_data(args.input)
    
    conditions = ['professional', 'minimalist', 'low_quality', 'neutral']
    
    print(f"Running pairwise comparisons with {args.correction_method} correction...")
    results = run_pairwise_tests_with_effects(
        df, 
        conditions, 
        alpha=args.alpha, 
        correction_method=args.correction_method
    )
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {args.output}")
    print(f"Correction method used: {args.correction_method}")
    print(f"Number of comparisons: {len(results['comparisons'])}")
    
    significant_count = sum(1 for comp in results['comparisons'] if comp['is_significant'])
    print(f"Significant comparisons: {significant_count}/{len(results['comparisons'])}")

if __name__ == '__main__':
    main()
