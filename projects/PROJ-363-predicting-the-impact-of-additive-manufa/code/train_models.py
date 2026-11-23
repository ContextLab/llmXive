import os
import sys
import json
import logging
import pickle
import time
import hashlib
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

# Import utilities from sibling module
from utils import setup_logging, load_state, update_state, compute_file_hash

# Configure logging
logger = setup_logging("train_models")

# Constants
RANDOM_STATE = 42
N_FOLDS = 5
MODELS_DIR = Path("models/artifacts")
RESULTS_DIR = Path("results/reports")
DATA_DIR = Path("data/processed")
STATE_FILE = Path("state.yaml")

def load_data(file_path):
    """Load CSV data and return DataFrame."""
    if not os.path.exists(file_path):
        logger.error(f"Input file not found: {file_path}")
        return None
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def train_gradient_boosting(X, y, random_state=RANDOM_STATE):
    """Train a Gradient Boosting Regressor."""
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=random_state
    )
    model.fit(X, y)
    return model

def train_mlp(X, y, random_state=RANDOM_STATE):
    """Train an MLP Regressor."""
    # Scale data for MLP
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = MLPRegressor(
        hidden_layer_sizes=(100, 50),
        max_iter=500,
        random_state=random_state,
        early_stopping=True,
        validation_fraction=0.1
    )
    model.fit(X_scaled, y)
    return model, scaler

def train_dummy_baseline(X, y, random_state=RANDOM_STATE):
    """Train a Dummy Regressor for baseline comparison."""
    model = DummyRegressor(strategy='mean', random_state=random_state)
    model.fit(X, y)
    return model

def compute_metrics(model, X, y, is_mlp=False, scaler=None):
    """Compute RMSE and R² for a single model on full data (for reporting)."""
    if is_mlp and scaler is not None:
        X_pred = scaler.transform(X)
    else:
        X_pred = X
    
    y_pred = model.predict(X_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    return {"rmse": rmse, "r2": r2}

def run_manual_cv(X, y, model_factory, is_mlp=False, n_folds=N_FOLDS, random_state=RANDOM_STATE):
    """Run k-fold cross-validation manually to compute fold metrics."""
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    fold_rmses = []
    fold_r2s = []
    best_model = None
    best_score = -np.inf
    
    # For MLP, we need to handle scaling per fold
    if is_mlp:
        # We train on the full data for the final model after CV
        scaler_full = StandardScaler()
        X_scaled_full = scaler_full.fit_transform(X)
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train fold model
        if is_mlp:
            scaler_fold = StandardScaler()
            X_train_scaled = scaler_fold.fit_transform(X_train)
            model, _ = model_factory(X_train_scaled, y_train)
            # Predict on test set
            X_test_scaled = scaler_fold.transform(X_test)
            y_pred = model.predict(X_test_scaled)
        else:
            model = model_factory(X_train, y_train)
            y_pred = model.predict(X_test)
        
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        fold_rmses.append(rmse)
        fold_r2s.append(r2)
        
        # Track best model based on R2
        if r2 > best_score:
            best_score = r2
            best_model = model
            if is_mlp:
                best_scaler = scaler_fold

    mean_rmse = np.mean(fold_rmses)
    mean_r2 = np.mean(fold_r2s)
    
    return {
        "fold_rmses": fold_rmses,
        "fold_r2s": fold_r2s,
        "mean_rmse": mean_rmse,
        "mean_r2": mean_r2,
        "best_model": best_model,
        "best_score": best_score,
        "best_scaler": best_scaler if is_mlp else None
    }

def save_model(model, path, scaler=None):
    """Save model (and scaler if present) to pickle file."""
    with open(path, 'wb') as f:
        if scaler is not None:
            pickle.dump({'model': model, 'scaler': scaler}, f)
        else:
            pickle.dump(model, f)
    logger.info(f"Saved model to {path}")

def load_model(path):
    """Load model from pickle file."""
    with open(path, 'rb') as f:
        data = pickle.load(f)
        if isinstance(data, dict):
            return data['model'], data['scaler']
        return data, None

def check_success_criteria(best_r2, dummy_r2):
    """Check SC-001: (Best Model R² > Dummy R²) OR (Best Model R² ≥ 0.65)."""
    passed = (best_r2 > dummy_r2) or (best_r2 >= 0.65)
    return passed

def main():
    logger.info("Starting Model Training (US2)")
    
    # Ensure directories exist
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data subsets
    cleaned_path = DATA_DIR / "cleaned_316L.csv"
    X_raw_path = DATA_DIR / "X_raw.csv"
    X_derived_path = DATA_DIR / "X_derived.csv"
    
    # We expect cleaned_316L.csv to have 'porosity' as target
    # X_raw.csv and X_derived.csv are feature subsets
    
    # Check if X_raw exists
    use_raw = X_raw_path.exists()
    use_derived = X_derived_path.exists()
    
    if not use_raw and not use_derived:
        logger.error("Neither X_raw.csv nor X_derived.csv found. Cannot train models.")
        sys.exit(1)
    
    # Load target from cleaned dataset
    cleaned_df = load_data(cleaned_path)
    if cleaned_df is None:
        sys.exit(1)
    y = cleaned_df['porosity']
    
    results_raw = None
    results_derived = None
    
    # Train on Raw Subset (if exists)
    if use_raw:
        logger.info("Training on Raw Subset...")
        X_raw = load_data(X_raw_path)
        if X_raw is None:
            sys.exit(1)
        
        # Train Gradient Boosting
        gb_cv_raw = run_manual_cv(X_raw, y, train_gradient_boosting, is_mlp=False)
        # Train MLP
        mlp_cv_raw = run_manual_cv(X_raw, y, train_mlp, is_mlp=True)
        
        # Compare and select best
        if gb_cv_raw['mean_r2'] >= mlp_cv_raw['mean_r2']:
            best_raw_model = gb_cv_raw['best_model']
            best_raw_scaler = None
            best_raw_type = "GradientBoosting"
            best_raw_r2 = gb_cv_raw['mean_r2']
        else:
            best_raw_model = mlp_cv_raw['best_model']
            best_raw_scaler = mlp_cv_raw['best_scaler']
            best_raw_type = "MLP"
            best_raw_r2 = mlp_cv_raw['mean_r2']
        
        # Dummy baseline
        dummy_raw = train_dummy_baseline(X_raw, y)
        dummy_raw_r2 = dummy_raw.score(X_raw, y)
        
        # Full data metrics for best model
        full_metrics_raw = compute_metrics(best_raw_model, X_raw, y, is_mlp=(best_raw_type=="MLP"), scaler=best_raw_scaler)
        
        # Check SC-001
        sc001_pass = check_success_criteria(best_raw_r2, dummy_raw_r2)
        
        results_raw = {
            "subset": "raw",
            "best_model_type": best_raw_type,
            "mean_r2": best_raw_r2,
            "mean_rmse": gb_cv_raw['mean_rmse'] if best_raw_type == "GradientBoosting" else mlp_cv_raw['mean_rmse'],
            "fold_r2s": gb_cv_raw['fold_r2s'] if best_raw_type == "GradientBoosting" else mlp_cv_raw['fold_r2s'],
            "fold_rmses": gb_cv_raw['fold_rmses'] if best_raw_type == "GradientBoosting" else mlp_cv_raw['fold_rmses'],
            "dummy_r2": dummy_raw_r2,
            "sc001_passed": sc001_pass,
            "full_data_metrics": full_metrics_raw
        }
        
        # Save model
        save_model(best_raw_model, MODELS_DIR / "best_raw_model.pkl", scaler=best_raw_scaler)
        
        logger.info(f"Raw Subset - Best Model: {best_raw_type}, R²: {best_raw_r2:.4f}, SC-001: {'PASS' if sc001_pass else 'FAIL'}")
    
    # Train on Derived Subset (always exists per spec)
    logger.info("Training on Derived Subset...")
    X_derived = load_data(X_derived_path)
    if X_derived is None:
        sys.exit(1)
    
    # Train Gradient Boosting
    gb_cv_derived = run_manual_cv(X_derived, y, train_gradient_boosting, is_mlp=False)
    # Train MLP
    mlp_cv_derived = run_manual_cv(X_derived, y, train_mlp, is_mlp=True)
    
    # Compare and select best
    if gb_cv_derived['mean_r2'] >= mlp_cv_derived['mean_r2']:
        best_derived_model = gb_cv_derived['best_model']
        best_derived_scaler = None
        best_derived_type = "GradientBoosting"
        best_derived_r2 = gb_cv_derived['mean_r2']
    else:
        best_derived_model = mlp_cv_derived['best_model']
        best_derived_scaler = mlp_cv_derived['best_scaler']
        best_derived_type = "MLP"
        best_derived_r2 = mlp_cv_derived['mean_r2']
    
    # Dummy baseline
    dummy_derived = train_dummy_baseline(X_derived, y)
    dummy_derived_r2 = dummy_derived.score(X_derived, y)
    
    # Full data metrics
    full_metrics_derived = compute_metrics(best_derived_model, X_derived, y, is_mlp=(best_derived_type=="MLP"), scaler=best_derived_scaler)
    
    # Check SC-001
    sc001_pass_derived = check_success_criteria(best_derived_r2, dummy_derived_r2)
    
    results_derived = {
        "subset": "derived",
        "best_model_type": best_derived_type,
        "mean_r2": best_derived_r2,
        "mean_rmse": gb_cv_derived['mean_rmse'] if best_derived_type == "GradientBoosting" else mlp_cv_derived['mean_rmse'],
        "fold_r2s": gb_cv_derived['fold_r2s'] if best_derived_type == "GradientBoosting" else mlp_cv_derived['fold_r2s'],
        "fold_rmses": gb_cv_derived['fold_rmses'] if best_derived_type == "GradientBoosting" else mlp_cv_derived['fold_rmses'],
        "dummy_r2": dummy_derived_r2,
        "sc001_passed": sc001_pass_derived,
        "full_data_metrics": full_metrics_derived
    }
    
    # Save model
    save_model(best_derived_model, MODELS_DIR / "best_derived_model.pkl", scaler=best_derived_scaler)
    
    logger.info(f"Derived Subset - Best Model: {best_derived_type}, R²: {best_derived_r2:.4f}, SC-001: {'PASS' if sc001_pass_derived else 'FAIL'}")
    
    # Save metrics reports
    if results_raw:
        with open(RESULTS_DIR / "model_metrics_raw.json", 'w') as f:
            json.dump(results_raw, f, indent=2)
    
    with open(RESULTS_DIR / "model_metrics_derived.json", 'w') as f:
        json.dump(results_derived, f, indent=2)
    
    # Update state.yaml with hashes
    state = load_state(STATE_FILE)
    if state is None:
        state = {"artifact_hashes": {}, "gate_verified": False, "degenerate": False}
    
    if results_raw:
        state["artifact_hashes"]["best_raw_model"] = compute_file_hash(MODELS_DIR / "best_raw_model.pkl")
        state["artifact_hashes"]["model_metrics_raw"] = compute_file_hash(RESULTS_DIR / "model_metrics_raw.json")
    
    state["artifact_hashes"]["best_derived_model"] = compute_file_hash(MODELS_DIR / "best_derived_model.pkl")
    state["artifact_hashes"]["model_metrics_derived"] = compute_file_hash(RESULTS_DIR / "model_metrics_derived.json")
    
    update_state(state, STATE_FILE)
    
    logger.info("Model training completed successfully.")

if __name__ == "__main__":
    main()