"""
Random Forest Regressor implementation for molecular permeability prediction.

This module provides the Random Forest baseline model as specified in User Story 2.
It includes training, prediction, evaluation, and a main entry point for standalone execution.
"""
import logging
from typing import Tuple, Optional, List, Union, Dict, Any
import numpy as np
import pandas as pd
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings

# Suppress specific sklearn warnings for cleaner logs
warnings.filterwarnings("ignore", category=UserWarning)

# Configure logging
logger = logging.getLogger(__name__)

def train_random_forest(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    random_state: int = 42,
    cv_folds: int = 5
) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    Train a Random Forest Regressor on the provided data.
    
    Args:
        X: Feature matrix (numpy array or pandas DataFrame).
        y: Target vector (numpy array or pandas Series).
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of the tree. If None, nodes expand until all leaves are pure.
        random_state: Seed for reproducibility.
        cv_folds: Number of folds for cross-validation score calculation.
    
    Returns:
        A tuple containing:
            - The trained RandomForestRegressor model.
            - A dictionary with 'cv_mean_score' and 'cv_std_score'.
    
    Raises:
        ValueError: If input data is empty or shapes mismatch.
    """
    logger.info(f"Training Random Forest with {n_estimators} estimators...")
    
    # Convert inputs to numpy if necessary
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, pd.Series):
        y = y.values
    
    if X.shape[0] != y.shape[0]:
        raise ValueError(f"X and y shapes mismatch: {X.shape[0]} vs {y.shape[0]}")
    
    if X.shape[0] == 0:
        raise ValueError("Input data X is empty.")

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        verbose=0
    )
    
    # Fit the model
    model.fit(X, y)
    
    # Perform cross-validation to estimate generalization performance
    # Note: Using negative MSE as score, so we need to negate back or use a different metric
    # sklearn's cross_val_score for regressors uses R2 by default if scoring is not specified? 
    # Actually, default is R2. Let's be explicit.
    try:
        cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring='r2', n_jobs=-1)
        cv_mean = float(np.mean(cv_scores))
        cv_std = float(np.std(cv_scores))
        logger.info(f"Cross-validation R2 score: {cv_mean:.4f} (+/- {cv_std:.4f})")
    except Exception as e:
        logger.warning(f"Cross-validation failed: {e}. Skipping CV metrics.")
        cv_mean = 0.0
        cv_std = 0.0

    return model, {"cv_mean_score": cv_mean, "cv_std_score": cv_std}

def predict(
    model: RandomForestRegressor,
    X: Union[np.ndarray, pd.DataFrame]
) -> np.ndarray:
    """
    Generate predictions using the trained Random Forest model.
    
    Args:
        model: Trained RandomForestRegressor instance.
        X: Feature matrix.
    
    Returns:
        Numpy array of predictions.
    """
    if isinstance(X, pd.DataFrame):
        X = X.values
    
    predictions = model.predict(X)
    logger.debug(f"Generated {len(predictions)} predictions.")
    return predictions

def evaluate_model(
    model: RandomForestRegressor,
    X_test: Union[np.ndarray, pd.DataFrame],
    y_test: Union[np.ndarray, pd.Series]
) -> Dict[str, float]:
    """
    Evaluate the Random Forest model on test data.
    
    Args:
        model: Trained RandomForestRegressor instance.
        X_test: Test feature matrix.
        y_test: Test target vector.
    
    Returns:
        Dictionary containing RMSE, MAE, and R2 metrics.
    """
    if isinstance(X_test, pd.DataFrame):
        X_test = X_test.values
    if isinstance(y_test, pd.Series):
        y_test = y_test.values
    
    y_pred = predict(model, X_test)
    
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))
    
    metrics = {
        "rmse": rmse,
        "mae": mae,
        "r2": r2
    }
    
    logger.info(f"Evaluation Metrics -> RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")
    return metrics

def main():
    """
    Main entry point for training and evaluating the Random Forest model.
    
    This function:
    1. Loads preprocessed data from data/processed/train.csv and data/processed/test.csv.
    2. Identifies the target column (assumed 'permeability_coefficient' or similar).
    3. Trains the Random Forest model.
    4. Evaluates the model on the test set.
    5. Saves the model artifact to models/ and metrics to results/.
    """
    import yaml
    
    # Setup logging
    log_dir = Path("projects/PROJ-422-predicting-molecular-permeability-coeffi/results/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_dir / "rf_training.log")
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Load config
    config_path = Path("projects/PROJ-422-predicting-molecular-permeability-coeffi/config.yaml")
    config = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    
    # Paths relative to project root
    project_root = Path("projects/PROJ-422-predicting-molecular-permeability-coeffi")
    train_path = project_root / "data" / "processed" / "train.csv"
    test_path = project_root / "data" / "processed" / "test.csv"
    model_save_path = project_root / "models" / "rf_model.joblib"
    metrics_save_path = project_root / "results" / "metrics_rf.json"
    
    # Ensure directories exist
    model_save_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_save_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not train_path.exists():
        logger.error(f"Training data not found at {train_path}. Please run T014-T017 first.")
        return
    
    if not test_path.exists():
        logger.error(f"Test data not found at {test_path}. Please run T014-T017 first.")
        return
    
    logger.info(f"Loading training data from {train_path}")
    df_train = pd.read_csv(train_path)
    logger.info(f"Loaded {len(df_train)} training samples.")
    
    logger.info(f"Loading test data from {test_path}")
    df_test = pd.read_csv(test_path)
    logger.info(f"Loaded {len(df_test)} test samples.")
    
    # Identify target column
    # Common targets in this project context based on T013b
    possible_targets = ['permeability_coefficient', 'logP', 'target']
    target_col = None
    for t in possible_targets:
        if t in df_train.columns:
            target_col = t
            break
    
    if not target_col:
        logger.error("Could not identify target column in training data.")
        logger.error(f"Available columns: {df_train.columns.tolist()}")
        return
    
    logger.info(f"Using target column: {target_col}")
    
    # Separate features and target
    # Exclude non-numeric columns if any, but assume preprocessed data is clean
    feature_cols = [c for c in df_train.columns if c != target_col]
    
    X_train = df_train[feature_cols]
    y_train = df_train[target_col]
    X_test = df_test[feature_cols]
    y_test = df_test[target_col]
    
    # Hyperparameters from config or defaults
    n_estimators = config.get('rf', {}).get('n_estimators', 100)
    max_depth = config.get('rf', {}).get('max_depth', None)
    
    # Train
    model, cv_metrics = train_random_forest(
        X_train, y_train,
        n_estimators=n_estimators,
        max_depth=max_depth
    )
    
    # Evaluate
    test_metrics = evaluate_model(model, X_test, y_test)
    
    # Save model
    joblib.dump(model, model_save_path)
    logger.info(f"Model saved to {model_save_path}")
    
    # Save metrics
    import json
    results = {
        "model": "RandomForest",
        "cv_metrics": cv_metrics,
        "test_metrics": test_metrics,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "target_column": target_col
    }
    
    with open(metrics_save_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Metrics saved to {metrics_save_path}")
    
    print(f"Random Forest training complete. RMSE: {test_metrics['rmse']:.4f}")

if __name__ == "__main__":
    main()