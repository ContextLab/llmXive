import os
import sys
import json
from pathlib import Path
import random
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

# Seed pinning for reproducibility (Task T031)
# Crucial for MixedLM convergence and random initialization
_SEED = 42
random.seed(_SEED)
np.random.seed(_SEED)

def get_project_root():
    """Returns the root path of the project."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent

def load_wide_data_for_mixed(csv_path: str) -> pd.DataFrame:
    """
    Loads wide data and reshapes to long format with demographics.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Wide data file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Reshape to long
    condition_names = ['professional', 'minimalist', 'low_quality', 'neutral']
    long_data = []
    
    for _, row in df.iterrows():
        pid = row['participant_id']
        age = row.get('age')
        edu = row.get('education')
        
        for cond in condition_names:
            col_name = f"condition_{cond}_credibility"
            if col_name in row:
                long_data.append({
                    'participant_id': pid,
                    'condition': cond,
                    'score': row[col_name],
                    'age': age,
                    'education': edu
                })
    
    return pd.DataFrame(long_data)

def run_mixed_effects_model(df: pd.DataFrame) -> dict:
    """
    Runs a Mixed-Effects Linear Model with condition, age, education as fixed effects.
    Random intercept for participant_id.
    """
    # Prepare data
    # Encode condition as dummy variables
    df['condition'] = pd.Categorical(df['condition'], categories=['professional', 'minimalist', 'low_quality', 'neutral'])
    
    # Drop rows with missing data
    df_clean = df.dropna(subset=['score', 'age', 'education'])
    
    if len(df_clean) == 0:
        raise ValueError("No valid data for mixed effects model.")
    
    # Formula: score ~ C(condition) + age + education
    # Random: 1 | participant_id
    formula = "score ~ C(condition) + age + education"
    re_formula = "1"
    groups = "participant_id"
    
    # Fit model
    # Set seed for optimization consistency
    np.random.seed(_SEED)
    
    try:
        model = MixedLM.from_formula(formula, df_clean, groups=df_clean[groups], re_formula=re_formula)
        result = model.fit()
    except Exception as e:
        raise RuntimeError(f"MixedLM failed to converge or fit: {e}")
    
    # Extract fixed effects
    fixed_effects = {}
    for param, value in result.params.items():
        fixed_effects[param] = float(value)
    
    # Extract random effects variance
    random_var = float(result.cov_re.iloc[0, 0]) if result.cov_re is not None else 0.0
    
    # Convergence status
    converged = result.converged
    
    return {
        'fixed_effects': fixed_effects,
        'random_intercept_variance': random_var,
        'converged': converged,
        'log_likelihood': float(result.llf),
        'aic': float(result.aic),
        'bic': float(result.bic)
    }

def main():
    """
    Main entry point for mixed effects analysis.
    """
    project_root = get_project_root()
    wide_csv = project_root / 'data' / 'processed' / 'wide_submissions.csv'
    output_json = project_root / 'data' / 'processed' / 'mixed_effects_results.json'
    
    if not wide_csv.exists():
        print(f"Error: Wide data not found at {wide_csv}", file=sys.stderr)
        sys.exit(1)
    
    try:
        df = load_wide_data_for_mixed(str(wide_csv))
        results = run_mixed_effects_model(df)
        
        output_path = Path(output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Mixed effects analysis complete. Results saved to {output_json}")
        
    except Exception as e:
        print(f"Error in mixed effects analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
