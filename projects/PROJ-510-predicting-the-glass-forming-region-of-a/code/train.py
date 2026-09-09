"""
Model training module for glass-forming alloy analysis.
Trains Random Forest regressor with cross-validation and null model comparison.
"""
import logging
import sys
import os
import json
import pickle
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold
from sklearn.ensemble import RandomForestRegressor, DummyRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/train.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DATA_PATH = "data/processed/processed_alloys.csv"
MODEL_PATH = "data/models/random_forest_model.pkl"
CV_METRICS_PATH = "data/models/cv_metrics.json"
NULL_MODEL_PATH = "data/models/null_model_cv_scores.json"
NULL_PREDICTIONS_PATH = "data/models/null_model_predictions.npy"
NULL_RMSE_PATH = "data/models/null_model_rmse.json"
TRAIN_VAL_PATH = "data/logs/training_set_validation.json"
MODELS_DIR = "data/models"
LOGS_DIR = "data/logs"

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def load_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load processed data and split into features and target.
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Processed data not found at {DATA_PATH}. Run features.py first.")

    df = pd.read_csv(DATA_PATH)
    
    # Select feature columns
    feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    target_col = 'critical_cooling_rate'

    # Check for required columns
    for col in feature_cols + [target_col]:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    X = df[feature_cols].values
    y = df[target_col].values

    # Check variance
    if np.var(y) == 0:
        raise ValueError("Target variable has zero variance; cannot train regression model.")

    return X, y

def train_model(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestRegressor:
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

def run_cross_validation(model, X: np.ndarray, y: np.ndarray, k: int = 5) -> List[float]:
    """
    Perform k-fold cross-validation and return RMSE scores.
    """
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    scores = []

    for train_idx, val_idx in kf.split(X):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]

        model.fit(X_tr, y_tr)
        y_pred = model.predict(X_val)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        scores.append(rmse)

    return scores

def evaluate_on_test(model, X_test: np.ndarray, y_test: np.ndarray) -> float:
    """
    Evaluate model on test set and return RMSE.
    """
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    return rmse

def save_model(model, path: str):
    """
    Save model to disk.
    """
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def train_and_evaluate_null_model(X_train: np.ndarray, y_train: np.ndarray, 
                                  X_test: np.ndarray, y_test: np.ndarray,
                                  cv_folds: KFold) -> Dict[str, Any]:
    """
    Train a dummy regressor and perform cross-validation.
    """
    # Cross-validation scores
    scores = []
    for train_idx, val_idx in cv_folds.split(X_train):
        X_tr, X_val = X_train[train_idx], X_train[val_idx]
        y_tr, y_val = y_train[train_idx], y_train[val_idx]

        model = DummyRegressor(strategy='mean')
        model.fit(X_tr, y_tr)
        y_pred = model.predict(X_val)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        scores.append(rmse)

    # Test set evaluation
    null_model = DummyRegressor(strategy='mean')
    null_model.fit(X_train, y_train)
    y_pred_test = null_model.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

    return {
        'fold_scores': scores,
        'mean_rmse': np.mean(scores),
        'std_rmse': np.std(scores),
        'test_rmse': test_rmse,
        'predictions': y_pred_test
    }

def run_training():
    """
    Main entry point for model training.
    """
    logger.info("Starting training pipeline")

    # Load data
    X, y = load_data()
    logger.info(f"Loaded data: {X.shape}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Validate training set size
    n_train = len(X_train)
    validation_status = "pass" if n_train >= 500 else "fail"
    if n_train < 500:
        logger.warning(f"SC-001 Violation: Training set size < 500 ({n_train})")
        raise ValueError(f"SC-001 Violation: Training set size < 500 after 80/20 split. Increase raw data or adjust split ratio.")
    
    validation_result = {
        "status": validation_status,
        "n_train": n_train
    }
    with open(TRAIN_VAL_PATH, 'w') as f:
        json.dump(validation_result, f, indent=2)
    logger.info(f"Training set validation: {validation_result}")

    # Create shared CV splitter
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    # Save fold indices (optional, for debugging)
    fold_indices = {
        "train": [train_idx.tolist() for train_idx, _ in kf.split(X_train)],
        "val": [val_idx.tolist() for _, val_idx in kf.split(X_train)]
    }
    with open(os.path.join(MODELS_DIR, "cv_folds_indices.json"), 'w') as f:
        json.dump(fold_indices, f)

    # Train main model
    logger.info("Training Random Forest model")
    rf_model = train_model(X_train, y_train)
    
    # Cross-validation for main model
    logger.info("Running cross-validation for main model")
    cv_scores = run_cross_validation(rf_model, X_train, y_train, k=5)
    cv_metrics = {
        "fold_scores": cv_scores,
        "mean_rmse": np.mean(cv_scores),
        "std_rmse": np.std(cv_scores)
    }
    with open(CV_METRICS_PATH, 'w') as f:
        json.dump(cv_metrics, f, indent=2)
    logger.info(f"CV metrics: {cv_metrics}")

    # Save model
    save_model(rf_model, MODEL_PATH)

    # Evaluate on test set
    test_rmse = evaluate_on_test(rf_model, X_test, y_test)
    logger.info(f"Test set RMSE: {test_rmse}")

    # Train and evaluate null model
    logger.info("Training and evaluating null model")
    null_results = train_and_evaluate_null_model(
        X_train, y_train, X_test, y_test, kf
    )
    
    # Save null model results
    null_cv = {
        "fold_scores": null_results['fold_scores'],
        "mean_rmse": null_results['mean_rmse'],
        "std_rmse": null_results['std_rmse']
    }
    with open(NULL_MODEL_PATH, 'w') as f:
        json.dump(null_cv, f, indent=2)

    np.save(NULL_PREDICTIONS_PATH, null_results['predictions'])
    
    null_rmse_result = {"test_rmse": null_results['test_rmse']}
    with open(NULL_RMSE_PATH, 'w') as f:
        json.dump(null_rmse_result, f, indent=2)

    logger.info("Training pipeline completed")

if __name__ == "__main__":
    run_training()
