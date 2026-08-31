"""
T017 [US2] [FR-005] Implement modeling pipeline.
Loads features, performs train/test split, fits Multiple Linear Regression and LASSO,
and writes results to data/processed/model_results.json.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Local imports (must match API surface provided)
# We assume config.py exists at code/config.py and exports get_path, ensure_dirs
# If the environment requires explicit path manipulation for imports:
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_path, ensure_dirs, get_seed

from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.linear_model import LinearRegression, Lasso
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

import warnings
warnings.filterwarnings('ignore')

# Constants
RANDOM_SEED = 42  # Default, can be overridden via config if needed

def load_features(input_path=None):
    """
    Load the features CSV file.
    Expects columns: participant_id, median_rt, delta_rel, theta_rel, alpha_rel, low_beta_rel, high_beta_rel, gamma_rel
    """
    if input_path is None:
        input_path = get_path('processed', 'features.csv')
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input features file not found at {input_path}. "
                                "Ensure T012c has completed successfully.")
    
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['participant_id', 'median_rt', 'delta_rel', 'theta_rel', 'alpha_rel', 
                     'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in features file: {missing}")
    
    return df

def load_split_indices(input_path=None):
    """
    Load split indices if they exist (for reproducibility in permutation tests).
    If not found, returns None.
    """
    if input_path is None:
        input_path = get_path('interim', 'split_indices.json')
    
    if not os.path.exists(input_path):
        return None
    
    with open(input_path, 'r') as f:
        return json.load(f)

def prepare_data(df):
    """
    Prepare X (features) and y (target) from the dataframe.
    Returns numpy arrays.
    """
    feature_cols = ['delta_rel', 'theta_rel', 'alpha_rel', 'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    X = df[feature_cols].values
    y = df['median_rt'].values
    return X, y

def fit_model_with_cv(X, y, model_type='linear', cv_folds=5, split_ratio=0.2):
    """
    Performs train/test split, then 5-fold CV on the training set to tune hyperparameters.
    
    Args:
        X: Feature matrix
        y: Target vector
        model_type: 'linear' or 'lasso'
        cv_folds: Number of CV folds
        split_ratio: Fraction of data for testing
    
    Returns:
        dict: Contains optimal model, test metrics, and split indices.
    """
    # 1. Train/Test Split
    X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
        X, y, test_size=split_ratio, random_state=RANDOM_SEED, shuffle=True
    )
    
    split_indices = {
        'train_indices': train_idx.tolist(),
        'test_indices': test_idx.tolist()
    }
    
    # 2. Define Model and Pipeline
    if model_type == 'lasso':
        base_model = Lasso(max_iter=10000, random_state=RANDOM_SEED)
        param_grid = {'lasso__alpha': [0.01, 0.1, 1.0, 10.0, 100.0]}
    else:
        # Linear Regression has no hyperparameters to tune in this context
        base_model = LinearRegression()
        param_grid = None
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('lasso' if model_type == 'lasso' else 'linear', base_model)
    ])
    
    # 3. Cross-Validation on Training Set
    if param_grid:
        # GridSearchCV with 5-fold CV on training data
        kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_SEED)
        search = GridSearchCV(
            pipeline, 
            param_grid, 
            cv=kfold, 
            scoring='neg_mean_squared_error',
            n_jobs=-1
        )
        search.fit(X_train, y_train)
        best_model = search.best_estimator_
        optimal_lambda = search.best_params_['lasso__alpha']
    else:
        pipeline.fit(X_train, y_train)
        best_model = pipeline
        optimal_lambda = None
    
    # 4. Evaluate on Test Set
    y_pred = best_model.predict(X_test)
    test_r2 = r2_score(y_test, y_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # 5. Calculate Adjusted R2 on Training Set (for reporting)
    y_train_pred = best_model.predict(X_train)
    ss_res = np.sum((y_train - y_train_pred) ** 2)
    ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
    n = len(y_train)
    p = X_train.shape[1]  # number of features
    adjusted_r2 = 1 - (1 - (1 - ss_res/ss_tot)) * (n - 1) / (n - p - 1) if n > p + 1 else 0.0
    
    # If Linear Regression, no lambda
    if optimal_lambda is None:
        # For linear regression, we can report the effective penalty as 0 or N/A
        optimal_lambda = 0.0
    
    return {
        'model': best_model,
        'test_r2': test_r2,
        'test_rmse': test_rmse,
        'adjusted_r2': adjusted_r2,
        'optimal_lambda': optimal_lambda,
        'split_indices': split_indices,
        'train_size': len(y_train),
        'test_size': len(y_test)
    }

def save_results(results, output_path=None):
    """
    Save model results to JSON.
    Excludes the sklearn model object itself.
    """
    if output_path is None:
        output_path = get_path('processed', 'model_results.json')
    
    ensure_dirs(output_path)
    
    # Prepare serializable dict
    serializable = {
        'adjusted_r2': float(results['adjusted_r2']),
        'optimal_lambda': float(results['optimal_lambda']),
        'rmse': float(results['test_rmse']), # Mapping test_rmse to 'rmse' as per spec
        'test_r2': float(results['test_r2']),
        'test_rmse': float(results['test_rmse']),
        'train_size': int(results['train_size']),
        'test_size': int(results['test_size']),
        'split_indices': results['split_indices']
    }
    
    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2)
    
    print(f"Results saved to {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Fit predictive models on EEG features.')
    parser.add_argument('--input', type=str, default=None, help='Path to features.csv')
    parser.add_argument('--output', type=str, default=None, help='Path to output model_results.json')
    parser.add_argument('--model', type=str, choices=['linear', 'lasso', 'both'], default='both',
                        help='Which models to fit. Default: both.')
    parser.add_argument('--cv-folds', type=int, default=5, help='Number of CV folds.')
    args = parser.parse_args()

    print("Loading features...")
    df = load_features(args.input)
    print(f"Loaded {len(df)} participants.")

    X, y = prepare_data(df)
    print(f"Feature matrix shape: {X.shape}")

    results = {}

    # Fit Linear Regression
    if args.model in ['linear', 'both']:
        print("Fitting Multiple Linear Regression...")
        linear_res = fit_model_with_cv(X, y, model_type='linear', cv_folds=args.cv_folds)
        results['linear'] = {
            'adjusted_r2': linear_res['adjusted_r2'],
            'test_r2': linear_res['test_r2'],
            'test_rmse': linear_res['test_rmse'],
            'optimal_lambda': 0.0
        }
        # Use linear results for the primary output if 'both' is selected, 
        # but the spec asks for a single model_results.json. 
        # We will prioritize Lasso if 'both' is chosen, or Linear if only linear.
        # However, the spec says "Fit Multiple Linear Regression and LASSO".
        # We will store the best performing one in the root, or store both.
        # Let's store the Lasso result as the primary 'model_results' if Lasso is run,
        # otherwise Linear.
        if args.model == 'linear':
            final_results = linear_res

    # Fit Lasso
    if args.model in ['lasso', 'both']:
        print("Fitting LASSO Regression...")
        lasso_res = fit_model_with_cv(X, y, model_type='lasso', cv_folds=args.cv_folds)
        results['lasso'] = {
            'adjusted_r2': lasso_res['adjusted_r2'],
            'test_r2': lasso_res['test_r2'],
            'test_rmse': lasso_res['test_rmse'],
            'optimal_lambda': lasso_res['optimal_lambda']
        }
        if args.model == 'lasso':
            final_results = lasso_res

    # Determine which result to save as the primary "model_results"
    # The spec implies a single set of metrics. Usually Lasso is preferred for feature selection.
    # We will save the Lasso results if available, otherwise Linear.
    if args.model == 'both':
        # Compare test R2 to decide which is "best" or just save Lasso as it's more robust
        # Let's save Lasso as the primary result if it was run
        final_results = lasso_res
        # We can also store a summary of both in the JSON if needed, but the spec keys are specific.
        # We will stick to the keys: adjusted_r2, optimal_lambda, rmse, test_r2, test_rmse.
        # Lasso fits this perfectly.
    
    # Save the primary result
    save_results(final_results, args.output)

    # If 'both' was requested, we might want to log the comparison
    if args.model == 'both':
        print(f"Linear R2: {results['linear']['test_r2']:.4f}, Lasso R2: {results['lasso']['test_r2']:.4f}")

if __name__ == "__main__":
    main()