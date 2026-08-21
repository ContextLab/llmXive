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

def load_wide_data_for_mixed(input_path):
    """Load data for mixed effects analysis."""
    import pandas as pd
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure we have the necessary columns
    required_cols = ['participant_id', 'Age', 'Education']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Reshape to long format for mixed effects
    credibility_cols = [col for col in df.columns if col.startswith('credibility_')]
    if not credibility_cols:
        raise ValueError("No credibility columns found. Data may not be in wide format.")
    
    df_long = df.melt(
        id_vars=['participant_id', 'Age', 'Education'],
        value_vars=credibility_cols,
        var_name='condition',
        value_name='credibility'
    )
    df_long['condition'] = df_long['condition'].str.replace('credibility_', '')
    
    return df_long

def run_mixed_effects_model(df):
    """Run mixed effects linear model."""
    import pandas as pd
    import statsmodels.api as sm
    from statsmodels.regression.mixed_linear_model import MixedLM
    
    # Prepare data
    df_long = df.copy()
    
    # Convert condition to categorical
    df_long['condition'] = df_long['condition'].astype('category')
    
    # Fit mixed effects model
    # Fixed effects: condition, age, education
    # Random effects: participant_id (random intercept)
    model = MixedLM.from_formula(
        'credibility ~ C(condition) + Age + Education',
        groups='participant_id',
        data=df_long
    )
    
    result = model.fit()
    
    return result

def main():
    """Main entry point for mixed effects analysis."""
    parser = argparse.ArgumentParser(description='Run mixed effects model on survey data')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV file')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON file')
    
    args = parser.parse_args()
    
    # Load data
    df = load_wide_data_for_mixed(args.input)
    
    # Run mixed effects model
    result = run_mixed_effects_model(df)
    
    # Extract coefficients
    params = result.params
    
    # Find condition coefficients (C(condition)[T.X])
    condition_coef = None
    condition_p = None
    
    for param_name, param_val in params.items():
        if param_name.startswith('C(condition)[T.'):
            condition_name = param_name.replace('C(condition)[T.', '').replace(']', '')
            condition_coef = float(param_val)
            # Get p-value
            p_val = result.pvalues[param_name]
            condition_p = float(p_val)
            break
    
    # Prepare output
    output = {
        'condition_coef': condition_coef,
        'condition_p': condition_p,
        'log_likelihood': float(result.llf),
        'n_groups': result.n_groups,
        'nobs': result.nobs,
        'converged': result.converged
    }
    
    # Write output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Mixed effects analysis complete. Results saved to {args.output}")

if __name__ == '__main__':
    main()