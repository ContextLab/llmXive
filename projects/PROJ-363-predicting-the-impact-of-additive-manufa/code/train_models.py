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
from sklearn.metrics import mean_squared_error, r2_score
from utils import setup_logging, set_seed, load_state, update_state, compute_file_hash

# Configure logging
logger = setup_logging(__name__)

def load_data(raw_path, subset_path):
    """
    Load the cleaned dataset and the specific feature subset (X_raw or X_derived).
    Returns X (features) and y (target).
    """
    logger.info(f"Loading cleaned data from {raw_path}")
    df = pd.read_csv(raw_path)
    
    logger.info(f"Loading feature subset from {subset_path}")
    X_df = pd.read_csv(subset_path)
    
    # Ensure target is present in the raw dataframe
    if 'porosity' not in df.columns:
        raise ValueError("Target column 'porosity' not found in cleaned dataset.")
    
    y = df['porosity'].values
    X = X_df.values
    
    logger.info(f"Loaded X shape: {X.shape}, y shape: {y.shape}")
    return X, y

def train_gradient_boosting(X, y, cv_folds=5, random_state=42):
    """
    Train a Gradient Boosting Regressor using 5-fold Cross Validation.
    Returns the trained model (fitted on full data for artifact saving) and CV scores.
    """
    logger.info("Training Gradient Boosting Regressor with 5-fold CV...")
    
    # Set seed for reproducibility
    set_seed(random_state)
    
    # Define the model
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=random_state,
        subsample=0.8
    )
    
    # Configure KFold
    kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    
    # Perform cross-validation
    # We use negative MSE from sklearn, convert to RMSE later if needed
    cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_squared_error')
    
    # Calculate R2 scores for CV
    cv_r2_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
    
    # Fit the model on the full dataset for saving as an artifact
    model.fit(X, y)
    
    logger.info(f"Gradient Boosting CV RMSE: {np.sqrt(-cv_scores)}")
    logger.info(f"Gradient Boosting CV R2: {cv_r2_scores}")
    
    return model, cv_scores, cv_r2_scores

def train_mlp(X, y, cv_folds=5, random_state=42, max_iter=1000):
    """
    Train a Multi-Layer Perceptron (MLP) Regressor using 5-fold Cross Validation.
    CPU-only execution enforced (no CUDA).
    """
    logger.info("Training MLP Regressor with 5-fold CV...")
    
    set_seed(random_state)
    
    # Define the model
    # Using a simple architecture suitable for tabular data
    model = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        solver='adam',
        alpha=0.0001,
        batch_size=32,
        learning_rate='adaptive',
        learning_rate_init=0.001,
        max_iter=max_iter,
        random_state=random_state,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=10,
        # Explicitly enforce CPU if torch is available, though sklearn defaults to CPU
        # sklearn MLPRegressor does not have a direct 'device' param like pytorch
        # but it runs on CPU by default.
    )
    
    kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    
    # Cross-validation scores
    cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_squared_error')
    cv_r2_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
    
    # Fit on full data
    model.fit(X, y)
    
    logger.info(f"MLP CV RMSE: {np.sqrt(-cv_scores)}")
    logger.info(f"MLP CV R2: {cv_r2_scores}")
    
    return model, cv_scores, cv_r2_scores

def train_dummy_baseline(X, y, cv_folds=5, random_state=42):
    """
    Train a Dummy Regressor (mean strategy) for baseline comparison (SC-001).
    """
    logger.info("Training Dummy Regressor (Mean Strategy) for baseline...")
    
    set_seed(random_state)
    
    model = DummyRegressor(strategy='mean', random_state=random_state)
    kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    
    cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_squared_error')
    cv_r2_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
    
    model.fit(X, y)
    
    logger.info(f"Dummy CV RMSE: {np.sqrt(-cv_scores)}")
    logger.info(f"Dummy CV R2: {cv_r2_scores}")
    
    return model, cv_scores, cv_r2_scores

def compute_metrics(cv_r2_scores, cv_mse_scores):
    """
    Compute aggregate metrics from CV scores.
    """
    rmse_scores = np.sqrt(-cv_mse_scores)
    mean_rmse = np.mean(rmse_scores)
    std_rmse = np.std(rmse_scores)
    mean_r2 = np.mean(cv_r2_scores)
    std_r2 = np.std(cv_r2_scores)
    
    return {
        'mean_rmse': float(mean_rmse),
        'std_rmse': float(std_rmse),
        'mean_r2': float(mean_r2),
        'std_r2': float(std_r2),
        'fold_rmse': [float(x) for x in rmse_scores],
        'fold_r2': [float(x) for x in cv_r2_scores]
    }

def save_model(model, path):
    """
    Save the trained model to a pickle file.
    """
    logger.info(f"Saving model to {path}")
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def main():
    """
    Main execution function for T022 (and associated US2 tasks).
    Trains Gradient Boosting and MLP on X_raw and X_derived subsets.
    """
    logger.info("Starting Model Training Pipeline (US2)")
    
    # Paths
    base_dir = Path(__file__).parent.parent
    cleaned_data_path = base_dir / "data" / "processed" / "cleaned_316L.csv"
    x_raw_path = base_dir / "data" / "processed" / "X_raw.csv"
    x_derived_path = base_dir / "data" / "processed" / "X_derived.csv"
    
    models_dir = base_dir / "models" / "artifacts"
    results_dir = base_dir / "results" / "reports"
    state_path = base_dir / "state" / "state.yaml"
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    # --- Subset 1: X_raw ---
    logger.info("--- Processing X_raw Subset ---")
    try:
        X_raw, y = load_data(cleaned_data_path, x_raw_path)
    except FileNotFoundError as e:
        logger.error(f"Data files not found. Ensure T018 and T016b are complete: {e}")
        sys.exit(1)
    
    # Train Gradient Boosting on X_raw
    gb_raw_model, gb_raw_mse, gb_raw_r2 = train_gradient_boosting(X_raw, y)
    save_model(gb_raw_model, models_dir / "gb_raw_model.pkl")
    
    # Train MLP on X_raw
    mlp_raw_model, mlp_raw_mse, mlp_raw_r2 = train_mlp(X_raw, y)
    save_model(mlp_raw_model, models_dir / "mlp_raw_model.pkl")
    
    # Train Dummy Baseline on X_raw
    dummy_raw_model, dummy_raw_mse, dummy_raw_r2 = train_dummy_baseline(X_raw, y)
    save_model(dummy_raw_model, models_dir / "dummy_raw_model.pkl")
    
    # Compute Metrics for X_raw
    metrics_raw = {
        'gradient_boosting': compute_metrics(gb_raw_r2, gb_raw_mse),
        'mlp': compute_metrics(mlp_raw_r2, mlp_raw_mse),
        'dummy_baseline': compute_metrics(dummy_raw_r2, dummy_raw_mse)
    }
    
    # SC-001 Check for Raw
    best_raw_r2 = max(metrics_raw['gradient_boosting']['mean_r2'], metrics_raw['mlp']['mean_r2'])
    dummy_raw_r2_val = metrics_raw['dummy_baseline']['mean_r2']
    
    sc001_pass = (best_raw_r2 > dummy_raw_r2_val) or (best_raw_r2 >= 0.65)
    metrics_raw['sc001_success_check'] = {
        'best_model_r2': best_raw_r2,
        'dummy_r2': dummy_raw_r2_val,
        'passed': sc001_pass,
        'condition': f"({best_raw_r2:.4f} > {dummy_raw_r2_val:.4f}) OR ({best_raw_r2:.4f} >= 0.65)"
    }
    
    if not sc001_pass:
        logger.warning(f"SC-001 Failed for X_raw: Best R2 ({best_raw_r2}) <= Dummy R2 ({dummy_raw_r2_val}) AND < 0.65")
        # Note: Task T027b handles the strict raise, but we log here for visibility
    
    # Save Raw Metrics
    raw_metrics_path = results_dir / "model_metrics_raw.json"
    with open(raw_metrics_path, 'w') as f:
        json.dump(metrics_raw, f, indent=2)
    logger.info(f"Saved raw metrics to {raw_metrics_path}")
    
    # --- Subset 2: X_derived ---
    logger.info("--- Processing X_derived Subset ---")
    try:
        X_derived, y = load_data(cleaned_data_path, x_derived_path)
    except FileNotFoundError as e:
        logger.error(f"Derived data files not found. Ensure T016b is complete: {e}")
        sys.exit(1)
    
    # Train Gradient Boosting on X_derived
    gb_derived_model, gb_derived_mse, gb_derived_r2 = train_gradient_boosting(X_derived, y)
    save_model(gb_derived_model, models_dir / "gb_derived_model.pkl")
    
    # Train MLP on X_derived
    mlp_derived_model, mlp_derived_mse, mlp_derived_r2 = train_mlp(X_derived, y)
    save_model(mlp_derived_model, models_dir / "mlp_derived_model.pkl")
    
    # Train Dummy Baseline on X_derived
    dummy_derived_model, dummy_derived_mse, dummy_derived_r2 = train_dummy_baseline(X_derived, y)
    save_model(dummy_derived_model, models_dir / "dummy_derived_model.pkl")
    
    # Compute Metrics for X_derived
    metrics_derived = {
        'gradient_boosting': compute_metrics(gb_derived_r2, gb_derived_mse),
        'mlp': compute_metrics(mlp_derived_r2, mlp_derived_mse),
        'dummy_baseline': compute_metrics(dummy_derived_r2, dummy_derived_mse)
    }
    
    # SC-001 Check for Derived
    best_derived_r2 = max(metrics_derived['gradient_boosting']['mean_r2'], metrics_derived['mlp']['mean_r2'])
    dummy_derived_r2_val = metrics_derived['dummy_baseline']['mean_r2']
    
    sc001_pass_derived = (best_derived_r2 > dummy_derived_r2_val) or (best_derived_r2 >= 0.65)
    metrics_derived['sc001_success_check'] = {
        'best_model_r2': best_derived_r2,
        'dummy_r2': dummy_derived_r2_val,
        'passed': sc001_pass_derived,
        'condition': f"({best_derived_r2:.4f} > {dummy_derived_r2_val:.4f}) OR ({best_derived_r2:.4f} >= 0.65)"
    }
    
    if not sc001_pass_derived:
        logger.warning(f"SC-001 Failed for X_derived: Best R2 ({best_derived_r2}) <= Dummy R2 ({dummy_derived_r2_val}) AND < 0.65")
    
    # Save Derived Metrics
    derived_metrics_path = results_dir / "model_metrics_derived.json"
    with open(derived_metrics_path, 'w') as f:
        json.dump(metrics_derived, f, indent=2)
    logger.info(f"Saved derived metrics to {derived_metrics_path}")
    
    # Update State
    logger.info("Updating state.yaml with model artifacts and metrics hashes...")
    state = load_state(state_path)
    
    # Hash models
    model_files = [
        "models/artifacts/gb_raw_model.pkl",
        "models/artifacts/mlp_raw_model.pkl",
        "models/artifacts/gb_derived_model.pkl",
        "models/artifacts/mlp_derived_model.pkl",
        "models/artifacts/dummy_raw_model.pkl",
        "models/artifacts/dummy_derived_model.pkl"
    ]
    
    for rel_path in model_files:
        full_path = base_dir / rel_path
        if full_path.exists():
            h = compute_file_hash(full_path)
            state['artifacts'][rel_path] = h
    
    # Hash metrics
    for rel_path in ["results/reports/model_metrics_raw.json", "results/reports/model_metrics_derived.json"]:
        full_path = base_dir / rel_path
        if full_path.exists():
            h = compute_file_hash(full_path)
            state['artifacts'][rel_path] = h
    
    update_state(state_path, state)
    logger.info("State updated successfully.")
    
    logger.info("Model Training Pipeline completed.")

if __name__ == "__main__":
    main()