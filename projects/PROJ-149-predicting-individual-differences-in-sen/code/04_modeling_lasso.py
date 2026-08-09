"""
T018: Implement LASSO regression with lambda tuning to minimize RMSE.

This script loads features and split indices from T017, performs 5-fold
cross-validated LASSO regression with hyperparameter tuning (alpha),
selects the optimal alpha that minimizes RMSE, and saves the results.

Inputs:
  - data/processed/features.csv (from T015/T016)
  - data/interim/split_indices.json (from T017)

Outputs:
  - data/interim/lasso_cv_results.json (detailed CV results)
  - data/processed/model_results_lasso.json (summary with optimal alpha, RMSE, R2)
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import get_path, ensure_dirs, set_global_seed, get_seed
from sklearn.linear_model import LassoCV, Lasso
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler


def load_features(filepath: str) -> pd.DataFrame:
    """Load the features dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Features file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df


def load_split_indices(filepath: str) -> dict:
    """Load the pre-computed split indices."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Split indices file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)


def prepare_data(df: pd.DataFrame, feature_cols: list, target_col: str):
    """
    Prepare X and y arrays from the dataframe.
    Returns scaled X and y.
    """
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Standardize features (important for LASSO)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y, scaler


def fit_lasso_cv(X: np.ndarray, y: np.ndarray, cv_folds: int = 5, 
                 alphas: np.ndarray = None, random_state: int = 42):
    """
    Fit LASSO regression with cross-validation to find optimal alpha.
    
    Args:
        X: Scaled feature matrix
        y: Target vector
        cv_folds: Number of CV folds
        alphas: Array of alpha values to try (if None, uses default grid)
        random_state: Random seed for reproducibility
        
    Returns:
        lasso_cv: Fitted LassoCV model
        cv_results: Dict containing CV results for each alpha
    """
    if alphas is None:
        # Create a range of alpha values on a log scale
        alphas = np.logspace(-4, 0, 100)
    
    # Fit LassoCV
    lasso_cv = LassoCV(
        alphas=alphas,
        cv=cv_folds,
        random_state=random_state,
        max_iter=10000,
        n_jobs=-1
    )
    lasso_cv.fit(X, y)
    
    # Collect CV results
    cv_results = {
        'best_alpha': float(lasso_cv.alpha_),
        'best_score': float(lasso_cv.score(X, y)),
        'mse_mean': lasso_cv.mse_path_.mean(axis=1).tolist(),
        'mse_std': lasso_cv.mse_path_.std(axis=1).tolist(),
        'alphas': alphas.tolist(),
        'n_nonzero_coefs': int((lasso_cv.coef_ != 0).sum())
    }
    
    return lasso_cv, cv_results


def evaluate_model(model: Lasso, X_test: np.ndarray, y_test: np.ndarray):
    """
    Evaluate the LASSO model on test data.
    
    Returns:
        Dict with RMSE, R2, and coefficients
    """
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    return {
        'rmse': float(rmse),
        'r2': float(r2),
        'coefficients': model.coef_.tolist(),
        'intercept': float(model.intercept_)
    }


def save_results(results: dict, output_path: str):
    """Save results to JSON file."""
    ensure_dirs(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='LASSO Regression with Lambda Tuning')
    parser.add_argument('--features', type=str, default=None,
                        help='Path to features CSV (default: from config)')
    parser.add_argument('--splits', type=str, default=None,
                        help='Path to split indices JSON (default: from config)')
    parser.add_argument('--cv-folds', type=int, default=5,
                        help='Number of CV folds (default: 5)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed (default: from config)')
    args = parser.parse_args()
    
    # Set seed
    if args.seed is not None:
        set_global_seed(args.seed)
    else:
        set_global_seed(get_seed())
    
    # Define paths
    features_path = args.features or get_path('processed', 'features.csv')
    splits_path = args.splits or get_path('interim', 'split_indices.json')
    
    # Output paths
    lasso_cv_results_path = get_path('interim', 'lasso_cv_results.json')
    lasso_model_results_path = get_path('processed', 'model_results_lasso.json')
    
    print(f"Loading features from: {features_path}")
    df = load_features(features_path)
    
    print(f"Loading split indices from: {splits_path}")
    split_indices = load_split_indices(splits_path)
    
    # Identify feature and target columns
    # Assuming the target column is 'median_rt' based on the pipeline
    feature_cols = [col for col in df.columns if col not in ['participant_id', 'median_rt']]
    target_col = 'median_rt'
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in features. "
                       f"Available columns: {list(df.columns)}")
    
    print(f"Features: {feature_cols}")
    print(f"Target: {target_col}")
    print(f"Number of samples: {len(df)}")
    
    # Prepare data
    X, y, scaler = prepare_data(df, feature_cols, target_col)
    
    # Split data using pre-computed indices
    # split_indices is a dict of lists: {'train': [...], 'test': [...]}
    train_indices = split_indices['train']
    test_indices = split_indices['test']
    
    X_train, X_test = X[train_indices], X[test_indices]
    y_train, y_test = y[train_indices], y[test_indices]
    
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Fit LASSO with CV
    print("Fitting LASSO with cross-validation...")
    lasso_cv, cv_results = fit_lasso_cv(
        X_train, y_train, 
        cv_folds=args.cv_folds,
        random_state=get_seed()
    )
    
    print(f"Best alpha: {cv_results['best_alpha']}")
    print(f"Best CV score (R2): {cv_results['best_score']:.4f}")
    print(f"Number of non-zero coefficients: {cv_results['n_nonzero_coefs']}")
    
    # Evaluate on test set
    print("Evaluating on test set...")
    test_metrics = evaluate_model(lasso_cv, X_test, y_test)
    
    # Prepare final results
    results = {
        'model_type': 'LASSO',
        'optimal_alpha': cv_results['best_alpha'],
        'cv_r2': cv_results['best_score'],
        'test_rmse': test_metrics['rmse'],
        'test_r2': test_metrics['r2'],
        'n_nonzero_coefs': cv_results['n_nonzero_coefs'],
        'coefficients': dict(zip(feature_cols, test_metrics['coefficients'])),
        'intercept': test_metrics['intercept'],
        'n_samples': len(df),
        'n_train': len(X_train),
        'n_test': len(X_test),
        'cv_folds': args.cv_folds,
        'seed': get_seed(),
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Save CV results
    save_results(cv_results, lasso_cv_results_path)
    
    # Save final model results
    save_results(results, lasso_model_results_path)
    
    print("\n=== LASSO Model Summary ===")
    print(f"Optimal Alpha (lambda): {results['optimal_alpha']:.6f}")
    print(f"CV R²: {results['cv_r2']:.4f}")
    print(f"Test RMSE: {results['test_rmse']:.4f}")
    print(f"Test R²: {results['test_r2']:.4f}")
    print(f"Non-zero coefficients: {results['n_nonzero_coefs']}/{len(feature_cols)}")
    
    # Print top features by absolute coefficient
    coef_dict = results['coefficients']
    sorted_coefs = sorted(coef_dict.items(), key=lambda x: abs(x[1]), reverse=True)
    print("\nTop 5 features by absolute coefficient:")
    for feat, coef in sorted_coefs[:5]:
        print(f"  {feat}: {coef:.6f}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
