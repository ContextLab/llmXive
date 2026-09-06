"""
Train a Random Forest model on the processed alloy data.
Performs train-test split, cross-validation, and final evaluation.
"""
import logging
import sys
import os
import json
import pickle
from typing import Dict, Any, Tuple, List
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_squared_error
import numpy as np

# Add parent directory to path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_logger, ensure_dir

# Constants
DATA_PATH = "data/processed/processed_alloys.csv"
MODEL_DIR = "data/models"
CV_METRICS_PATH = os.path.join(MODEL_DIR, "cv_metrics.json")
MODEL_PATH = os.path.join(MODEL_DIR, "random_forest_model.pkl")
NULL_MODEL_RMSE_PATH = os.path.join(MODEL_DIR, "null_model_rmse.json")
NULL_MODEL_PREDICTIONS_PATH = os.path.join(MODEL_DIR, "null_model_predictions.npy")

def load_data() -> Tuple[pd.DataFrame, pd.Series]:
    """Load processed alloy data and split features/target."""
    logger = get_logger(__name__)
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Processed data not found at {DATA_PATH}. Run ingestion.py first.")
    
    df = pd.read_csv(DATA_PATH)
    
    # Expected feature columns based on T014, T015 implementation
    # These must exist in the processed CSV
    feature_cols = [
        'mixing_enthalpy', 
        'atomic_size_mismatch', 
        'electronegativity_variance'
    ]
    
    # Verify all required columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns in {DATA_PATH}: {missing_cols}")
    
    if 'critical_cooling_rate' not in df.columns:
        raise ValueError(f"Target column 'critical_cooling_rate' not found in {DATA_PATH}")
    
    X = df[feature_cols]
    y = df['critical_cooling_rate']
    
    logger.info(f"Loaded data: {X.shape[0]} samples, {X.shape[1]} features")
    return X, y

def train_model(X_train: pd.DataFrame, y_train: pd.Series, random_state: int = 42) -> RandomForestRegressor:
    """Train a Random Forest Regressor."""
    logger = get_logger(__name__)
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    logger.info("Model trained successfully")
    return model

def run_cross_validation(model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series, cv_folds: int = 5) -> Dict[str, Any]:
    """Perform k-fold cross-validation and save metrics."""
    logger = get_logger(__name__)
    ensure_dir(MODEL_DIR)
    
    scores = cross_val_score(model, X, y, cv=cv_folds, scoring='neg_root_mean_squared_error')
    rmse_scores = np.abs(scores)
    
    metrics = {
        "fold_scores": rmse_scores.tolist(),
        "mean_rmse": float(np.mean(rmse_scores)),
        "std_rmse": float(np.std(rmse_scores))
    }
    
    with open(CV_METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Cross-validation completed: Mean RMSE = {metrics['mean_rmse']:.4f} (+/- {metrics['std_rmse']:.4f})")
    return metrics

def evaluate_on_test(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """Evaluate model on held-out test set and return RMSE."""
    logger = get_logger(__name__)
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    logger.info(f"Test set RMSE: {rmse:.4f}")
    return rmse

def save_model(model: RandomForestRegressor, model_path: str) -> None:
    """Save the trained model to disk."""
    logger = get_logger(__name__)
    ensure_dir(os.path.dirname(model_path))
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

def train_and_evaluate_null_model(X_train: pd.DataFrame, y_train: pd.Series, 
                                  X_test: pd.DataFrame, y_test: pd.Series,
                                  random_state: int = 42) -> Dict[str, Any]:
    """Train a DummyRegressor and evaluate on test set."""
    logger = get_logger(__name__)
    
    # Train null model
    null_model = DummyRegressor(strategy='mean', random_state=random_state)
    null_model.fit(X_train, y_train)
    
    # Predict on test set
    null_predictions = null_model.predict(X_test)
    null_rmse = np.sqrt(mean_squared_error(y_test, null_predictions))
    
    # Save predictions
    np.save(NULL_MODEL_PREDICTIONS_PATH, null_predictions)
    
    # Save RMSE metrics
    metrics = {
        "null_model_rmse": float(null_rmse),
        "strategy": "mean"
    }
    with open(NULL_MODEL_RMSE_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Null model (mean strategy) test RMSE: {null_rmse:.4f}")
    return metrics

def run_training() -> None:
    """Main entry point for training pipeline."""
    logger = get_logger(__name__)
    logger.info("Starting training pipeline")
    
    # Load data
    X, y = load_data()
    
    # Train-test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(f"Train set: {X_train.shape[0]}, Test set: {X_test.shape[0]}")
    
    # Train model
    model = train_model(X_train, y_train)
    
    # Cross-validation
    cv_metrics = run_cross_validation(model, X_train, y_train)
    
    # Evaluate on test set
    test_rmse = evaluate_on_test(model, X_test, y_test)
    
    # Save model
    save_model(model, MODEL_PATH)
    
    # Train and evaluate null model
    null_metrics = train_and_evaluate_null_model(X_train, y_train, X_test, y_test)
    
    logger.info("Training pipeline completed successfully")
    
    # Print summary
    print(f"\n=== Training Summary ===")
    print(f"CV Mean RMSE: {cv_metrics['mean_rmse']:.4f}")
    print(f"Test RMSE: {test_rmse:.4f}")
    print(f"Null Model RMSE: {null_metrics['null_model_rmse']:.4f}")
    print(f"Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    run_training()