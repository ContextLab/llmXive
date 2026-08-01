import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score

# Local imports based on provided API surface
from utils.logging_config import get_logger, log_pipeline_event
from utils.config import get_config_summary
from data.preprocess import split_data, load_raw_data

logger = get_logger(__name__)

def load_data(features_path: str) -> pd.DataFrame:
    """Load the processed features dataset."""
    logger.info(f"Loading data from {features_path}")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    df = pd.read_csv(features_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def inner_loop_cv_selection(train_df: pd.DataFrame, target_col: str = 'decomposition_energy') -> Tuple[Dict[str, Any], RandomForestRegressor]:
    """
    Perform 5-fold CV Grid Search to select best hyperparameters.
    Returns best_params dict and the best estimator.
    """
    logger.info("Starting inner-loop CV for hyperparameter selection...")
    
    X = train_df.drop(columns=[target_col])
    y = train_df[target_col]

    param_grid = {
        'max_depth': [10, 15, 20],
        'min_samples_leaf': [1, 2, 4]
    }

    base_model = RandomForestRegressor(random_state=42, n_jobs=-1)
    
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=5,
        scoring='neg_mean_squared_error',
        n_jobs=-1,
        verbose=1
    )

    grid_search.fit(X, y)

    best_params = grid_search.best_params_
    best_model = grid_search.best_estimator_

    logger.info(f"Best parameters found: {best_params}")
    logger.info(f"Best CV score (neg MSE): {grid_search.best_score_}")

    return best_params, best_model

def train_model(train_df: pd.DataFrame, target_col: str = 'decomposition_energy', best_params: Optional[Dict[str, Any]] = None) -> RandomForestRegressor:
    """
    Train the final model on the full training set using best parameters.
    If best_params is provided, uses them; otherwise performs CV selection internally.
    """
    if best_params is None:
        logger.warning("No best_params provided. Running CV selection first.")
        best_params, _ = inner_loop_cv_selection(train_df, target_col)

    logger.info(f"Training final model with params: {best_params}")
    
    X = train_df.drop(columns=[target_col])
    y = train_df[target_col]

    model = RandomForestRegressor(**best_params, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    logger.info("Model training completed.")
    return model

def evaluate_model(model: RandomForestRegressor, test_df: pd.DataFrame, target_col: str = 'decomposition_energy') -> Dict[str, float]:
    """
    Evaluate the model on the held-out test set.
    Calculates RMSE and R2, and logs the test RMSE to results/metrics.json.
    """
    logger.info("Evaluating model on held-out test set...")
    
    X_test = test_df.drop(columns=[target_col])
    y_test = test_df[target_col]

    y_pred = model.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    logger.info(f"Test RMSE: {rmse:.4f} eV/atom")
    logger.info(f"Test R2 Score: {r2:.4f}")

    # Prepare metrics dictionary
    metrics = {
        "rmse": float(rmse),
        "r2_score": float(r2),
        "test_size": len(test_df),
        "model_type": "RandomForestRegressor"
    }

    # Ensure results directory exists
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    metrics_path = results_dir / "metrics.json"
    
    # Load existing metrics if present, to preserve other info (like low confidence flag)
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            existing_metrics = json.load(f)
        existing_metrics.update(metrics)
        metrics = existing_metrics
    
    # Save to results/metrics.json
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {metrics_path}")

    return metrics

def run_permutation_sensitivity_analysis(model: RandomForestRegressor, test_df: pd.DataFrame, target_col: str = 'decomposition_energy') -> None:
    """
    Placeholder for permutation importance logic (T028).
    This function is called by main but implementation is deferred to T028.
    """
    logger.info("Permutation sensitivity analysis skipped in this task (T028).")

def save_artifacts(model: RandomForestRegressor, metrics: Dict[str, Any]) -> None:
    """
    Save the trained model and metrics to disk.
    Note: T031 handles saving model.pkl, but we ensure metrics.json is here as per T026.
    """
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # Save model (T031 requirement, done here to ensure pipeline flow)
    model_path = results_dir / "model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

    # Metrics are already saved in evaluate_model, but we log it here for clarity
    logger.info("Artifacts saved successfully.")

def main():
    """
    Main execution entry point for T026.
    1. Load processed features.
    2. Split data (80/20) - assuming T022 split_data is available or we re-split.
       Since T022 is marked completed, we rely on the split data files if they exist,
       or re-split if the task implies training on the split set directly.
       Based on T022 description: "split_data function ... save processed data".
       We assume data/processed/train.csv and data/processed/test.csv exist or we split here.
       To be safe and robust: if split files exist, load them. If not, split in memory.
    3. Train model (inner loop CV if needed).
    4. Evaluate on test set -> T026 core.
    5. Save artifacts.
    """
    logger.info("Starting Model Training and Evaluation Pipeline (T026).")
    
    features_path = "data/processed/features.csv"
    
    # Check for split files first (as per T022 expectation)
    train_path = "data/processed/train.csv"
    test_path = "data/processed/test.csv"

    if os.path.exists(train_path) and os.path.exists(test_path):
        logger.info("Loading pre-split train and test sets.")
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
    else:
        logger.info("Pre-split files not found. Loading full features and splitting.")
        full_df = load_data(features_path)
        train_df, test_df = split_data(full_df, target_col='decomposition_energy')
        # Save splits if they didn't exist (T022 side effect)
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)
        logger.info(f"Saved splits to {train_path} and {test_path}")

    # Inner loop CV and Training
    best_params, best_model = inner_loop_cv_selection(train_df)
    final_model = train_model(train_df, best_params=best_params)

    # T026: Evaluation
    metrics = evaluate_model(final_model, test_df)

    # Save artifacts (Model and updated metrics)
    save_artifacts(final_model, metrics)

    logger.info("Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()