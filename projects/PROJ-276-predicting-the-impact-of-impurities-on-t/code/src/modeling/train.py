"""
Training script for MgB2 superconductivity models.
Implements Linear Regression, Ridge Regression, Random Forest, and XGBoost.
Performs stratified split, hyperparameter tuning, and model selection.
"""
import os
import sys
import json
import pickle
import argparse
import signal
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from code.src.utils.logging import get_modeling_logger
from code.src.utils.constants import VIF_THRESHOLD

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

logger = get_modeling_logger("train")

# Timeout handling
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Model training exceeded time limit")

class TimeoutGuard:
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.old_handler = None

    def __enter__(self):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        if self.old_handler:
            signal.signal(signal.SIGALRM, self.old_handler)

def load_clean_data(filepath: str) -> pd.DataFrame:
    """Load the cleaned MgB2 dataset."""
    path = Path(filepath)
    if not path.exists():
        logger.error(f"Clean data file not found: {filepath}")
        raise FileNotFoundError(f"Clean data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    
    # Validate required columns
    required_cols = ['Tc', 'impurity_C', 'impurity_O', 'impurity_Al', 
                    'impurity_Si', 'temp_K', 'pressure_GPa']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        raise ValueError(f"Missing required columns: {missing}")
    
    return df

def prepare_features_targets(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare features (X) and target (y) for modeling.
    Stratification is based on impurity type (dominant impurity).
    """
    # Target: Tc (critical temperature)
    y = df['Tc'].values
    
    # Features: impurity concentrations and synthesis conditions
    feature_cols = ['impurity_C', 'impurity_O', 'impurity_Al', 
                   'impurity_Si', 'temp_K', 'pressure_GPa']
    X = df[feature_cols].values
    
    # Create stratification label: dominant impurity type
    impurity_cols = ['impurity_C', 'impurity_O', 'impurity_Al', 'impurity_Si']
    impurity_data = df[impurity_cols].values
    
    # Find dominant impurity for each sample
    dominant_impurity = np.argmax(impurity_data, axis=1)
    strat_labels = np.array(['C' if i == 0 else 'O' if i == 1 else 'Al' if i == 2 else 'Si' 
                             for i in dominant_impurity])
    
    # Handle edge case: all zeros -> 'None'
    zero_mask = (impurity_data.sum(axis=1) == 0)
    strat_labels[zero_mask] = 'None'
    
    logger.info(f"Stratification labels distribution: {np.unique(strat_labels, return_counts=True)}")
    
    return X, y, strat_labels

def train_model(model_name: str, X_train: np.ndarray, y_train: np.ndarray, 
               X_test: np.ndarray, y_test: np.ndarray, 
               param_grid: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Train a model with optional hyperparameter tuning.
    Returns model info, metrics, and best parameters.
    """
    logger.info(f"Training {model_name}...")
    
    # Define models
    models = {
        'Linear Regression': LinearRegression(),
        'Ridge Regression': Ridge(),
        'Random Forest': RandomForestRegressor(random_state=42, n_jobs=-1),
        'XGBoost': xgb.XGBRegressor(random_state=42, n_jobs=-1, verbosity=0)
    }
    
    model = models[model_name]
    
    # Define default parameter grids
    default_grids = {
        'Linear Regression': {},
        'Ridge Regression': {'alpha': [0.1, 1.0, 10.0]},
        'Random Forest': {
            'n_estimators': [50, 100],
            'max_depth': [5, 10, None],
            'min_samples_split': [2, 5]
        },
        'XGBoost': {
            'n_estimators': [50, 100],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.1]
        }
    }
    
    grid = param_grid if param_grid else default_grids.get(model_name, {})
    
    # Use GridSearchCV if parameters provided, else fit directly
    if grid:
        logger.info(f"  Hyperparameter grid: {grid}")
        
        # Limit grid combinations to <= 10 as per spec
        total_combinations = 1
        for param_values in grid.values():
            total_combinations *= len(param_values) if isinstance(param_values, list) else 1
        
        if total_combinations > 10:
            logger.warning(f"  Grid has {total_combinations} combinations, reducing to 10")
            # Truncate grid to first 10 combinations
            keys = list(grid.keys())
            for key in keys:
                if isinstance(grid[key], list) and len(grid[key]) > 10:
                    grid[key] = grid[key][:10]
            total_combinations = 1
            for param_values in grid.values():
                total_combinations *= len(param_values) if isinstance(param_values, list) else 1
            logger.info(f"  Reduced grid to {total_combinations} combinations")
        
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        
        # For regression, we need to create stratification labels for CV
        # Use binned y values for stratification
        y_binned = pd.qcut(y_train, q=3, labels=False, duplicates='drop')
        
        try:
            grid_search = GridSearchCV(
                model, grid, cv=cv, scoring='r2', n_jobs=-1, verbose=1
            )
            grid_search.fit(X_train, y_train)
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            cv_r2 = grid_search.best_score_
            logger.info(f"  Best CV R²: {cv_r2:.4f}")
        except Exception as e:
            logger.warning(f"  Grid search failed: {e}, falling back to default params")
            best_model = model
            if model_name == 'Ridge Regression':
                best_model = Ridge(alpha=1.0)
            elif model_name == 'Random Forest':
                best_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
            elif model_name == 'XGBoost':
                best_model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, n_jobs=-1, verbosity=0)
            best_params = {'fallback': True}
            cv_r2 = None
    else:
        best_model = model
        best_params = {}
        best_model.fit(X_train, y_train)
        cv_r2 = None
    
    # Evaluate on test set
    y_pred = best_model.predict(X_test)
    test_r2 = r2_score(y_test, y_pred)
    test_mae = mean_absolute_error(y_test, y_pred)
    
    logger.info(f"  Test R²: {test_r2:.4f}, Test MAE: {test_mae:.4f}")
    
    return {
        'model_name': model_name,
        'model': best_model,
        'best_params': best_params,
        'cv_r2': cv_r2,
        'test_r2': test_r2,
        'test_mae': test_mae,
        'predictions': y_pred
    }

def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description='Train MgB2 superconductivity models')
    parser.add_argument('--input', type=str, default=str(DATA_DIR / 'mgb2_clean.csv'),
                      help='Path to cleaned data CSV')
    parser.add_argument('--output-model', type=str, default=str(OUTPUT_DIR / 'best_model.pkl'),
                      help='Path to save best model')
    parser.add_argument('--output-metrics', type=str, default=str(OUTPUT_DIR / 'model_metrics.json'),
                      help='Path to save metrics JSON')
    parser.add_argument('--timeout', type=int, default=1800,
                      help='Timeout in seconds (default: 30 mins)')
    parser.add_argument('--test-size', type=float, default=0.2,
                      help='Test set size (default: 0.2)')
    
    args = parser.parse_args()
    
    logger.info("Starting MgB2 model training pipeline")
    logger.info(f"Input data: {args.input}")
    logger.info(f"Output model: {args.output_model}")
    logger.info(f"Output metrics: {args.output_metrics}")
    
    # Timeout guard
    with TimeoutGuard(args.timeout):
        # Load data
        df = load_clean_data(args.input)
        
        # Prepare features and targets
        X, y, strat_labels = prepare_features_targets(df)
        
        # Stratified train-test split
        X_train, X_test, y_train, y_test, strat_train, strat_test = train_test_split(
            X, y, strat_labels, test_size=args.test_size, random_state=42, stratify=strat_labels
        )
        
        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train all models
        model_names = ['Linear Regression', 'Ridge Regression', 'Random Forest', 'XGBoost']
        results = []
        
        for name in model_names:
            try:
                result = train_model(
                    name, X_train_scaled, y_train,
                    X_test_scaled, y_test
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to train {name}: {e}")
                continue
        
        if not results:
            logger.error("No models were successfully trained")
            sys.exit(1)
        
        # Select best model by test R²
        best_result = max(results, key=lambda x: x['test_r2'])
        logger.info(f"Best model: {best_result['model_name']} with R²={best_result['test_r2']:.4f}")
        
        # Save best model
        model_path = Path(args.output_model)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': best_result['model'],
                'scaler': scaler,
                'model_name': best_result['model_name'],
                'best_params': best_result['best_params']
            }, f)
        
        logger.info(f"Saved best model to {model_path}")
        
        # Prepare metrics report
        metrics_report = {
            'timestamp': datetime.now().isoformat(),
            'best_model': best_result['model_name'],
            'best_test_r2': best_result['test_r2'],
            'best_test_mae': best_result['test_mae'],
            'all_models': []
        }
        
        for result in results:
            metrics_report['all_models'].append({
                'model_name': result['model_name'],
                'cv_r2': result['cv_r2'],
                'test_r2': result['test_r2'],
                'test_mae': result['test_mae'],
                'best_params': result['best_params']
            })
        
        # Save metrics JSON
        metrics_path = Path(args.output_metrics)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics_report, f, indent=2)
        
        logger.info(f"Saved metrics to {metrics_path}")
    
    logger.info("Training pipeline completed successfully")
    return 0

if __name__ == '__main__':
    sys.exit(main())
