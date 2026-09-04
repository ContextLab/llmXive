"""
Model Training Module for Glass Forming Region Prediction.

Trains a Random Forest regressor with cross-validation.
Evaluates against a null model.
"""
import logging
import sys
import os
import json
import pickle
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, DummyRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(DATA_DIR, "models")

def load_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load processed data and perform train-test split.
    """
    data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run ingestion.py first.")
    
    df = pd.read_csv(data_path)
    
    # Select features
    feature_cols = ['atomic_size_mismatch', 'electronegativity_variance']
    # Add mixing_enthalpy if available
    if 'mixing_enthalpy' in df.columns:
        feature_cols.append('mixing_enthalpy')
    
    # Drop rows with NaN in features or target
    df = df.dropna(subset=feature_cols + ['critical_cooling_rate'])
    
    X = df[feature_cols].values
    y = df['critical_cooling_rate'].values
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    logger.info(f"Train set size: {len(X_train)}, Test set size: {len(X_test)}")
    return X_train, X_test, y_train, y_test

def train_model(X_train: np.ndarray, y_train: np.ndarray) -> Any:
    """
    Train a Random Forest regressor.
    """
    model = RandomForestRegressor(
        n_estimators=100, 
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model

def run_cross_validation(model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Perform 5-fold cross-validation.
    """
    scores = cross_val_score(
        model, X, y, cv=5, scoring='neg_mean_squared_error', n_jobs=-1
    )
    rmse_scores = np.sqrt(-scores)
    
    result = {
        'fold_scores': rmse_scores.tolist(),
        'mean_rmse': float(np.mean(rmse_scores))
    }
    return result

def evaluate_on_test(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> float:
    """
    Evaluate model on test set.
    """
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    return float(rmse)

def save_model(model: Any, filepath: str):
    """
    Save model to pickle file.
    """
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {filepath}")

def train_and_evaluate_null_model(X_train: np.ndarray, y_train: np.ndarray, 
                                  X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
    """
    Train a DummyRegressor (mean strategy) and evaluate.
    """
    null_model = DummyRegressor(strategy='mean')
    null_model.fit(X_train, y_train)
    
    y_pred_null = null_model.predict(X_test)
    rmse_null = np.sqrt(mean_squared_error(y_test, y_pred_null))
    
    return {
        'rmse': float(rmse_null)
    }

def run_training():
    """
    Main function to run the training pipeline.
    """
    logger.info("Starting Model Training Pipeline...")
    
    # Ensure output directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Load data
    X_train, X_test, y_train, y_test = load_data()
    
    # Train model
    model = train_model(X_train, y_train)
    
    # Cross-validation
    cv_results = run_cross_validation(model, X_train, y_train)
    cv_path = os.path.join(MODELS_DIR, "cv_metrics.json")
    with open(cv_path, 'w') as f:
        json.dump(cv_results, f, indent=2)
    logger.info(f"CV metrics saved to {cv_path}")
    
    # Evaluate on test set
    test_rmse = evaluate_on_test(model, X_test, y_test)
    logger.info(f"Test RMSE: {test_rmse:.4f}")
    
    # Save model
    model_path = os.path.join(MODELS_DIR, "random_forest_model.pkl")
    save_model(model, model_path)
    
    # Train and evaluate null model
    null_results = train_and_evaluate_null_model(X_train, y_train, X_test, y_test)
    null_path = os.path.join(MODELS_DIR, "null_model_rmse.json")
    with open(null_path, 'w') as f:
        json.dump(null_results, f, indent=2)
    logger.info(f"Null model RMSE saved to {null_path}")
    
    return model, cv_results, null_results

if __name__ == "__main__":
    run_training()
