import os
import sys
import json
import random
import numpy as np

# Seed pinning for reproducibility (Task T031)
np.random.seed(42)
random.seed(42)

from pathlib import Path

def get_project_root():
    """Get the root directory of the project."""
    return Path(__file__).resolve().parent.parent.parent

def load_wide_data(input_path):
    """Load and validate the wide-format data."""
    import pandas as pd
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure we have the necessary columns
    if 'credibility_Professional' not in df.columns:
        # If not in wide format, pivot
        if 'stimulus_id' in df.columns and 'credibility' in df.columns:
            df = df.pivot(index='participant_id', columns='stimulus_id', values='credibility')
            df.columns = [f'credibility_{col}' for col in df.columns]
            df = df.reset_index()
    
    return df

def calculate_cohens_d(group1, group2):
    """Calculate Cohen's d effect size for paired samples."""
    import numpy as np
    
    # Calculate differences
    diffs = group1 - group2
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    
    if std_diff == 0:
        return 0.0
    
    cohens_d = mean_diff / std_diff
    return float(cohens_d)

def run_pairwise_tests_with_effects(df, alpha=0.05):
    """Run all pairwise comparisons with effect sizes."""
    from scipy import stats
    import pandas as pd
    
    # Reshape to long format
    df_long = df.melt(
        id_vars=['participant_id'],
        value_vars=[col for col in df.columns if col.startswith('credibility_')],
        var_name='condition',
        value_name='credibility'
    )
    df_long['condition'] = df_long['condition'].str.replace('credibility_', '')
    
    conditions = sorted(df_long['condition'].unique())
    results = []
    
    for i in range(len(conditions)):
        for j in range(i + 1, len(conditions)):
            cond1 = conditions[i]
            cond2 = conditions[j]
            
            data1 = df_long[df_long['condition'] == cond1]['credibility']
            data2 = df_long[df_long['condition'] == cond2]['credibility']
            
            # Paired t-test
            t_stat, p_val = stats.ttest_rel(data1, data2)
            
            # Calculate Cohen's d
            cohens_d = calculate_cohens_d(data1.values, data2.values)
            
            results.append({
                'comparison': f'{cond1}_vs_{cond2}',
                't_statistic': float(t_stat),
                'p_value': float(p_val),
                'cohens_d': cohens_d
            })
    
    return results

def main():
    """Main entry point for pairwise analysis."""
    parser = argparse.ArgumentParser(description='Run pairwise t-tests with effect sizes')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV file')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON file')
    
    args = parser.parse_args()
    
    # Load data
    df = load_wide_data(args.input)
    
    # Run pairwise tests
    pairwise_results = run_pairwise_tests_with_effects(df)
    
    # Apply Bonferroni correction
    n_comparisons = len(pairwise_results)
    for result in pairwise_results:
        result['p_value_bonferroni'] = min(result['p_value'] * n_comparisons, 1.0)
    
    # Prepare output
    output = {
        'pairwise': pairwise_results,
        'n_comparisons': n_comparisons,
        'alpha': 0.05
    }
    
    # Write output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Pairwise analysis complete. Results saved to {args.output}")

if __name__ == '__main__':
    main()
