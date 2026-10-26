"""
User Story 2: Train Baseline Models (Random Forest and SVR).

Implements 5‑fold CV or LOOCV based on sample size strategy.
Includes explicit logging of sample sizes and CV strategy selection 
to logs/pipeline.log before training begins (Task T043).
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import cross_val_predict, LeaveOneOut, KFold
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
import joblib

# Project utilities
from utils.config import get_project_root, get_data_path, get_results_path, get_log_path
from utils.logging_config import setup_logging, get_logger
from utils.constants import SEED
from modeling.checkpoint import save_model_checkpoint, load_model_checkpoint

# Constants
STRATEGY_FILE = "results/cv_strategy.json"
HYPERPARAM_FILE = "results/hyperparameters.json"
OUTPUT_METRICS_FILE = "results/within_stress_metrics.json"
LOG_FILE_NAME = "pipeline.log"

def load_strategy_config() -> Dict[str, Any]:
    """Load the CV strategy configuration."""
    project_root = get_project_root()
    strategy_path = project_root / STRATEGY_FILE
    if not strategy_path.exists():
        raise FileNotFoundError(f"Strategy config not found at {strategy_path}. Run T019a first.")
    
    with open(strategy_path, 'r') as f:
        return json.load(f)

def load_hyperparameters() -> Dict[str, Any]:
    """Load hyperparameters based on the selected strategy."""
    project_root = get_project_root()
    hyper_path = project_root / HYPERPARAM_FILE
    if not hyper_path.exists():
        raise FileNotFoundError(f"Hyperparameters config not found at {hyper_path}. Run T019b first.")
    
    with open(hyper_path, 'r') as f:
        return json.load(f)

def load_processed_data() -> pd.DataFrame:
    """Load the preprocessed merged matrix."""
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "merged_matrix.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run T014 first.")
    
    df = pd.read_csv(data_path)
    
    # Identify target column (assumed to be 'expression_level' or similar based on context)
    # If not present, use the last numeric column as fallback.
    if 'expression_level' not in df.columns:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            raise ValueError("No numeric columns found to infer a target.")
        target_col = numeric_cols[-1]
    else:
        target_col = 'expression_level'
    
    return df, target_col

def log_sample_sizes_and_strategy(df: pd.DataFrame, target_col: str, logger: logging.Logger) -> Dict[str, int]:
    """
    Task T043: Log sample sizes per stress condition and the CV strategy.
    Reads strategy from config, counts samples, and logs to pipeline.log.
    """
    project_root = get_project_root()
    log_path = project_root / "logs" / LOG_FILE_NAME
    
    logger.info(f"--- T043 Sample Size & Strategy Check ---")
    logger.info(f"Log file: {log_path}")
    
    # Load strategy to determine what we are doing
    strategy_config = load_strategy_config()
    strategy_type = strategy_config.get("strategy", "unknown")
    
    # Count samples per stress condition
    if 'stress_condition' not in df.columns:
        logger.warning("Column 'stress_condition' not found. Cannot log per‑stress sample sizes.")
        sample_counts = {"total": len(df)}
    else:
        counts = df['stress_condition'].value_counts().to_dict()
        sample_counts = counts
        logger.info("Sample counts per stress condition:")
        for stress, count in sorted(counts.items()):
            logger.info(f"  - {stress}: n={count}")
    
    total_samples = len(df)
    logger.info(f"Total samples available: {total_samples}")
    logger.info(f"Selected CV Strategy: {strategy_type}")
    
    if strategy_type == "LOOCV":
        logger.info(f"LOOCV selected: Will perform {total_samples} folds.")
    elif strategy_type == "5-fold":
        logger.info(f"5‑fold CV selected: Will perform 5 folds.")
    else:
        logger.warning(f"Unknown strategy: {strategy_type}. Defaulting to 5‑fold.")
    
    logger.info(f"--- End T043 Check ---")
    
    return sample_counts

def train_model(
    X: pd.DataFrame, 
    y: pd.Series, 
    model_type: str, 
    strategy_type: str, 
    hyperparams: Dict[str, Any],
    logger: logging.Logger
) -> Tuple[Any, Dict[str, Any], StandardScaler]:
    """
    Train a model using the specified CV strategy.
    Returns the fitted model, metrics, and the scaler.
    """
    logger.info(f"Training {model_type} with {strategy_type} strategy.")
    
    # Initialise model with the project‑wide seed where applicable
    if model_type == "RandomForest":
        model = RandomForestRegressor(
            n_estimators=hyperparams.get("n_estimators", 100),
            max_depth=hyperparams.get("max_depth", 10),
            random_state=SEED,
            n_jobs=-1
        )
    elif model_type == "SVR":
        kernel = hyperparams.get("kernel", "rbf")
        C = hyperparams.get("C", 1.0)
        epsilon = hyperparams.get("epsilon", 0.1)
        model = SVR(kernel=kernel, C=C, epsilon=epsilon)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Scale features (important for SVR)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Choose CV splitter
    if strategy_type == "LOOCV":
        cv = LeaveOneOut()
    else:
        cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
    
    # Cross‑validated predictions
    try:
        y_pred = cross_val_predict(model, X_scaled, y, cv=cv)
    except Exception as e:
        logger.error(f"CV prediction failed: {e}")
        raise
    
    # Metrics
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    
    logger.info(f"{model_type} Results → R²: {r2:.4f}, RMSE: {rmse:.4f}")
    
    # Fit on full data for later use / checkpointing
    model.fit(X_scaled, y)
    
    metrics = {
        "model_type": model_type,
        "strategy": strategy_type,
        "r2": float(r2),
        "rmse": float(rmse),
        "n_samples": int(len(y))
    }
    
    return model, metrics, scaler

def run_training_pipeline() -> Dict[str, Any]:
    """Orchestrate the training of RF and SVR models."""
    # Setup logging
    project_root = get_project_root()
    log_path = project_root / "logs" / LOG_FILE_NAME
    logger = setup_logging(log_file=log_path, log_level=logging.INFO)
    
    logger.info("Starting Training Pipeline (T019c + T043)")
    
    # Load data
    df, target_col = load_processed_data()
    logger.info(f"Loaded data with shape {df.shape}, target column: {target_col}")
    
    # Log sample sizes & strategy
    sample_counts = log_sample_sizes_and_strategy(df, target_col, logger)
    
    # Load configuration
    strategy_config = load_strategy_config()
    strategy_type = strategy_config.get("strategy", "5-fold")
    hyperparams = load_hyperparameters()
    
    # Prepare features / target
    feature_cols = [c for c in df.columns if c not in [target_col, 'stress_condition']]
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Drop rows with missing values (should be rare after preprocessing)
    if X.isnull().any().any() or y.isnull().any():
        logger.warning("Missing values detected. Dropping affected rows.")
        valid_idx = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[valid_idx]
        y = y[valid_idx]
    
    results: Dict[str, Any] = {
        "strategy": strategy_type,
        "total_samples": int(len(y)),
        "samples_per_stress": sample_counts,
        "models": {}
    }
    
    # Train Random Forest
    try:
        rf_model, rf_metrics, rf_scaler = train_model(
            X, y, "RandomForest", strategy_type, hyperparams, logger
        )
        results["models"]["RandomForest"] = rf_metrics
        save_model_checkpoint(rf_model, rf_scaler, rf_metrics, "RandomForest", strategy_type)
    except Exception as e:
        logger.error(f"Failed to train RandomForest: {e}")
        results["models"]["RandomForest"] = {"error": str(e)}
    
    # Train SVR
    try:
        svr_model, svr_metrics, svr_scaler = train_model(
            X, y, "SVR", strategy_type, hyperparams, logger
        )
        results["models"]["SVR"] = svr_metrics
        save_model_checkpoint(svr_model, svr_scaler, svr_metrics, "SVR", strategy_type)
    except Exception as e:
        logger.error(f"Failed to train SVR: {e}")
        results["models"]["SVR"] = {"error": str(e)}
    
    # Write metrics JSON
    output_path = project_root / OUTPUT_METRICS_FILE
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Training complete. Metrics saved to {output_path}")
    return results

def main():
    """Entry point for the training script."""
    parser = argparse.ArgumentParser(description="Train Baseline Models")
    parser.add_argument("--strategy", type=str, default=None,
                        help="Override strategy (5-fold or LOOCV)")
    args = parser.parse_args()
    
    try:
        run_training_pipeline()
        print("Training pipeline executed successfully.")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Data/Config Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Pipeline Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
