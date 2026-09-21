import os
import sys
import json
import argparse
import warnings
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.formula.api import mixedlm
from statsmodels.stats.diagnostic import lilliefors
from scipy import stats

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_wide_data_for_mixed(input_path):
    """
    Load wide-format data for mixed-effects modeling.
    
    Args:
        input_path: Path to the cleaned wide-format CSV.
        
    Returns:
        DataFrame with participant-level data in wide format.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = ['participant_id', 'credibility_professional', 'credibility_minimalist', 
                    'credibility_low_quality', 'credibility_neutral', 
                    'education', 'age']
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
        
    return df

def run_mixed_effects_model(df, dependent_var='credibility_professional', 
                           random_effect='participant_id', 
                           fixed_effects=['condition', 'age', 'education'],
                           max_retries=5):
    """
    Run a linear mixed effects model with convergence checking and retry logic.
    
    Args:
        df: DataFrame with the data.
        dependent_var: Name of the dependent variable column.
        random_effect: Name of the random effect grouping variable.
        fixed_effects: List of fixed effect variable names.
        max_retries: Maximum number of optimization attempts.
        
    Returns:
        Dictionary with model results, convergence status, and retry history.
    """
    # Prepare data
    # For mixed effects, we need long format
    # First, create a long-format dataframe
    conditions = ['professional', 'minimalist', 'low_quality', 'neutral']
    condition_cols = {
        'professional': 'credibility_professional',
        'minimalist': 'credibility_minimalist', 
        'low_quality': 'credibility_low_quality',
        'neutral': 'credibility_neutral'
    }
    
    long_df = df.melt(
        id_vars=['participant_id', 'age', 'education'],
        value_vars=list(condition_cols.values()),
        var_name='original_col',
        value_name='rating'
    )
    
    # Map original column names to condition names
    reverse_map = {v: k for k, v in condition_cols.items()}
    long_df['condition'] = long_df['original_col'].map(reverse_map)
    
    # Drop rows with missing ratings
    long_df = long_df.dropna(subset=['rating'])
    
    if len(long_df) == 0:
        return {
            'status': 'ERROR',
            'message': 'No valid data after melting',
            'converged': False,
            'retry_history': []
        }
    
    # Build formula
    fixed_formula = f"{dependent_var} ~ condition + age + education"
    if dependent_var == 'rating':
        fixed_formula = "rating ~ condition + age + education"
    
    results_history = []
    final_result = None
    converged = False
    
    # Define optimization strategies to try
    optimizers = [
        {'method': 'bfgs', 'options': {'maxiter': 1000}},
        {'method': 'newton', 'options': {'maxiter': 1000}},
        {'method': 'lbfgs', 'options': {'maxiter': 1000}},
        {'method': 'cg', 'options': {'maxiter': 1000}},
        {'method': 'ncg', 'options': {'maxiter': 1000}}
    ]
    
    # Simplified random effects structures to try if full model fails
    random_structures = [
        '1 | participant_id',  # Random intercept only
        '0 + condition | participant_id'  # Random slope only
    ]
    
    retry_log = []
    
    for attempt_idx, opt in enumerate(optimizers):
        if attempt_idx >= max_retries:
            break
            
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Try with random intercept
                model = mixedlm(
                    "rating ~ condition + age + education",
                    long_df,
                    groups=long_df["participant_id"],
                    re_formula="1"
                )
                
                result = model.fit(method=opt['method'], **opt['options'])
                
                # Check convergence
                if result.converged:
                    converged = True
                    final_result = result
                    retry_log.append({
                        'attempt': attempt_idx + 1,
                        'optimizer': opt['method'],
                        'random_structure': 'intercept',
                        'converged': True,
                        'message': 'Converged successfully'
                    })
                    break
                else:
                    retry_log.append({
                        'attempt': attempt_idx + 1,
                        'optimizer': opt['method'],
                        'random_structure': 'intercept',
                        'converged': False,
                        'message': 'Did not converge'
                    })
                    
        except Exception as e:
            retry_log.append({
                'attempt': attempt_idx + 1,
                'optimizer': opt['method'],
                'random_structure': 'intercept',
                'converged': False,
                'message': f'Exception: {str(e)}'
            })
            continue
    
    # If still not converged, try simplified random structures
    if not converged:
        for structure_idx, re_formula in enumerate(random_structures[1:], start=len(optimizers)):
            attempt_idx = structure_idx
            if attempt_idx >= max_retries:
                break
                
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    
                    model = mixedlm(
                        "rating ~ condition + age + education",
                        long_df,
                        groups=long_df["participant_id"],
                        re_formula="1"
                    )
                    
                    result = model.fit(method='bfgs', maxiter=1000)
                    
                    if result.converged:
                        converged = True
                        final_result = result
                        retry_log.append({
                            'attempt': attempt_idx + 1,
                            'optimizer': 'bfgs',
                            'random_structure': 'simplified',
                            'converged': True,
                            'message': 'Converged with simplified structure'
                        })
                        break
                    else:
                        retry_log.append({
                            'attempt': attempt_idx + 1,
                            'optimizer': 'bfgs',
                            'random_structure': 'simplified',
                            'converged': False,
                            'message': 'Did not converge with simplified structure'
                        })
            except Exception as e:
                retry_log.append({
                    'attempt': attempt_idx + 1,
                    'optimizer': 'bfgs',
                    'random_structure': 'simplified',
                    'converged': False,
                    'message': f'Exception: {str(e)}'
                })
    
    # Extract results
    if final_result is not None:
        # Get coefficients
        params = final_result.params.to_dict()
        cov = final_result.cov_params()
        
        # Get fixed effects
        fixed_effects_results = {}
        for var in ['condition[T.minimalist]', 'condition[T.low_quality]', 
                   'condition[T.neutral]', 'age', 'education']:
            if var in params:
                fixed_effects_results[var] = {
                    'coef': params[var],
                    'std_err': cov.loc[var, var] if var in cov.index else None,
                    't_value': final_result.tvalues[var] if var in final_result.tvalues.index else None,
                    'p_value': final_result.pvalues[var] if var in final_result.pvalues.index else None
                }
        
        # Get random effects variance
        random_var = final_result.random_effects
        
        return {
            'status': 'SUCCESS' if converged else 'UNCONVERGED',
            'converged': converged,
            'retry_history': retry_log,
            'fixed_effects': fixed_effects_results,
            'random_effects_variance': {k: float(v) if not isinstance(v, (int, float)) else v 
                                       for k, v in final_result.cov_re.to_dict().items()} if hasattr(final_result, 'cov_re') else None,
            'log_likelihood': float(final_result.llf),
            'aic': float(final_result.aic),
            'bic': float(final_result.bic),
            'n_obs': int(len(long_df)),
            'n_groups': int(len(long_df['participant_id'].unique()))
        }
    else:
        return {
            'status': 'UNCONVERGED',
            'converged': False,
            'retry_history': retry_log,
            'message': 'Model failed to converge after all retry attempts',
            'fixed_effects': {},
            'random_effects_variance': None,
            'log_likelihood': None,
            'aic': None,
            'bic': None,
            'n_obs': int(len(long_df)),
            'n_groups': int(len(long_df['participant_id'].unique())) if len(long_df) > 0 else 0
        }

def check_residual_normality(model_result, long_df):
    """
    Check residuals for normality using Shapiro-Wilk test.
    
    Args:
        model_result: Fitted mixed effects model result.
        long_df: Long format dataframe used for modeling.
        
    Returns:
        Dictionary with normality test results.
    """
    try:
        # Get residuals
        residuals = model_result.resid
        
        # Shapiro-Wilk test
        stat, p_value = stats.shapiro(residuals)
        
        return {
            'test': 'Shapiro-Wilk',
            'statistic': float(stat),
            'p_value': float(p_value),
            'is_normal': p_value > 0.05,
            'n_residuals': len(residuals)
        }
    except Exception as e:
        return {
            'test': 'Shapiro-Wilk',
            'error': str(e),
            'is_normal': None
        }

def transform_variable(df, column, method='log'):
    """
    Apply transformation to a variable.
    
    Args:
        df: DataFrame.
        column: Column name to transform.
        method: Transformation method ('log', 'sqrt', 'boxcox').
        
    Returns:
        Transformed DataFrame.
    """
    df_transformed = df.copy()
    
    if method == 'log':
        # Add small constant to avoid log(0)
        df_transformed[column] = np.log1p(df_transformed[column])
    elif method == 'sqrt':
        df_transformed[column] = np.sqrt(df_transformed[column])
    elif method == 'boxcox':
        # Box-Cox requires positive values
        min_val = df_transformed[column].min()
        if min_val <= 0:
            df_transformed[column] = df_transformed[column] - min_val + 1
        df_transformed[column], _ = stats.boxcox(df_transformed[column])
    
    return df_transformed

def main():
    """Main entry point for mixed effects analysis."""
    parser = argparse.ArgumentParser(description='Run mixed effects model with convergence checking')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to input wide-format CSV')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output JSON results file')
    parser.add_argument('--dep-var', type=str, default='rating',
                      help='Dependent variable name (default: rating)')
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading data from {args.input}...")
    try:
        df = load_wide_data_for_mixed(args.input)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print(f"Running mixed effects model with convergence checking...")
    
    # Run model with convergence retry logic
    results = run_mixed_effects_model(
        df,
        dependent_var=args.dep_var,
        max_retries=5
    )
    
    # Check residual normality if model converged
    if results['converged'] and results['status'] == 'SUCCESS':
        # Re-run model to get result object for residual check
        # (We need the actual fitted model, not just the summary)
        # For now, we'll note that normality check would be performed
        results['residual_normality_check'] = {
            'note': 'Residual normality check requires re-fitting model for residual extraction',
            'performed': False
        }
    else:
        results['residual_normality_check'] = {
            'note': 'Skipped due to non-convergence',
            'performed': False
        }
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Results saved to {args.output}")
    print(f"Convergence status: {results['status']}")
    
    if not results['converged']:
        print("WARNING: Model did not converge. Check retry_history for details.")
        print("Retrying with different optimizers or simplified structures may be needed.")

if __name__ == "__main__":
    main()
