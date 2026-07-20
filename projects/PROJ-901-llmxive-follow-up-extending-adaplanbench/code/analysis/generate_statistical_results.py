"""
Generate statistical results from execution traces and human annotations.

This script performs the following:
1. Loads execution traces from data/processed/execution_traces.csv
2. Loads human annotations from data/processed/human_annotations.csv (if available)
3. Fits a GLMM model to test the interaction between constraint count and architecture
4. Calculates effect sizes
5. Outputs statistical_results.json with p-values, effect sizes, and convergence status
"""

import argparse
import json
import os
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from statsmodels.base.model import ConvergenceWarning
import warnings

# Suppress convergence warnings for cleaner output
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import Paths


def load_execution_traces() -> pd.DataFrame:
    """Load execution traces from CSV."""
    traces_path = Paths.PROCESSED_DATA_DIR / "execution_traces.csv"
    if not traces_path.exists():
        raise FileNotFoundError(f"Execution traces not found at {traces_path}")
    return pd.read_csv(traces_path)


def load_human_annotations() -> Optional[pd.DataFrame]:
    """Load human annotations if available."""
    annotations_path = Paths.PROCESSED_DATA_DIR / "human_annotations.csv"
    if not annotations_path.exists():
        return None
    return pd.read_csv(annotations_path)


def prepare_data_for_glmm(traces_df: pd.DataFrame, annotations_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Prepare data for GLMM analysis.
    
    Combines execution traces with human annotations if available.
    Creates binary outcome variable and ensures proper data types.
    """
    # Start with execution traces
    data = traces_df.copy()
    
    # Ensure required columns exist
    required_cols = ['architecture', 'constraint_count', 'violation', 'final_score']
    for col in required_cols:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Convert violation to binary (0/1)
    data['violation_binary'] = data['violation'].astype(int)
    
    # If human annotations available, merge them
    if annotations_df is not None:
        # Merge on task_id
        if 'task_id' in data.columns and 'task_id' in annotations_df.columns:
            data = data.merge(annotations_df[['task_id', 'human_violation']], 
                             on='task_id', how='left')
            # Use human annotation if available, otherwise use model violation
            data['final_violation'] = data['human_violation'].fillna(data['violation_binary'])
        else:
            data['final_violation'] = data['violation_binary']
    else:
        data['final_violation'] = data['violation_binary']
    
    # Encode architecture as numeric (for GLMM)
    data['architecture_encoded'] = (data['architecture'] == 'dual_track').astype(int)
    
    return data


def fit_glmm(data: pd.DataFrame) -> Tuple[Dict[str, Any], Optional[Any]]:
    """
    Fit GLMM model to test interaction between constraint count and architecture.
    
    Returns:
        Dictionary with model results and fit status
        The fitted model object (or None if fitting failed)
    """
    try:
        # Prepare formula for GLM (using architecture and constraint count as predictors)
        # We'll use a binomial family for binary violation outcome
        formula = "final_violation ~ architecture_encoded + constraint_count + architecture_encoded * constraint_count"
        
        # Add intercept
        X = sm.add_constant(data[['architecture_encoded', 'constraint_count']])
        # Add interaction term manually
        X['interaction'] = X['architecture_encoded'] * X['constraint_count']
        
        y = data['final_violation']
        
        # Fit GLM with binomial family
        model = GLM(y, X, family=families.Binomial())
        result = model.fit()
        
        # Check convergence
        converged = result.converged
        
        # Extract coefficients and p-values
        coefficients = result.params.to_dict()
        p_values = result.pvalues.to_dict()
        
        # Extract interaction p-value specifically
        interaction_p = p_values.get('architecture_encoded:constraint_count', 
                                   p_values.get('interaction', None))
        
        return {
            'converged': converged,
            'coefficients': coefficients,
            'p_values': p_values,
            'interaction_p_value': interaction_p,
            'log_likelihood': result.llf,
            'aic': result.aic,
            'bic': result.bic,
            'n_obs': len(data)
        }, result
        
    except Exception as e:
        return {
            'converged': False,
            'error': str(e),
            'coefficients': {},
            'p_values': {},
            'interaction_p_value': None,
            'log_likelihood': None,
            'aic': None,
            'bic': None,
            'n_obs': len(data)
        }, None


def calculate_effect_sizes(data: pd.DataFrame, model_result: Optional[Any] = None) -> Dict[str, Any]:
    """
    Calculate effect sizes for the analysis.
    
    For logistic regression, we calculate odds ratios and confidence intervals.
    """
    effect_sizes = {}
    
    if model_result is not None:
        # Calculate odds ratios from coefficients
        coefficients = model_result.params
        odds_ratios = np.exp(coefficients)
        
        # Calculate confidence intervals
        conf_int = model_result.conf_int()
        lower_bounds = np.exp(conf_int[0])
        upper_bounds = np.exp(conf_int[1])
        
        effect_sizes['odds_ratios'] = odds_ratios.to_dict()
        effect_sizes['confidence_intervals'] = {
            'lower': lower_bounds.to_dict(),
            'upper': upper_bounds.to_dict()
        }
        
        # Calculate pseudo R-squared
        ll_null = model_result.llnull
        ll_fitted = model_result.llf
        pseudo_r2 = 1 - (ll_fitted / ll_null) if ll_null != 0 else 0
        effect_sizes['pseudo_r_squared'] = pseudo_r2
        
    return effect_sizes


def run_statistical_analysis() -> Dict[str, Any]:
    """
    Run complete statistical analysis pipeline.
    
    Returns:
        Dictionary containing all statistical results
    """
    # Load data
    print("Loading execution traces...")
    traces_df = load_execution_traces()
    
    print("Loading human annotations (if available)...")
    annotations_df = load_human_annotations()
    
    # Prepare data
    print("Preparing data for GLMM...")
    prepared_data = prepare_data_for_glmm(traces_df, annotations_df)
    
    # Fit model
    print("Fitting GLMM model...")
    model_results, fitted_model = fit_glmm(prepared_data)
    
    # Calculate effect sizes
    print("Calculating effect sizes...")
    effect_sizes = calculate_effect_sizes(prepared_data, fitted_model)
    
    # Compile final results
    results = {
        'analysis_metadata': {
            'timestamp': pd.Timestamp.now().isoformat(),
            'data_source': 'execution_traces.csv',
            'human_annotations_included': annotations_df is not None,
            'sample_size': len(prepared_data)
        },
        'model_fit': {
            'converged': model_results['converged'],
            'log_likelihood': model_results['log_likelihood'],
            'aic': model_results['aic'],
            'bic': model_results['bic'],
            'n_observations': model_results['n_obs']
        },
        'hypothesis_testing': {
            'interaction_p_value': model_results['interaction_p_value'],
            'null_hypothesis': 'No interaction between architecture and constraint count',
            'alternative_hypothesis': 'Architecture moderates the effect of constraint count on violations'
        },
        'coefficients': model_results['coefficients'],
        'p_values': model_results['p_values'],
        'effect_sizes': effect_sizes,
        'conclusion': {
            'significant_interaction': model_results['interaction_p_value'] < 0.05 
                                      if model_results['interaction_p_value'] is not None else False,
            'interpretation': (
                "Dual-track architecture shows significant mitigation of constraint-related performance degradation"
                if model_results['interaction_p_value'] is not None and model_results['interaction_p_value'] < 0.05
                else "No significant evidence that dual-track architecture mitigates constraint-related degradation"
            ) if model_results['converged'] else "Model failed to converge - results unreliable"
        }
    }
    
    return results


def main():
    """Main entry point for statistical results generation."""
    parser = argparse.ArgumentParser(
        description='Generate statistical results from execution traces'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(Paths.PROCESSED_DATA_DIR / 'statistical_results.json'),
        help='Output path for statistical results JSON'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed progress information'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        print("Starting statistical analysis...")
    
    try:
        # Run analysis
        results = run_statistical_analysis()
        
        # Write results to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Statistical results written to {output_path}")
        
        # Print summary
        if args.verbose:
            print("\n=== Analysis Summary ===")
            print(f"Sample size: {results['analysis_metadata']['sample_size']}")
            print(f"Model converged: {results['model_fit']['converged']}")
            print(f"Interaction p-value: {results['hypothesis_testing']['interaction_p_value']}")
            print(f"Conclusion: {results['conclusion']['interpretation']}")
        
    except Exception as e:
        print(f"Error during statistical analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
