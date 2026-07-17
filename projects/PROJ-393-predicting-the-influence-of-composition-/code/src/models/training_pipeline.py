"""
Training Pipeline for Heusler Alloy Hysteresis Prediction.

Orchestrates k-fold cross-validation, GridSearchCV hyperparameter tuning,
and model persistence for Linear Regression and Random Forest models.
"""
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold, GridSearchCV, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
import joblib

from src.models.linear_regressor import run_linear_regression, create_model_pipeline as create_linear_pipeline
from src.models.random_forest_regressor import run_random_forest_regression, create_model_pipeline as create_rf_pipeline
from src.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

# Constants
MODEL_DIR = Path("code/models")
METRICS_FILE = Path("data/processed/model_metrics.json")
RANDOM_STATE = 42
N_FOLDS = 5

def load_features_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the dataset containing features and targets.
    Expects 'data/processed/alloys_features.csv' if no path provided.
    """
    if input_path is None:
        input_path = Path("data/processed/alloys_features.csv")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Features file not found at {input_path}")
    
    logger.info(f"Loading features from {input_path}")
    df = pd.read_csv(input_path)
    return df

def prepare_data(df: pd.DataFrame, target_col: str = "coercivity_oersted") -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare X and y arrays from the dataframe.
    Returns features, target, and list of feature names.
    """
    # Identify feature columns (exclude known non-feature columns)
    exclude_cols = ['composition', 'source_type', 'synthesis_method', 'target_source', 'coercivity_oersted']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Check if target exists
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe. Available: {df.columns.tolist()}")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Handle missing values in X if any (should be handled by preprocessing, but safe-guard)
    if np.isnan(X).any() or np.isnan(y).any():
        logger.warning("NaN values detected in data after feature selection. Dropping rows.")
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
    
    return X, y, feature_cols

def run_cross_validation(model, X: np.ndarray, y: np.ndarray, cv: int = 5) -> Dict[str, float]:
    """
    Perform k-fold cross-validation and return mean scores.
    """
    kfold = KFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
    
    r2_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
    mae_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_absolute_error')
    
    # Negate MAE scores returned by sklearn
    mae_scores = -mae_scores
    
    return {
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
        "mae_mean": float(np.mean(mae_scores)),
        "mae_std": float(np.std(mae_scores))
    }

def tune_and_train_linear(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Tuple[Any, Dict[str, Any]]:
    """
    Run GridSearchCV for Linear Regression (including Ridge/Lasso if desired, 
    but primarily tuning regularization strength if using Ridge/Lasso variants).
    For standard LinearRegression, we just train and evaluate.
    """
    # Standard Linear Regression has no hyperparameters to tune significantly,
    # but we can wrap it in a pipeline.
    # If we want to tune regularization, we'd use Ridge/Lasso. 
    # Based on T033, we assume standard LinearRegression or Ridge.
    # Let's implement a simple GridSearch for Ridge regularization as a proxy for 'tuning'.
    
    from sklearn.linear_model import Ridge
    
    param_grid = {
        'alpha': [0.01, 0.1, 1.0, 10.0, 100.0]
    }
    
    base_model = Ridge()
    grid_search = GridSearchCV(
        base_model, 
        param_grid, 
        cv=N_FOLDS, 
        scoring='r2', 
        n_jobs=-1,
        return_train_score=False
    )
    
    logger.info("Running GridSearchCV for Linear/Ridge model...")
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Cross-validation scores from the best model
    cv_results = run_cross_validation(best_model, X, y, cv=N_FOLDS)
    
    metrics = {
        "model_type": "Ridge_Regression",
        "best_params": best_params,
        "cv_results": cv_results,
        "feature_names": feature_names
    }
    
    return best_model, metrics

def tune_and_train_rf(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Tuple[Any, Dict[str, Any]]:
    """
    Run GridSearchCV for Random Forest Regressor.
    """
    from sklearn.ensemble import RandomForestRegressor
    
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [None, 5, 10, 20],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    
    base_model = RandomForestRegressor(random_state=RANDOM_STATE)
    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=N_FOLDS,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    logger.info("Running GridSearchCV for Random Forest model...")
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Cross-validation scores
    cv_results = run_cross_validation(best_model, X, y, cv=N_FOLDS)
    
    metrics = {
        "model_type": "Random_Forest",
        "best_params": best_params,
        "cv_results": cv_results,
        "feature_names": feature_names
    }
    
    return best_model, metrics

def save_model(model: Any, model_name: str) -> str:
    """
    Save the trained model to disk.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / f"{model_name}.pkl"
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")
    return str(model_path)

def save_metrics(metrics: Dict[str, Any], model_name: str) -> str:
    """
    Save metrics to the central metrics JSON file.
    """
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing metrics if present
    all_metrics = {}
    if METRICS_FILE.exists():
        try:
            with open(METRICS_FILE, 'r') as f:
                all_metrics = json.load(f)
        except json.JSONDecodeError:
            all_metrics = {}
    
    all_metrics[model_name] = metrics
    
    with open(METRICS_FILE, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {METRICS_FILE}")
    return str(METRICS_FILE)

def run_training_pipeline(
    input_path: Optional[Path] = None,
    target_col: str = "coercivity_oersted",
    enable_linear: bool = True,
    enable_rf: bool = True
) -> Dict[str, Any]:
    """
    Main entry point for the training pipeline.
    Orchestrates data loading, model training (CV + GridSearch), and saving.
    """
    setup_logging()
    
    logger.info("Starting Training Pipeline (T035)...")
    
    # 1. Load Data
    df = load_features_data(input_path)
    if df.empty:
        raise ValueError("Input dataframe is empty. Cannot train models.")
    
    # 2. Prepare Data
    X, y, feature_names = prepare_data(df, target_col)
    logger.info(f"Prepared data: {X.shape[0]} samples, {X.shape[1]} features.")
    
    results = {}
    
    # 3. Train Linear Model
    if enable_linear:
        logger.info("Training Linear/Ridge Model...")
        try:
            linear_model, linear_metrics = tune_and_train_linear(X, y, feature_names)
            linear_path = save_model(linear_model, "linear_model")
            save_metrics(linear_metrics, "linear_model")
            results["linear"] = {
                "path": linear_path,
                "metrics": linear_metrics
            }
        except Exception as e:
            logger.error(f"Failed to train linear model: {e}")
            results["linear"] = {"error": str(e)}
    
    # 4. Train Random Forest Model
    if enable_rf:
        logger.info("Training Random Forest Model...")
        try:
            rf_model, rf_metrics = tune_and_train_rf(X, y, feature_names)
            rf_path = save_model(rf_model, "random_forest_model")
            save_metrics(rf_metrics, "random_forest_model")
            results["random_forest"] = {
                "path": rf_path,
                "metrics": rf_metrics
            }
        except Exception as e:
            logger.error(f"Failed to train random forest model: {e}")
            results["random_forest"] = {"error": str(e)}
    
    logger.info("Training Pipeline completed.")
    return results

def main():
    """
    CLI entry point.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run Model Training Pipeline")
    parser.add_argument("--input", type=str, default="data/processed/alloys_features.csv",
                        help="Path to features CSV")
    parser.add_argument("--target", type=str, default="coercivity_oersted",
                        help="Target column name")
    parser.add_argument("--no-linear", action="store_true", help="Disable Linear model training")
    parser.add_argument("--no-rf", action="store_true", help="Disable Random Forest model training")
    
    args = parser.parse_args()
    
    run_training_pipeline(
        input_path=Path(args.input),
        target_col=args.target,
        enable_linear=not args.no_linear,
        enable_rf=not args.no_rf
    )

if __name__ == "__main__":
    main()
