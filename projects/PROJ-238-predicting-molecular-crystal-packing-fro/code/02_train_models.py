import os
import sys
import logging
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from config import get_config, log_event
from utils.metrics import paired_t_test, bonferroni_correct

# Ensure code directory is in path for relative imports if run directly
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_split_data(data_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load train, val, and test datasets."""
    train_path = Path(data_path) / "train.csv"
    val_path = Path(data_path) / "val.csv"
    test_path = Path(data_path) / "test.csv"

    if not all(p.exists() for p in [train_path, val_path, test_path]):
        raise FileNotFoundError(f"Split data files not found in {data_path}")

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    return train_df, val_df, test_df

def validate_columns(df: pd.DataFrame, required_cols: List[str]) -> bool:
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True

def validate_ids_unique_and_non_overlapping(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
    train_ids = set(train_df['id'])
    val_ids = set(val_df['id'])
    test_ids = set(test_df['id'])

    if len(train_ids) != len(train_df):
        raise ValueError("Duplicate IDs in train set")
    if len(val_ids) != len(val_df):
        raise ValueError("Duplicate IDs in val set")
    if len(test_ids) != len(test_df):
        raise ValueError("Duplicate IDs in test set")

    if train_ids & val_ids:
        raise ValueError("Overlapping IDs between train and val")
    if train_ids & test_ids:
        raise ValueError("Overlapping IDs between train and test")
    if val_ids & test_ids:
        raise ValueError("Overlapping IDs between val and test")

    return True

def validate_target_distribution(df: pd.DataFrame, target_col: str) -> bool:
    if df[target_col].isnull().any():
        raise ValueError(f"Target column {target_col} contains null values")
    return True

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, random_state: int = 42) -> RandomForestRegressor:
    model = RandomForestRegressor(random_state=random_state, n_jobs=-1)
    model.fit(X_train, y_train)
    return model

def train_gradient_boosting(X_train: np.ndarray, y_train: np.ndarray, random_state: int = 42) -> GradientBoostingRegressor:
    model = GradientBoostingRegressor(random_state=random_state)
    model.fit(X_train, y_train)
    return model

def train_mean_baseline(y_train: np.ndarray) -> float:
    return float(np.mean(y_train))

def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    return {"r2": r2, "mae": mae, "rmse": rmse}

def evaluate_baseline(mean_val: float, y_test: np.ndarray) -> Dict[str, float]:
    y_pred = np.full_like(y_test, mean_val, dtype=float)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    return {"r2": r2, "mae": mae, "rmse": rmse}

def main():
    logger = setup_logger("train_models")
    config = get_config()
    
    data_path = Path(config.get("DATA_PATH", "data/processed"))
    results_path = Path("results")
    results_path.mkdir(exist_ok=True)

    logger.info(f"Loading data from {data_path}")
    train_df, val_df, test_df = load_split_data(str(data_path))

    feature_cols = ["Volume", "SurfaceArea", "Dipole", "HBD", "HBA", "PSA"]
    target_col = "packing_coefficient"

    # Validation
    for name, df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        validate_columns(df, feature_cols + [target_col])
        validate_target_distribution(df, target_col)
    validate_ids_unique_and_non_overlapping(train_df, val_df, test_df)

    logger.info("Split data validated.")

    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values

    # Train Models
    logger.info("Training Random Forest...")
    rf_model = train_random_forest(X_train, y_train)
    
    logger.info("Training Gradient Boosting...")
    gb_model = train_gradient_boosting(X_train, y_train)
    
    logger.info("Training Mean Baseline...")
    mean_baseline_val = train_mean_baseline(y_train)

    # Evaluate Models (Task T027)
    logger.info("Evaluating models on test set...")
    rf_metrics = evaluate_model(rf_model, X_test, y_test)
    gb_metrics = evaluate_model(gb_model, X_test, y_test)
    baseline_metrics = evaluate_baseline(mean_baseline_val, y_test)

    logger.info(f"RF Metrics: {rf_metrics}")
    logger.info(f"GB Metrics: {gb_metrics}")
    logger.info(f"Baseline Metrics: {baseline_metrics}")

    # T028 & T029: Statistical tests and saving metrics
    # Bonferroni correction for 2 models (RF, GB)
    alpha = 0.05
    n_models = 2
    alpha_corrected = alpha / n_models

    # Paired t-tests: predictions vs baseline predictions
    rf_pred = rf_model.predict(X_test)
    gb_pred = gb_model.predict(X_test)
    baseline_pred = np.full_like(y_test, mean_baseline_val, dtype=float)

    t_stat_rf, p_val_rf = paired_t_test(rf_pred, baseline_pred)
    t_stat_gb, p_val_gb = paired_t_test(gb_pred, baseline_pred)

    # Bonferroni correction applied to p-values
    p_val_rf_corrected = min(p_val_rf * n_models, 1.0)
    p_val_gb_corrected = min(p_val_gb * n_models, 1.0)

    sig_rf = p_val_rf_corrected < alpha_corrected
    sig_gb = p_val_gb_corrected < alpha_corrected

    metrics_summary = {
        "models": {
            "random_forest": {
                "metrics": rf_metrics,
                "p_value_raw": p_val_rf,
                "p_value_corrected": p_val_rf_corrected,
                "significant_vs_baseline": sig_rf
            },
            "gradient_boosting": {
                "metrics": gb_metrics,
                "p_value_raw": p_val_gb,
                "p_value_corrected": p_val_gb_corrected,
                "significant_vs_baseline": sig_gb
            },
            "mean_baseline": {
                "metrics": baseline_metrics
            }
        },
        "statistical_test": {
            "method": "paired_t_test",
            "alpha": alpha,
            "n_models": n_models,
            "alpha_corrected": alpha_corrected,
            "bonferroni_correction": True
        }
    }

    output_file = results_path / "metrics.json"
    with open(output_file, 'w') as f:
        json.dump(metrics_summary, f, indent=2)

    logger.info(f"Metrics saved to {output_file}")
    log_event("T027_complete", {"file": str(output_file)})

if __name__ == "__main__":
    main()