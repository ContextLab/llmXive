import os
import sys
import json
import logging
import pickle
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, KFold
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.dummy import DummyRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import make_scorer, r2_score, mean_squared_error
from pathlib import Path

# Import local utilities
from utils import setup_logging, set_seed, load_state, update_state, compute_file_hash

# Setup logging
logger = setup_logging()

def load_data():
    """Load the preprocessed dataset."""
    data_path = Path("data/processed/cleaned_316L.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}. Run preprocessing first.")
    
    df = pd.read_csv(data_path)
    
    # Define features and target based on spec
    # Assuming columns: power, speed, hatch, thickness, energy_density, porosity
    # Features: power, speed, hatch, thickness (normalized or raw depending on preprocessing)
    # Target: porosity
    
    feature_cols = ['power', 'speed', 'hatch', 'thickness']
    target_col = 'porosity'
    
    # Check if energy_density exists and if we should use it instead of raw params to avoid multicollinearity
    # For US2, we use the normalized features from preprocessing
    if all(col in df.columns for col in feature_cols):
        X = df[feature_cols]
    elif 'energy_density' in df.columns and len(feature_cols) > 0:
        # Fallback or alternative if raw params were dropped
        logger.warning("Raw parameters missing, using energy_density if available")
        X = df[['energy_density']] if 'energy_density' in df.columns else df.drop(columns=[target_col])
    else:
        # Default fallback: drop target and use remaining numeric cols
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if target_col in numeric_cols:
            numeric_cols.remove(target_col)
        X = df[numeric_cols]
    
    y = df[target_col]
    
    return X, y

def train_gradient_boosting(X, y, cv=5, seed=42):
    """Train Gradient Boosting Regressor with 5-fold CV."""
    set_seed(seed)
    
    # Create pipeline with scaling
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=seed
        ))
    ])
    
    kfold = KFold(n_splits=cv, shuffle=True, random_state=seed)
    
    # Compute R2 scores
    r2_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
    
    # Compute RMSE scores (need to use neg_mse and take sqrt)
    neg_mse_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_squared_error')
    rmse_scores = np.sqrt(-neg_mse_scores)
    
    return {
        'model': model,
        'r2_scores': r2_scores.tolist(),
        'rmse_scores': rmse_scores.tolist(),
        'mean_r2': float(np.mean(r2_scores)),
        'mean_rmse': float(np.mean(rmse_scores))
    }

def train_mlp(X, y, cv=5, seed=42):
    """Train MLP Regressor with 5-fold CV."""
    set_seed(seed)
    
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', MLPRegressor(
            hidden_layer_sizes=(100, 50),
            max_iter=500,
            random_state=seed,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=10
        ))
    ])
    
    kfold = KFold(n_splits=cv, shuffle=True, random_state=seed)
    
    r2_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
    neg_mse_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_squared_error')
    rmse_scores = np.sqrt(-neg_mse_scores)
    
    return {
        'model': model,
        'r2_scores': r2_scores.tolist(),
        'rmse_scores': rmse_scores.tolist(),
        'mean_r2': float(np.mean(r2_scores)),
        'mean_rmse': float(np.mean(rmse_scores))
    }

def train_dummy_baseline(X, y, cv=5, seed=42):
    """Train Dummy Regressor (mean strategy) with 5-fold CV for baseline comparison."""
    set_seed(seed)
    
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', DummyRegressor(strategy='mean'))
    ])
    
    kfold = KFold(n_splits=cv, shuffle=True, random_state=seed)
    
    r2_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
    neg_mse_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_squared_error')
    rmse_scores = np.sqrt(-neg_mse_scores)
    
    return {
        'model': model,
        'r2_scores': r2_scores.tolist(),
        'rmse_scores': rmse_scores.tolist(),
        'mean_r2': float(np.mean(r2_scores)),
        'mean_rmse': float(np.mean(rmse_scores))
    }

def compute_metrics(results_dict):
    """Compute aggregate metrics from CV results."""
    return {
        'r2_scores': results_dict['r2_scores'],
        'rmse_scores': results_dict['rmse_scores'],
        'mean_r2': results_dict['mean_r2'],
        'mean_rmse': results_dict['mean_rmse']
    }

def save_model(model, path):
    """Save model to pickle file."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def main():
    """Main execution function for training models and baseline."""
    logger.info("Starting model training pipeline...")
    
    # Load data
    X, y = load_data()
    logger.info(f"Loaded data with {X.shape[0]} samples and {X.shape[1]} features")
    
    # Set seed for reproducibility
    seed = 42
    set_seed(seed)
    
    # Train models
    logger.info("Training Gradient Boosting Regressor...")
    gb_results = train_gradient_boosting(X, y, cv=5, seed=seed)
    
    logger.info("Training MLP Regressor...")
    mlp_results = train_mlp(X, y, cv=5, seed=seed)
    
    logger.info("Training Dummy Baseline Regressor...")
    dummy_results = train_dummy_baseline(X, y, cv=5, seed=seed)
    
    # Determine best model based on mean R2
    models_performance = {
        'GradientBoosting': gb_results['mean_r2'],
        'MLP': mlp_results['mean_r2'],
        'DummyBaseline': dummy_results['mean_r2']
    }
    
    best_model_name = max(models_performance, key=models_performance.get)
    best_model_r2 = models_performance[best_model_name]
    dummy_baseline_r2 = dummy_results['mean_r2']
    
    # SC-001 Verification: Compare best model against dummy baseline
    # PASS if best model R2 > dummy baseline R2
    sc001_pass = best_model_r2 > dummy_baseline_r2
    sc001_result = "PASS" if sc001_pass else "FAIL"
    
    logger.info(f"Best Model: {best_model_name} with R² = {best_model_r2:.4f}")
    logger.info(f"Dummy Baseline R² = {dummy_baseline_r2:.4f}")
    logger.info(f"SC-001 Verification: {sc001_result}")
    
    # Prepare metrics report
    metrics_report = {
        'models': {
            'GradientBoosting': compute_metrics(gb_results),
            'MLP': compute_metrics(mlp_results),
            'DummyBaseline': compute_metrics(dummy_results)
        },
        'best_model': {
            'name': best_model_name,
            'mean_r2': best_model_r2,
            'mean_rmse': models_performance[best_model_name]  # Placeholder, will fix
        },
        'sc001_verification': {
            'best_model_r2': best_model_r2,
            'dummy_baseline_r2': dummy_baseline_r2,
            'result': sc001_result,
            'passed': sc001_pass
        },
        'seed': seed,
        'cv_folds': 5
    }
    
    # Fix best_model rmse
    if best_model_name == 'GradientBoosting':
        metrics_report['best_model']['mean_rmse'] = gb_results['mean_rmse']
    elif best_model_name == 'MLP':
        metrics_report['best_model']['mean_rmse'] = mlp_results['mean_rmse']
    else:
        metrics_report['best_model']['mean_rmse'] = dummy_results['mean_rmse']
    
    # Save models
    models_dir = Path("models/artifacts")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    save_model(gb_results['model'], models_dir / "gradient_boosting.pkl")
    save_model(mlp_results['model'], models_dir / "mlp_regressor.pkl")
    save_model(dummy_results['model'], models_dir / "dummy_baseline.pkl")
    
    # Save metrics report
    results_dir = Path("results/reports")
    results_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = results_dir / "model_metrics.json"
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics_report, f, indent=2)
    
    logger.info(f"Metrics report saved to {metrics_path}")
    
    # Update state.yaml
    state = load_state()
    state['artifacts']['model_metrics'] = {
        'path': str(metrics_path),
        'hash': compute_file_hash(metrics_path)
    }
    state['artifacts']['models'] = {
        'gradient_boosting': {
            'path': str(models_dir / "gradient_boosting.pkl"),
            'hash': compute_file_hash(models_dir / "gradient_boosting.pkl")
        },
        'mlp': {
            'path': str(models_dir / "mlp_regressor.pkl"),
            'hash': compute_file_hash(models_dir / "mlp_regressor.pkl")
        },
        'dummy_baseline': {
            'path': str(models_dir / "dummy_baseline.pkl"),
            'hash': compute_file_hash(models_dir / "dummy_baseline.pkl")
        }
    }
    update_state(state)
    
    logger.info("Model training pipeline completed successfully")
    return metrics_report

if __name__ == "__main__":
    main()
