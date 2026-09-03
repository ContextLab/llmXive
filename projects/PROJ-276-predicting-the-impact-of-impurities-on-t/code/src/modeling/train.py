import os
import sys
import json
import pickle
import argparse
import signal
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from code.src.utils.logging import get_modeling_logger

# Logger instance
logger = get_modeling_logger("train")

# Global flag for timeout
timeout_reached = False

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    global timeout_reached
    timeout_reached = True
    logger.error("Runtime watchdog triggered: Maximum allowed time exceeded. Aborting.")
    raise TimeoutError("Constitution Principle VII: Maximum allowed time exceeded.")

class TimeoutGuard:
    """Context manager to enforce a runtime limit using signal module."""
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.old_handler = None

    def __enter__(self):
        if os.name == 'nt':
            # Windows doesn't support signal.SIGALRM in the same way
            # Use a threading timer fallback or just warn if strict enforcement is needed
            # For this implementation, we assume Unix-like environment for strict enforcement
            # or rely on the fact that GridSearchCV might not support signal interruption directly
            # but we can wrap the call.
            logger.warning("Running on Windows. Signal-based timeout may not work as expected.")
            self.old_handler = None
            return
        
        self.old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.name != 'nt':
            signal.alarm(0)  # Cancel the alarm
            if self.old_handler:
                signal.signal(signal.SIGALRM, self.old_handler)
        if exc_type is TimeoutError:
            return True  # Suppress the exception if we want to handle it gracefully, 
                         # but here we want it to propagate or be caught by main
        return False

def load_clean_data(csv_path: str) -> pd.DataFrame:
    """Load the clean dataset from CSV."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Clean data file not found: {csv_path}")
    
    logger.info(f"Loading clean data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Validate required columns
    required_cols = ['Tc', 'impurities_atomic_pct', 'temp_K', 'pressure_GPa']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in clean data: {missing}")
    
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def prepare_features_targets(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Prepare features (X) and targets (y) for modeling."""
    # Features: impurity columns (excluding Tc, temp_K, pressure_GPa if they are targets/controls)
    # Assuming impurity columns are those with 'impurity' in name or specific columns
    # For this implementation, we assume all numeric columns except Tc and controls are features
    # or specifically defined impurity columns.
    
    # Let's assume the impurity columns are named like 'impurity_X_atomic_pct' or similar
    # We need to identify them dynamically or by convention.
    # Based on T014, we have 'impurities_atomic_pct'. Let's assume this is a string or we need to parse it.
    # However, for modeling, we likely have one-hot encoded or separate columns for each impurity.
    # Let's assume the dataframe has columns like 'Al_atomic_pct', 'Si_atomic_pct', etc.
    # Or if 'impurities_atomic_pct' is a string, we need to parse it.
    # Given the context of T014 merging, it's likely we have specific impurity columns.
    # Let's assume we select all numeric columns that are not Tc, temp_K, pressure_GPa.
    
    exclude_cols = ['Tc', 'temp_K', 'pressure_GPa', 'impurities_atomic_pct'] # 'impurities_atomic_pct' might be a summary string
    feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['int64', 'float64']]
    
    if not feature_cols:
        # Fallback: try to find columns with 'impurity'
        feature_cols = [col for col in df.columns if 'impurity' in col.lower() and col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found for modeling.")
    
    logger.info(f"Using {len(feature_cols)} feature columns: {feature_cols[:5]}...")
    
    X = df[feature_cols].fillna(0) # Handle missing values if any
    y = df['Tc']
    
    # Stratification target: impurity type (if available) or binned Tc
    # T016 mentions stratified split by impurity type. Let's assume a column 'impurity_type' exists
    # or we derive it from the most significant impurity column.
    if 'impurity_type' in df.columns:
        stratify = df['impurity_type']
    else:
        # Fallback: bin Tc for stratification if no explicit type
        logger.warning("No 'impurity_type' column found. Using binned Tc for stratification.")
        stratify = pd.qcut(y, q=5, labels=False, duplicates='drop')
    
    return X, y, stratify

def train_model(X: pd.DataFrame, y: pd.Series, stratify: pd.Series, timeout_seconds: int = 1800) -> Dict[str, Any]:
    """
    Train multiple models with hyperparameter tuning under a time limit.
    
    Models: Linear Regression, Ridge Regression, Random Forest, XGBoost.
    Returns a dictionary containing the best model, metrics, and all results.
    """
    results = {
        'models': {},
        'best_model': None,
        'best_score': -np.inf,
        'best_params': None,
        'best_model_name': None
    }
    
    # Define models and their parameter grids
    # Hard cap on grid combinations as per task requirement
    max_combinations = 50
    
    models_config = {
        'LinearRegression': {
            'model': LinearRegression(),
            'params': {} # No hyperparameters to tune
        },
        'Ridge': {
            'model': Ridge(),
            'params': {
                'alpha': [0.1, 1.0, 10.0]
            }
        },
        'RandomForest': {
            'model': RandomForestRegressor(random_state=42),
            'params': {
                'n_estimators': [50, 100],
                'max_depth': [None, 5, 10],
                'min_samples_split': [2, 5]
            }
        },
        'XGBoost': {
            'model': XGBRegressor(random_state=42, verbosity=0),
            'params': {
                'n_estimators': [50, 100],
                'max_depth': [3, 5],
                'learning_rate': [0.1, 0.01]
            }
        }
    }
    
    # Validate total combinations
    total_combos = 1 # Linear
    for name, config in models_config.items():
        if name == 'LinearRegression':
            continue
        combos = 1
        for v in config['params'].values():
            combos *= len(v)
        total_combos += combos
    
    if total_combos > max_combinations:
        logger.warning(f"Total grid combinations ({total_combos}) exceed hard cap ({max_combinations}). Truncating grids.")
        # Simple truncation strategy: reduce the largest grid
        for name, config in models_config.items():
            if name == 'LinearRegression':
                continue
            for param in config['params']:
                if len(config['params'][param]) > 3:
                    config['params'][param] = config['params'][param][:3]
        
        # Recalculate
        total_combos = 1
        for name, config in models_config.items():
            if name == 'LinearRegression':
                continue
            combos = 1
            for v in config['params'].values():
                combos *= len(v)
            total_combos += combos
        
        logger.info(f"Adjusted total grid combinations: {total_combos}")

    # Cross-validation strategy
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    
    logger.info(f"Starting model training with timeout of {timeout_seconds} seconds...")
    
    try:
        with TimeoutGuard(timeout_seconds):
            for name, config in models_config.items():
                if timeout_reached:
                    break
                
                logger.info(f"Training {name}...")
                
                model = config['model']
                params = config['params']
                
                # Wrap in pipeline for scaling if needed (especially for Ridge/Linear)
                # For tree models, scaling is less critical but we can include it
                pipeline = Pipeline([
                    ('scaler', StandardScaler()),
                    ('estimator', model)
                ])
                
                # Adjust param names for pipeline
                if params:
                    tuned_params = {f'estimator__{k}': v for k, v in params.items()}
                else:
                    tuned_params = {}
                
                # GridSearchCV
                # If no params, just fit once (no grid search needed)
                if not tuned_params:
                    # Just fit the model
                    pipeline.fit(X, y)
                    score = cross_val_score(pipeline, X, y, cv=cv, scoring='r2').mean()
                    results['models'][name] = {
                        'model': pipeline,
                        'cv_r2': score,
                        'params': {},
                        'mae': 0.0 # Placeholder, calculate later
                    }
                else:
                    grid_search = GridSearchCV(
                        pipeline, 
                        tuned_params, 
                        cv=cv, 
                        scoring='r2',
                        n_jobs=-1,
                        refit=True
                    )
                    grid_search.fit(X, y)
                    
                    best_estimator = grid_search.best_estimator_
                    best_params = grid_search.best_params_
                    best_score = grid_search.best_score_
                    
                    # Calculate MAE on full data for reporting (or use cross_val_predict)
                    # For simplicity, we use the cross_val_score mean for R2 and calculate MAE similarly
                    # or just store the best score.
                    # Let's compute MAE via cross_val_score as well
                    mae_scores = cross_val_score(best_estimator, X, y, cv=cv, scoring='neg_mean_absolute_error')
                    mean_mae = -mae_scores.mean()
                    
                    results['models'][name] = {
                        'model': best_estimator,
                        'cv_r2': best_score,
                        'mae': mean_mae,
                        'params': best_params
                    }
                
                logger.info(f"{name} completed. Best R²: {results['models'][name]['cv_r2']:.4f}")
                
                # Update best model
                if best_score > results['best_score']:
                    results['best_score'] = best_score
                    results['best_model'] = best_estimator
                    results['best_model_name'] = name
                    results['best_params'] = best_params

    except TimeoutError:
        logger.error("Training aborted due to timeout.")
        # Save partial results if any
        if not results['best_model']:
            raise RuntimeError("No models completed training before timeout.")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Train and select best model for MgB2 superconductivity prediction.")
    parser.add_argument("--input", type=str, default="data/processed/mgb2_clean.csv", help="Path to clean data CSV")
    parser.add_argument("--output-model", type=str, default="data/processed/best_model.pkl", help="Path to save best model")
    parser.add_argument("--output-metrics", type=str, default="data/processed/model_metrics.json", help="Path to save metrics JSON")
    parser.add_argument("--timeout", type=int, default=1800, help="Timeout in seconds (default: 1800)")
    args = parser.parse_args()
    
    try:
        # Load data
        df = load_clean_data(args.input)
        
        # Prepare features
        X, y, stratify = prepare_features_targets(df)
        
        # Train models
        results = train_model(X, y, stratify, timeout_seconds=args.timeout)
        
        # Save best model
        output_model_path = Path(args.output_model)
        output_model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_model_path, 'wb') as f:
            pickle.dump(results['best_model'], f)
        logger.info(f"Best model ({results['best_model_name']}) saved to {output_model_path}")
        
        # Save metrics
        # Format metrics for JSON
        metrics_output = {
            'best_model_name': results['best_model_name'],
            'best_r2': results['best_score'],
            'models': {}
        }
        
        for name, data in results['models'].items():
            metrics_output['models'][name] = {
                'cv_r2': data['cv_r2'],
                'mae': data.get('mae', 0.0),
                'params': data['params']
            }
        
        output_metrics_path = Path(args.output_metrics)
        with open(output_metrics_path, 'w') as f:
            json.dump(metrics_output, f, indent=2)
        logger.info(f"Metrics saved to {output_metrics_path}")
        
        print(f"Training complete. Best model: {results['best_model_name']} (R²: {results['best_score']:.4f})")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()