import os
import sys
import json
import logging
import pickle
import time
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score
from utils import setup_logging, load_state, update_state, compute_file_hash

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    """Load cleaned data and feature subsets."""
    data_path = "data/processed/cleaned_316L.csv"
    X_raw_path = "data/processed/X_raw.csv"
    X_derived_path = "data/processed/X_derived.csv"
    
    df = pd.read_csv(data_path)
    X_raw = pd.read_csv(X_raw_path) if os.path.exists(X_raw_path) else None
    X_derived = pd.read_csv(X_derived_path) if os.path.exists(X_derived_path) else None
    
    y = df['porosity'].values
    return df, X_raw, X_derived, y

def train_gradient_boosting(X, y, n_estimators=100, max_depth=3):
    model = GradientBoostingRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    model.fit(X, y)
    return model

def train_mlp(X, y, hidden_layer_sizes=(100,), max_iter=500, random_state=42):
    model = MLPRegressor(hidden_layer_sizes=hidden_layer_sizes, max_iter=max_iter, random_state=random_state)
    model.fit(X, y)
    return model

def train_dummy_baseline(X, y):
    model = DummyRegressor(strategy='mean')
    model.fit(X, y)
    return model

def compute_metrics(model, X, y):
    y_pred = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    return {'rmse': rmse, 'r2': r2}

def run_manual_cv(model_func, X, y, n_splits=5, random_state=42):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    metrics = []
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        model = model_func(X_train, y_train)
        m = compute_metrics(model, X_test, y_test)
        metrics.append(m)
    
    mean_metrics = {
        'rmse': np.mean([m['rmse'] for m in metrics]),
        'r2': np.mean([m['r2'] for m in metrics]),
        'fold_r2': [m['r2'] for m in metrics]
    }
    return mean_metrics

def save_model(model, path):
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def check_success_criteria(model_metrics, dummy_metrics, subset_name):
    best_r2 = model_metrics['r2']
    dummy_r2 = dummy_metrics['r2']
    
    # SC-001: R2 > Dummy R2 OR R2 >= 0.65
    passed = (best_r2 > dummy_r2) or (best_r2 >= 0.65)
    
    result = {
        'subset': subset_name,
        'model_r2': best_r2,
        'dummy_r2': dummy_r2,
        'sc001_passed': passed,
        'reason': "PASS" if passed else "FAIL"
    }
    
    if not passed:
        raise RuntimeError(f"Success Criterion SC-001 Failed for {subset_name}: R2={best_r2}, Dummy R2={dummy_r2}")
    
    return result

def main():
    setup_logging()
    logging.info("Starting Model Training Pipeline (US2)")
    
    df, X_raw, X_derived, y = load_data()
    
    results_raw = {}
    results_derived = {}
    
    # --- Raw Subset ---
    if X_raw is not None and not X_raw.empty:
        logging.info("Training on Raw Subset...")
        X = X_raw.values
        
        # Models
        gb_metrics = run_manual_cv(lambda X_t, y_t: train_gradient_boosting(X_t, y_t), X, y)
        mlp_metrics = run_manual_cv(lambda X_t, y_t: train_mlp(X_t, y_t), X, y)
        dummy_metrics = run_manual_cv(lambda X_t, y_t: train_dummy_baseline(X_t, y_t), X, y)
        
        # Check SC-001
        sc001_raw = check_success_criteria(gb_metrics, dummy_metrics, "raw")
        
        results_raw = {
            'GradientBoosting': gb_metrics,
            'MLP': mlp_metrics,
            'Dummy': dummy_metrics,
            'sc001_success_check': sc001_raw
        }
        
        # Save best model (GB assumed best if R2 > 0.65, else pick best)
        best_model = train_gradient_boosting(X, y)
        save_model(best_model, "models/artifacts/best_raw_model.pkl")
        logging.info("Saved best raw model.")
    
    # --- Derived Subset ---
    if X_derived is not None and not X_derived.empty:
        logging.info("Training on Derived Subset...")
        X = X_derived[['energy_density']].values # Use only Ev for derived
        # Note: X_derived has ['energy_density', 'porosity'], we need features only
        # But train_models expects X and y separately. 
        # X_derived in preprocess contains Ev and porosity.
        # So we take Ev as feature.
        
        gb_metrics = run_manual_cv(lambda X_t, y_t: train_gradient_boosting(X_t, y_t), X, y)
        mlp_metrics = run_manual_cv(lambda X_t, y_t: train_mlp(X_t, y_t), X, y)
        dummy_metrics = run_manual_cv(lambda X_t, y_t: train_dummy_baseline(X_t, y_t), X, y)
        
        sc001_derived = check_success_criteria(gb_metrics, dummy_metrics, "derived")
        
        results_derived = {
            'GradientBoosting': gb_metrics,
            'MLP': mlp_metrics,
            'Dummy': dummy_metrics,
            'sc001_success_check': sc001_derived
        }
        
        best_model = train_gradient_boosting(X, y)
        save_model(best_model, "models/artifacts/best_derived_model.pkl")
        logging.info("Saved best derived model.")
    
    # Save reports
    results_dir = Path("results/reports")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    if results_raw:
        with open(results_dir / "model_metrics_raw.json", 'w') as f:
            json.dump(results_raw, f, indent=2)
    
    if results_derived:
        with open(results_dir / "model_metrics_derived.json", 'w') as f:
            json.dump(results_derived, f, indent=2)
    
    # Update state
    state_path = "state/state.yaml"
    state = load_state(state_path)
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    # Hash models
    if os.path.exists("models/artifacts/best_raw_model.pkl"):
        state['artifact_hashes']['best_raw_model'] = compute_file_hash("models/artifacts/best_raw_model.pkl")
    if os.path.exists("models/artifacts/best_derived_model.pkl"):
        state['artifact_hashes']['best_derived_model'] = compute_file_hash("models/artifacts/best_derived_model.pkl")
    update_state(state, state_path)
    
    logging.info("Model training complete.")

if __name__ == "__main__":
    main()
