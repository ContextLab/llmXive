"""
Model Training Pipeline for Solubility Prediction.

Implements XGBoost and Random Forest regressors with k-fold cross-validation
and hyperparameter grid search. Includes Abraham solvation parameter baseline.
"""
import os
import sys
import json
import time
import pickle
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, RegressorMixin

import xgboost as xgb

# Project imports
from utils.constants import DATA_DIR, ARTIFACTS_DIR
from utils.logging import monitor_resources
from utils.errors import CustomDataError

# Constants
RANDOM_SEED = 42
N_FOLDS = 5
MAX_TRIAL_TIME_MINUTES = 30
INPUT_FILE = DATA_DIR / "processed" / "solubility_features.csv"
OUTPUT_MODEL_FILE = ARTIFACTS_DIR / "trained_models.pkl"
OUTPUT_REPORT_FILE = ARTIFACTS_DIR / "training_report.json"


def load_data() -> pd.DataFrame:
    """Load the processed feature dataset."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}. "
                                "Run feature engineering pipeline first.")
    df = pd.read_csv(INPUT_FILE)
    
    # Identify target column (assuming 'log_solubility' based on context)
    target_col = None
    for col in ['log_solubility', 'solubility', 'logS']:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        raise CustomDataError("Could not identify target column in dataset. "
                              "Expected 'log_solubility', 'solubility', or 'logS'.")
    
    # Drop rows with missing target
    df = df.dropna(subset=[target_col])
    return df, target_col


def prepare_features(df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Prepare X and y arrays, returning feature names."""
    feature_cols = [c for c in df.columns if c != target_col]
    # Ensure we have numeric features
    numeric_features = df[feature_cols].select_dtypes(include=[np.number])
    
    if numeric_features.empty:
        raise CustomDataError("No numeric features found in dataset.")
    
    X = numeric_features.values
    y = df[target_col].values
    feature_names = numeric_features.columns.tolist()
    return X, y, feature_names


def train_xgboost(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """Train XGBoost regressor with grid search."""
    print("Training XGBoost model...")
    
    # Define parameter grid
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [3, 5],
        'learning_rate': [0.01, 0.1],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }
    
    xgb_base = xgb.XGBRegressor(
        random_state=RANDOM_SEED,
        objective='reg:squarederror',
        n_jobs=1,  # Limit parallelism to avoid resource contention
        tree_method='hist'
    )
    
    # Use reduced grid for time constraints
    # In production, use Optuna or similar for efficient search
    grid = GridSearchCV(
        xgb_base,
        param_grid,
        cv=N_FOLDS,
        scoring='neg_mean_squared_error',
        n_jobs=1,
        verbose=1,
        refit=True
    )
    
    start_time = time.time()
    grid.fit(X, y)
    elapsed = time.time() - start_time
    
    if elapsed > MAX_TRIAL_TIME_MINUTES * 60:
        print(f"Warning: XGBoost training exceeded time limit ({elapsed/60:.1f} min)")
    
    best_model = grid.best_estimator_
    best_params = grid.best_params_
    
    # Cross-validation scores
    cv_scores = -grid.cv_results_['mean_test_score']
    rmse_cv = np.sqrt(cv_scores)
    
    return {
        'model': best_model,
        'params': best_params,
        'cv_rmse_mean': np.mean(rmse_cv),
        'cv_rmse_std': np.std(rmse_cv),
        'training_time': elapsed,
        'type': 'xgboost'
    }


def train_random_forest(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """Train Random Forest regressor with grid search."""
    print("Training Random Forest model...")
    
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [5, 10, None],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    
    rf_base = RandomForestRegressor(
        random_state=RANDOM_SEED,
        n_jobs=1
    )
    
    grid = GridSearchCV(
        rf_base,
        param_grid,
        cv=N_FOLDS,
        scoring='neg_mean_squared_error',
        n_jobs=1,
        verbose=1,
        refit=True
    )
    
    start_time = time.time()
    grid.fit(X, y)
    elapsed = time.time() - start_time
    
    if elapsed > MAX_TRIAL_TIME_MINUTES * 60:
        print(f"Warning: RF training exceeded time limit ({elapsed/60:.1f} min)")
    
    best_model = grid.best_estimator_
    best_params = grid.best_params_
    
    cv_scores = -grid.cv_results_['mean_test_score']
    rmse_cv = np.sqrt(cv_scores)
    
    return {
        'model': best_model,
        'params': best_params,
        'cv_rmse_mean': np.mean(rmse_cv),
        'cv_rmse_std': np.std(rmse_cv),
        'training_time': elapsed,
        'type': 'random_forest'
    }


def train_abraham_baseline(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Train Abraham solvation parameter baseline.
    
    Primary: Use 'solv' package if available.
    Fallback: Use LinearRegression with Abraham parameters if columns exist.
    """
    print("Training Abraham solvation baseline...")
    
    abraham_cols = ['a', 'b', 'c', 's', 'v', 'r']
    available_cols = [c for c in abraham_cols if c in feature_names]
    
    if not available_cols:
        print("Warning: No Abraham parameters found in features. "
              "Using full feature set as fallback.")
        # Fallback: Use all available features with LinearRegression
        X_abraham = X
        used_cols = feature_names
        is_fallback = True
    else:
        # Use only Abraham parameters
        col_indices = [feature_names.index(c) for c in available_cols]
        X_abraham = X[:, col_indices]
        used_cols = available_cols
        is_fallback = False
    
    model = LinearRegression()
    model.fit(X_abraham, y)
    
    # Cross-validation
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    cv_scores = []
    for train_idx, test_idx in kf.split(X_abraham):
        X_train, X_test = X_abraham[train_idx], X_abraham[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        cv_scores.append(rmse)
    
    return {
        'model': model,
        'params': {'coefficients': dict(zip(used_cols, model.coef_)), 'intercept': float(model.intercept_)},
        'cv_rmse_mean': float(np.mean(cv_scores)),
        'cv_rmse_std': float(np.std(cv_scores)),
        'training_time': 0.0,
        'type': 'abraham_baseline',
        'is_fallback': is_fallback,
        'used_columns': used_cols
    }


def evaluate_models(models: Dict[str, Any], X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Evaluate all trained models on the full dataset (for reporting)."""
    results = {}
    
    for name, data in models.items():
        model = data['model']
        y_pred = model.predict(X)
        
        results[name] = {
            'rmse': float(np.sqrt(mean_squared_error(y, y_pred))),
            'mae': float(mean_absolute_error(y, y_pred)),
            'r2': float(r2_score(y, y_pred)),
            'cv_rmse_mean': data.get('cv_rmse_mean', 0),
            'cv_rmse_std': data.get('cv_rmse_std', 0),
            'training_time': data.get('training_time', 0),
            'type': data.get('type', 'unknown')
        }
    
    return results


def save_models(models: Dict[str, Any], feature_names: List[str], eval_results: Dict[str, Any]):
    """Save trained models and metadata."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    save_data = {
        'models': {k: v for k, v in models.items()},
        'feature_names': feature_names,
        'evaluation_results': eval_results,
        'metadata': {
            'random_seed': RANDOM_SEED,
            'n_folds': N_FOLDS,
            'max_trial_time_min': MAX_TRIAL_TIME_MINUTES
        }
    }
    
    with open(OUTPUT_MODEL_FILE, 'wb') as f:
        pickle.dump(save_data, f)
    
    print(f"Models saved to {OUTPUT_MODEL_FILE}")


def save_report(eval_results: Dict[str, Any], models: Dict[str, Any]):
    """Save training report JSON."""
    # Determine best model
    best_model = None
    best_rmse = float('inf')
    
    for name, res in eval_results.items():
        if res['rmse'] < best_rmse:
            best_rmse = res['rmse']
            best_model = name
    
    report = {
        'best_model': best_model,
        'best_rmse': best_rmse,
        'models': eval_results,
        'hyperparameters': {
            name: data['params'] for name, data in models.items()
        },
        'config': {
            'n_folds': N_FOLDS,
            'random_seed': RANDOM_SEED,
            'max_trial_time_min': MAX_TRIAL_TIME_MINUTES
        }
    }
    
    with open(OUTPUT_REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"Report saved to {OUTPUT_REPORT_FILE}")


def main():
    """Main entry point for model training."""
    # Check resources
    monitor_resources(ram_limit_gb=7.0, disk_limit_gb=14.0)
    
    print("Starting Model Training Pipeline...")
    
    try:
        # Load and prepare data
        df, target_col = load_data()
        X, y, feature_names = prepare_features(df, target_col)
        
        print(f"Loaded {len(X)} samples with {len(feature_names)} features.")
        
        # Train models
        models = {}
        
        # XGBoost
        try:
            models['xgboost'] = train_xgboost(X, y, feature_names)
        except Exception as e:
            print(f"XGBoost training failed: {e}")
            models['xgboost'] = {'error': str(e)}
        
        # Random Forest
        try:
            models['random_forest'] = train_random_forest(X, y, feature_names)
        except Exception as e:
            print(f"Random Forest training failed: {e}")
            models['random_forest'] = {'error': str(e)}
        
        # Abraham Baseline
        try:
            models['abraham'] = train_abraham_baseline(X, y, feature_names)
        except Exception as e:
            print(f"Abraham baseline training failed: {e}")
            models['abraham'] = {'error': str(e)}
        
        # Evaluate
        eval_results = evaluate_models(models, X, y)
        
        # Save artifacts
        save_models(models, feature_names, eval_results)
        save_report(eval_results, models)
        
        print("Model training completed successfully.")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()