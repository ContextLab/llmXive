import os
import sys
import logging
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score
from utils.logger import get_logger
from utils.config import get_config

# Initialize logger
logger = get_logger(__name__)
config = get_config()

def load_window_data(window_path: Path) -> tuple:
    """
    Load window data from a CSV file.
    Returns features (X) and target (y) as numpy arrays.
    """
    logger.info(f"Loading window data from {window_path}")
    df = pd.read_csv(window_path)
    
    # Assume the last column is the target
    feature_cols = df.columns[:-1].tolist()
    target_col = df.columns[-1]
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    logger.info(f"Loaded window with shape {X.shape} and target shape {y.shape}")
    return X, y, feature_cols

def prepare_features_target(X: np.ndarray, y: np.ndarray) -> tuple:
    """
    Prepare features and target for model training.
    Ensures correct data types and handles any preprocessing if needed.
    """
    # Convert to float64 for sklearn
    X = X.astype(np.float64)
    y = y.astype(np.float64)
    
    # Check for NaNs or Infs
    if np.any(np.isnan(X)) or np.any(np.isinf(X)):
        logger.warning("NaN or Inf values detected in features. Dropping rows.")
        mask = ~(np.isnan(X).any(axis=1) | np.isinf(X).any(axis=1))
        X = X[mask]
        y = y[mask]
    
    if np.any(np.isnan(y)) or np.any(np.isinf(y)):
        logger.warning("NaN or Inf values detected in target. Dropping rows.")
        mask = ~(np.isnan(y) | np.isinf(y))
        X = X[mask]
        y = y[mask]
    
    return X, y

def train_model(X: np.ndarray, y: np.ndarray, seed: int = 42) -> RandomForestRegressor:
    """
    Train a RandomForestRegressor model.
    """
    logger.info("Training RandomForest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=seed,
        n_jobs=-1
    )
    model.fit(X, y)
    logger.info("Model training completed.")
    return model

def evaluate_model(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray) -> float:
    """
    Evaluate model performance using R² score.
    """
    logger.info("Evaluating model performance...")
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    logger.info(f"Model R² score: {r2:.4f}")
    return r2

def validate_model_performance(r2_score_val: float, threshold: float = 0.8) -> bool:
    """
    Validate model performance against a threshold.
    Returns True if R² >= threshold, False otherwise.
    Logs "Model Failure" if validation fails.
    """
    if r2_score_val < threshold:
        logger.error(f"Model Failure: R² score {r2_score_val:.4f} is below threshold {threshold}")
        return False
    logger.info(f"Model validation passed: R² score {r2_score_val:.4f} >= {threshold}")
    return True

def calculate_importance(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray, feature_names: list) -> dict:
    """
    Calculate permutation importance for the trained model.
    """
    logger.info("Calculating permutation importance...")
    result = permutation_importance(
        model, X, y,
        n_repeats=10,
        random_state=42,
        n_jobs=-1,
        scoring='r2'
    )
    
    importance_dict = {}
    for i, name in enumerate(feature_names):
        importance_dict[name] = {
            'mean_importance': float(result.importances_mean[i]),
            'std_importance': float(result.importances_std[i])
        }
    
    logger.info("Permutation importance calculation completed.")
    return importance_dict

def save_importance_profile(importance_dict: dict, window_id: str, output_dir: Path) -> Path:
    """
    Save importance profile to a JSON file.
    """
    output_file = output_dir / f"importance_profile_{window_id}.json"
    logger.info(f"Saving importance profile to {output_file}")
    
    with open(output_file, 'w') as f:
        json.dump({
            'window_id': window_id,
            'importance_scores': importance_dict
        }, f, indent=2)
    
    return output_file

def train_and_compute_importance(window_id: str, window_path: Path, output_dir: Path, r2_threshold: float = 0.8) -> dict:
    """
    Main function to train model, validate performance, and compute importance.
    Returns a dictionary with window_id, r2_score, and importance_scores if successful.
    Returns None if model validation fails.
    """
    logger.info(f"Processing window {window_id}")
    
    # Load data
    X, y, feature_names = load_window_data(window_path)
    
    # Prepare data
    X, y = prepare_features_target(X, y)
    
    # Train model
    model = train_model(X, y)
    
    # Evaluate model
    r2 = evaluate_model(model, X, y)
    
    # Validate model performance (T012 requirement)
    if not validate_model_performance(r2, r2_threshold):
        # Skip this window if R² < 0.8
        return None
    
    # Calculate importance
    importance_scores = calculate_importance(model, X, y, feature_names)
    
    # Save importance profile
    save_importance_profile(importance_scores, window_id, output_dir)
    
    return {
        'window_id': window_id,
        'r2_score': r2,
        'importance_scores': importance_scores
    }

def main():
    """
    Main entry point for the module.
    Processes a single window specified by environment variables or command line args.
    """
    if len(sys.argv) < 3:
        logger.error("Usage: python train_and_importance.py <window_id> <window_path>")
        sys.exit(1)
    
    window_id = sys.argv[1]
    window_path = Path(sys.argv[2])
    output_dir = config.get('output_dir', Path('data/processed'))
    
    result = train_and_compute_importance(window_id, window_path, output_dir)
    
    if result is None:
        logger.warning(f"Window {window_id} was skipped due to model validation failure.")
        sys.exit(0)  # Exit successfully but indicate skip
    else:
        logger.info(f"Successfully processed window {window_id}")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()