import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import from config
from config import get_path, ensure_dirs, get_cv_folds

# Import from utils
from utils.stats_helpers import calculate_sample_size_for_r2

def load_json_safe(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if not found or invalid."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {path}: {e}")
        return None

def calculate_adjusted_r2(r2: float, n_samples: int, n_features: int) -> float:
    """
    Calculate Adjusted R-squared.
    Formula: 1 - (1 - R^2) * (n - 1) / (n - p - 1)
    where n is samples and p is predictors (features).
    """
    if n_samples <= n_features + 1:
        # Avoid division by zero or negative denominator
        return float('-inf')
    
    return 1 - (1 - r2) * (n_samples - 1) / (n_samples - n_features - 1)

def update_model_results(
    results_path: str, 
    features_df: pd.DataFrame, 
    optimal_lambda: Optional[float] = None,
    lasso_r2: Optional[float] = None,
    lasso_rmse: Optional[float] = None,
    linear_r2: Optional[float] = None,
    linear_rmse: Optional[float] = None
) -> Dict[str, Any]:
    """
    Update model_results.json with Adjusted R² and optimal lambda.
    
    Args:
        results_path: Path to model_results.json
        features_df: DataFrame containing features (to get n_samples, n_features)
        optimal_lambda: Optimal lambda from LASSO (if available)
        lasso_r2: R² from LASSO model (if available)
        lasso_rmse: RMSE from LASSO model (if available)
        linear_r2: R² from Linear Regression (if available)
        linear_rmse: RMSE from Linear Regression (if available)
        
    Returns:
        Updated results dictionary
    """
    # Load existing results if they exist
    results = load_json_safe(results_path)
    if results is None:
        results = {}
    
    # Ensure 'models' key exists
    if 'models' not in results:
        results['models'] = {}
    
    n_samples = len(features_df)
    # Exclude target column from feature count if present
    feature_cols = [c for c in features_df.columns if c != 'median_rt']
    n_features = len(feature_cols)
    
    # Calculate Adjusted R² for LASSO if we have R²
    if lasso_r2 is not None:
        adj_r2_lasso = calculate_adjusted_r2(lasso_r2, n_samples, n_features)
        results['models']['lasso'] = results['models'].get('lasso', {})
        results['models']['lasso']['adjusted_r2'] = float(adj_r2_lasso)
        if optimal_lambda is not None:
            results['models']['lasso']['optimal_lambda'] = float(optimal_lambda)
        if lasso_rmse is not None:
            results['models']['lasso']['rmse'] = float(lasso_rmse)
    
    # Calculate Adjusted R² for Linear Regression if we have R²
    if linear_r2 is not None:
        adj_r2_linear = calculate_adjusted_r2(linear_r2, n_samples, n_features)
        results['models']['linear_regression'] = results['models'].get('linear_regression', {})
        results['models']['linear_regression']['adjusted_r2'] = float(adj_r2_linear)
        if linear_rmse is not None:
            results['models']['linear_regression']['rmse'] = float(linear_rmse)
    
    # Add metadata
    results['metadata'] = results.get('metadata', {})
    results['metadata']['n_samples'] = n_samples
    results['metadata']['n_features'] = n_features
    results['metadata']['n_cv_folds'] = get_cv_folds()
    
    return results

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save results dictionary to JSON file."""
    ensure_dirs(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Calculate Adjusted R² and optimal lambda for model results.")
    parser.add_argument('--features', type=str, default='data/processed/features_clr.csv',
                        help='Path to features CSV file')
    parser.add_argument('--results', type=str, default='data/processed/model_results.json',
                        help='Path to model results JSON file')
    parser.add_argument('--lasso-lambda', type=float, default=None,
                        help='Optimal lambda from LASSO (optional)')
    parser.add_argument('--lasso-r2', type=float, default=None,
                        help='R² from LASSO model (optional)')
    parser.add_argument('--lasso-rmse', type=float, default=None,
                        help='RMSE from LASSO model (optional)')
    parser.add_argument('--linear-r2', type=float, default=None,
                        help='R² from Linear Regression (optional)')
    parser.add_argument('--linear-rmse', type=float, default=None,
                        help='RMSE from Linear Regression (optional)')
    args = parser.parse_args()

    # Load features
    if not os.path.exists(args.features):
        print(f"Error: Features file not found: {args.features}")
        sys.exit(1)
    
    features_df = pd.read_csv(args.features)
    print(f"Loaded features: {len(features_df)} samples, {len(features_df.columns)} columns")

    # Update model results
    updated_results = update_model_results(
        results_path=args.results,
        features_df=features_df,
        optimal_lambda=args.lasso_lambda,
        lasso_r2=args.lasso_r2,
        lasso_rmse=args.lasso_rmse,
        linear_r2=args.linear_r2,
        linear_rmse=args.linear_rmse
    )

    # Save updated results
    save_results(updated_results, args.results)
    
    # Print summary
    if 'models' in updated_results:
        print("\nModel Summary:")
        for model_name, model_data in updated_results['models'].items():
            print(f"  {model_name}:")
            if 'adjusted_r2' in model_data:
                print(f"    Adjusted R²: {model_data['adjusted_r2']:.4f}")
            if 'optimal_lambda' in model_data:
                print(f"    Optimal Lambda: {model_data['optimal_lambda']:.4f}")
            if 'rmse' in model_data:
                print(f"    RMSE: {model_data['rmse']:.4f}")

if __name__ == '__main__':
    main()
