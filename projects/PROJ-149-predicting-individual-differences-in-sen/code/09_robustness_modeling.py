"""
Robustness Modeling (T025c)

Re-runs the modeling pipeline on robustness features generated with 
alternative parameters (2s window size, no ICA).

Input: data/processed/robustness_features_2s.csv
Output: data/processed/robustness_model_results.json
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_path, ensure_dirs, EPSILON
from sklearn.linear_model import LinearRegression, Lasso
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


def load_features(input_path: str) -> pd.DataFrame:
    """Load features from CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Features file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['participant_id', 'median_rt', 'delta_rel', 'theta_rel', 
                    'alpha_rel', 'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df


def prepare_data(df: pd.DataFrame, feature_cols: list) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare X (features), y (target), and participant_ids.
    
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        participant_ids: Array of participant IDs
    """
    X = df[feature_cols].values
    y = df['median_rt'].values
    participant_ids = df['participant_id'].values
    
    return X, y, participant_ids


def fit_model_with_cv(X: np.ndarray, y: np.ndarray, 
                     n_folds: int = 5, 
                     alpha_range: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    Fit Linear Regression and Lasso models with cross-validation.
    
    Args:
        X: Feature matrix
        y: Target vector
        n_folds: Number of CV folds
        alpha_range: Range of alpha values for Lasso (default: logspace -4 to 2)
        
    Returns:
        Dictionary with model results
    """
    if alpha_range is None:
        alpha_range = np.logspace(-4, 2, 50)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Linear Regression
    lr = LinearRegression()
    cv = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    lr_scores = cross_val_score(lr, X_scaled, y, cv=cv, scoring='r2')
    lr_r2_mean = np.mean(lr_scores)
    lr_r2_std = np.std(lr_scores)
    
    # Lasso with CV for optimal alpha
    best_alpha = None
    best_lasso_r2 = -np.inf
    lasso_r2_scores = []
    
    for alpha in alpha_range:
        lasso = Lasso(alpha=alpha, max_iter=10000, random_state=42)
        scores = cross_val_score(lasso, X_scaled, y, cv=cv, scoring='r2')
        mean_score = np.mean(scores)
        lasso_r2_scores.append(mean_score)
        
        if mean_score > best_lasso_r2:
            best_lasso_r2 = mean_score
            best_alpha = alpha
    
    # Fit final models on full data
    lr.fit(X_scaled, y)
    lasso = Lasso(alpha=best_alpha, max_iter=10000, random_state=42)
    lasso.fit(X_scaled, y)
    
    # Calculate R² on full data
    lr_r2_full = r2_score(y, lr.predict(X_scaled))
    lasso_r2_full = r2_score(y, lasso.predict(X_scaled))
    
    # Calculate RMSE
    lr_rmse = np.sqrt(mean_squared_error(y, lr.predict(X_scaled)))
    lasso_rmse = np.sqrt(mean_squared_error(y, lasso.predict(X_scaled)))
    
    # Calculate adjusted R²
    n = len(y)
    p = X.shape[1]
    
    lr_adj_r2 = 1 - (1 - lr_r2_full) * (n - 1) / (n - p - 1) if n > p + 1 else lr_r2_full
    lasso_adj_r2 = 1 - (1 - lasso_r2_full) * (n - 1) / (n - p - 1) if n > p + 1 else lasso_r2_full
    
    return {
        'linear_regression': {
            'r2_cv_mean': float(lr_r2_mean),
            'r2_cv_std': float(lr_r2_std),
            'r2_full': float(lr_r2_full),
            'adj_r2_full': float(lr_adj_r2),
            'rmse_full': float(lr_rmse),
            'coefficients': lr.coef_.tolist(),
            'intercept': float(lr.intercept_)
        },
        'lasso': {
            'optimal_alpha': float(best_alpha),
            'r2_cv_mean': float(best_lasso_r2),
            'r2_full': float(lasso_r2_full),
            'adj_r2_full': float(lasso_adj_r2),
            'rmse_full': float(lasso_rmse),
            'coefficients': lasso.coef_.tolist(),
            'intercept': float(lasso.intercept_)
        },
        'model_comparison': {
            'best_model': 'lasso' if best_lasso_r2 > lr_r2_mean else 'linear_regression',
            'r2_difference': float(best_lasso_r2 - lr_r2_mean)
        },
        'metadata': {
            'n_samples': int(n),
            'n_features': int(p),
            'n_folds': n_folds,
            'feature_names': ['delta_rel', 'theta_rel', 'alpha_rel', 
                             'low_beta_rel', 'high_beta_rel', 'gamma_rel']
        }
    }


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save results to JSON file."""
    output_dir = Path(output_path).parent
    ensure_dirs(output_dir)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_path}")


def main():
    """Main entry point for robustness modeling."""
    parser = argparse.ArgumentParser(description='Robustness Modeling Analysis')
    parser.add_argument('--input', type=str, default=None,
                      help='Path to robustness features CSV')
    parser.add_argument('--output', type=str, default=None,
                      help='Path to output results JSON')
    parser.add_argument('--n-folds', type=int, default=5,
                      help='Number of CV folds')
    args = parser.parse_args()
    
    # Default paths
    input_path = args.input or get_path('data/processed/robustness_features_2s.csv')
    output_path = args.output or get_path('data/processed/robustness_model_results.json')
    
    print(f"Loading robustness features from: {input_path}")
    
    # Load features
    try:
        df = load_features(input_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Make sure T025b has been run to generate robustness_features_2s.csv")
        sys.exit(1)
    
    print(f"Loaded {len(df)} participants")
    
    # Define feature columns
    feature_cols = ['delta_rel', 'theta_rel', 'alpha_rel', 
                   'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    
    # Prepare data
    X, y, participant_ids = prepare_data(df, feature_cols)
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Target vector shape: {y.shape}")
    
    # Check for sufficient samples
    if len(y) < 10:
        print("WARNING: Very small sample size. Results may not be reliable.")
    
    # Fit models
    print("Fitting models with cross-validation...")
    results = fit_model_with_cv(X, y, n_folds=args.n_folds)
    
    # Add metadata
    results['analysis_type'] = 'robustness_modeling'
    results['input_file'] = input_path
    results['parameter_variant'] = '2s_window_no_ica'
    results['timestamp'] = pd.Timestamp.now().isoformat()
    
    # Save results
    save_results(results, output_path)
    
    # Print summary
    print("\n=== Robustness Modeling Results ===")
    print(f"Linear Regression - CV R²: {results['linear_regression']['r2_cv_mean']:.4f} ± {results['linear_regression']['r2_cv_std']:.4f}")
    print(f"Lasso - CV R²: {results['lasso']['r2_cv_mean']:.4f} (alpha={results['lasso']['optimal_alpha']:.4f})")
    print(f"Best Model: {results['model_comparison']['best_model']}")
    print(f"R² Difference: {results['model_comparison']['r2_difference']:.4f}")
    print(f"\nResults saved to: {output_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
