import os
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
from config import PROCESSED_DATA_DIR, MODELS_DIR, OUTPUTS_DIR
from utils.logging import setup_logger
from utils.logging_metrics import log_training_metrics

# Setup logger
logger = setup_logger(__name__)

def main():
    """Train baseline Gradient Boosting model on Magpie features."""
    logger.info("Starting baseline model training...")

    # Load features
    features_path = PROCESSED_DATA_DIR / "baseline_features.parquet"
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found: {features_path}")

    df = pd.read_parquet(features_path)
    logger.info(f"Loaded {len(df)} samples with {len(df.columns)} features")

    # Prepare features and target
    # Assume 'formation_energy' is the target
    if 'formation_energy' not in df.columns:
        raise ValueError("formation_energy column not found in features")

    feature_cols = [col for col in df.columns if col != 'formation_energy']
    X = df[feature_cols]
    y = df['formation_energy']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    logger.info(f"Training set: {len(X_train)} samples, Test set: {len(X_test)} samples")

    # Define hyperparameter grid
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.05, 0.1, 0.2]
    }

    # Initialize model
    base_model = GradientBoostingRegressor(random_state=42)

    # Grid search
    logger.info("Performing hyperparameter tuning...")
    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=3,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1
    )

    grid_search.fit(X_train, y_train)

    # Get best model and parameters
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    best_score = grid_search.best_score_

    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV score: {best_score:.4f}")

    # Evaluate on test set
    y_pred = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    logger.info(f"Test MAE: {mae:.4f}")
    logger.info(f"Test RMSE: {rmse:.4f}")

    # Save model
    model_path = MODELS_DIR / "baseline_model.pkl"
    joblib.dump(best_model, model_path)
    logger.info(f"Saved model to {model_path}")

    # Save tuning results
    tuning_results = {
        'best_params': best_params,
        'best_cv_score': float(best_score),
        'test_mae': float(mae),
        'test_rmse': float(rmse),
        'n_train_samples': len(X_train),
        'n_test_samples': len(X_test),
        'n_features': len(feature_cols)
    }

    tuning_path = OUTPUTS_DIR / "baseline_tuning_results.json"
    with open(tuning_path, 'w') as f:
        json.dump(tuning_results, f, indent=2)
    logger.info(f"Saved tuning results to {tuning_path}")

    # Log training metrics
    log_training_metrics({
        'model_type': 'GradientBoostingRegressor',
        'mae': mae,
        'rmse': rmse,
        'best_params': best_params
    })

    return best_model, mae, rmse

if __name__ == "__main__":
    main()
