import os
import sys
import json
import argparse
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
    
    # Validate required columns
    required_cols = ['participant_id', 'condition_Professional', 'condition_Minimalist', 
                    'condition_Low-Quality', 'condition_Neutral', 'credibility']
    
    # Check if we have the wide format credibility columns or need to pivot
    # Assuming the data is already pivoted by preprocess task T024
    if 'credibility_Professional' not in df.columns:
        # If not in wide format, we need to pivot
        if 'stimulus_id' in df.columns and 'credibility' in df.columns:
            df = df.pivot(index='participant_id', columns='stimulus_id', values='credibility')
            df.columns = [f'credibility_{col}' for col in df.columns]
            df = df.reset_index()
    
    return df

def calculate_partial_eta_squared(ss_effect, ss_error):
    """Calculate partial eta-squared for effect size."""
    return ss_effect / (ss_effect + ss_error)

def run_repeated_measures_anova(df):
    """Run repeated measures ANOVA on credibility scores."""
    import pandas as pd
    from statsmodels.stats.anova import AnovaRM
    
    # Reshape to long format for statsmodels
    df_long = df.melt(
        id_vars=['participant_id'],
        value_vars=[col for col in df.columns if col.startswith('credibility_')],
        var_name='condition',
        value_name='credibility'
    )
    
    # Extract condition name (remove 'credibility_' prefix)
    df_long['condition'] = df_long['condition'].str.replace('credibility_', '')
    
    # Run ANOVA
    aov_rm = AnovaRM(df_long, 'credibility', 'participant_id', within=['condition'])
    res = aov_rm.fit()
    
    return res

def run_conditional_pairwise_tests(df, alpha=0.05):
    """Run pairwise t-tests with Bonferroni correction if ANOVA is significant."""
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
    
    # Get unique conditions
    conditions = df_long['condition'].unique()
    pairs = []
    
    for i in range(len(conditions)):
        for j in range(i + 1, len(conditions)):
            cond1 = conditions[i]
            cond2 = conditions[j]
            
            data1 = df_long[df_long['condition'] == cond1]['credibility']
            data2 = df_long[df_long['condition'] == cond2]['credibility']
            
            t_stat, p_val = stats.ttest_rel(data1, data2)
            pairs.append({
                'comparison': f'{cond1}_vs_{cond2}',
                't_statistic': float(t_stat),
                'p_value': float(p_val)
            })
    
    return pairs

def main():
    """Main entry point for ANOVA analysis."""
    parser = argparse.ArgumentParser(description='Run repeated measures ANOVA on survey data')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV file')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON file')
    
    args = parser.parse_args()
    
    # Load data
    df = load_wide_data(args.input)
    
    # Run ANOVA
    anova_result = run_repeated_measures_anova(df)
    
    # Calculate effect size
    # Extract sums of squares from ANOVA result
    ss_condition = anova_result.anova_table['Sum Sq']['condition']
    ss_error = anova_result.anova_table['Sum Sq']['Error']
    eta_sq = calculate_partial_eta_squared(ss_condition, ss_error)
    
    # Extract F-statistic and p-value
    f_stat = float(anova_result.anova_table['F']['condition'])
    p_val = float(anova_result.anova_table['Pr > F']['condition'])
    df_num = int(anova_result.anova_table['DF']['condition'])
    df_den = int(anova_result.anova_table['DF']['Error'])
    
    # Run pairwise tests if significant
    pairwise_results = []
    if p_val < 0.05:
        pairs = run_conditional_pairwise_tests(df)
        # Bonferroni correction
        n_comparisons = len(pairs)
        for pair in pairs:
            pair['p_value_bonferroni'] = min(pair['p_value'] * n_comparisons, 1.0)
            pairwise_results.append(pair)
    
    # Prepare output
    output = {
        'f_stat': f_stat,
        'df': [df_num, df_den],
        'p_val': p_val,
        'eta_sq': eta_sq,
        'pairwise': pairwise_results
    }
    
    # Write output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Analysis complete. Results saved to {args.output}")

if __name__ == '__main__':
    main()
