"""
Modeling pipeline for predicting Poisson's ratio of aluminum alloys.
Implements Random Forest regression with cross-validation and evaluation.
"""
import logging
import pickle
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler
import joblib

from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger(__name__)
config = get_config()

# Ensure models directory exists
os.makedirs(config.models_dir, exist_ok=True)


def load_features_and_target() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the cleaned and ILR-transformed dataset.
    Returns features (X) and target (y).
    """
    # The task description for T025b depends on the output of T015/T046 which
    # produces data/processed/alloys_clean.parquet.
    # However, the error log from the previous run indicated:
    # "AttributeError: 'Config' object has no attribute 'data_processed'"
    # and the code was looking for "filtered_alloys.csv".
    # Based on T015/T046 specs, the output is `data/processed/alloys_clean.parquet`.
    # We will use the config path if available, otherwise fallback to the standard processed path.
    
    # Check for the specific attribute error fix first by using the standard path
    # defined in T015: data/processed/alloys_clean.parquet
    data_path = config.data_processed_dir / "alloys_clean.parquet"
    
    if not data_path.exists():
        # Fallback for legacy paths if the parquet isn't there yet (though it should be)
        legacy_path = config.data_processed_dir / "filtered_alloys.csv"
        if legacy_path.exists():
            data_path = legacy_path
        else:
            raise FileNotFoundError(f"Cleaned data not found at {data_path} or {legacy_path}")

    log_operation("load_features", path=str(data_path))
    
    if data_path.suffix == '.parquet':
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)

    # Identify ILR columns and target
    # ILR columns are typically named ilr_0, ilr_1... or similar, or we infer from schema
    # The target is 'poisson_ratio'
    
    target_col = 'poisson_ratio'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset. Columns: {df.columns.tolist()}")
    
    y = df[target_col]
    
    # Features are all columns except target and metadata
    # We assume ILR transformation has been applied and stored as 'ilr_*' columns
    # or the dataframe contains the transformed features directly.
    # Based on T019, ILR transformation is applied.
    ilr_cols = [col for col in df.columns if col.startswith('ilr_')]
    
    if not ilr_cols:
        # If no ilr_ columns, assume the numeric columns are the features (excluding target)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        ilr_cols = [c for c in numeric_cols if c != target_col]
        if not ilr_cols:
            raise ValueError("No feature columns found for modeling.")
    
    X = df[ilr_cols]
    logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features.")
    return X, y


def train_random_forest_with_cv(X: pd.DataFrame, y: pd.Series, n_splits: int = 5) -> Tuple[RandomForestRegressor, List[float]]:
    """
    Train a Random Forest model with k-fold cross-validation.
    Returns the trained model and CV scores.
    """
    log_operation("train_random_forest", n_estimators=100, cv_splits=n_splits)
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=2  # Parallelization per T039
    )
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=n_splits, scoring='neg_mean_absolute_error')
    # Convert negative MAE to positive
    cv_mae_scores = -cv_scores
    
    logger.info(f"Cross-validation MAE scores: {cv_mae_scores}")
    logger.info(f"Mean CV MAE: {cv_mae_scores.mean():.4f}, Std: {cv_mae_scores.std():.4f}")
    
    # Train final model on full data
    model.fit(X, y)
    
    return model, cv_mae_scores.tolist()


def evaluate_model_on_test(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """
    Evaluate the model on the test set and return MAE.
    """
    log_operation("evaluate_model")
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    logger.info(f"Test set MAE: {mae:.4f}")
    return mae


def save_model(model: RandomForestRegressor) -> str:
    """
    Serialize the trained model to disk.
    """
    output_path = config.models_dir / "rf_model.pkl"
    log_operation("save_model", path=str(output_path))
    
    # Ensure directory exists
    os.makedirs(str(config.models_dir), exist_ok=True)
    
    joblib.dump(model, str(output_path), compress=3, protocol=3)
    logger.info(f"Model saved to {output_path}")
    return str(output_path)


def save_model_metrics(cv_mae: float, test_mae: float, std_dev: float, mae_flag: bool) -> str:
    """
    Save model metrics to JSON file.
    Implements T025b and T023c logic.
    Schema: {'cv_mae': float, 'test_mae': float, 'std_dev': float, 'mae_flag': boolean, 'threshold': 0.05}
    """
    output_path = config.data_processed_dir / "model_metrics.json"
    log_operation("save_model_metrics", path=str(output_path))
    
    metrics = {
        "cv_mae": float(cv_mae),
        "test_mae": float(test_mae),
        "std_dev": float(std_dev),
        "mae_flag": bool(mae_flag),
        "threshold": 0.05
    }
    
    os.makedirs(str(config.data_processed_dir), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Model metrics saved to {output_path}")
    return str(output_path)


def run_modeling_pipeline():
    """
    Orchestrates the full modeling pipeline:
    1. Load data
    2. Split data
    3. Train model with CV
    4. Evaluate on test set
    5. Save model
    6. Save metrics (T025b, T023c)
    """
    log_operation("run_modeling_pipeline")
    start_time = time.time()
    
    # 1. Load Data
    X, y = load_features_and_target()
    
    # 2. Train/Test Split (T021)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # 3. Train Model with CV (T022)
    model, cv_mae_scores = train_random_forest_with_cv(X_train, y_train)
    
    # Calculate aggregate CV metrics
    cv_mae = float(np.mean(cv_mae_scores))
    std_dev = float(np.std(cv_mae_scores))
    
    # 4. Evaluate on Test Set (T019b)
    test_mae = evaluate_model_on_test(model, X_test, y_test)
    
    # 5. MAE Flagging (T023c)
    # Condition: mae_flag = True if cv_mae > 0.05
    threshold = 0.05
    mae_flag = cv_mae > threshold
    
    if mae_flag:
        logger.warning(f"MethodologicalConcern: CV MAE ({cv_mae:.4f}) exceeds threshold ({threshold})")
    
    # 6. Save Model (T024)
    save_model(model)
    
    # 7. Save Metrics (T025b)
    save_model_metrics(cv_mae, test_mae, std_dev, mae_flag)
    
    elapsed = time.time() - start_time
    logger.info(f"Modeling pipeline completed in {elapsed:.2f} seconds.")
    return model, cv_mae, test_mae


def main():
    """
    Entry point for the modeling script.
    """
    log_operation("main")
    try:
        run_modeling_pipeline()
        logger.info("Modeling pipeline finished successfully.")
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
