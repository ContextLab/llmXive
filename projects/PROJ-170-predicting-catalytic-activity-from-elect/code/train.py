import os
import sys
import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib

from config import get_project_root, get_data_path, get_output_path
from logging_config import setup_logging, get_logger

# Initialize logging
logger = get_logger(__name__)

def load_aligned_dataset() -> pd.DataFrame:
    """Load the preprocessed aligned dataset."""
    data_path = get_data_path()
    file_path = data_path / "processed" / "aligned_dataset.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Aligned dataset not found at {file_path}. Run preprocessing first.")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded aligned dataset with {len(df)} rows and {len(df.columns)} columns.")
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Identify feature columns (exclude target and identifiers)."""
    exclude_cols = {'energy_change', 'composition', 'surface_facet', 'sample_id'}
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    logger.info(f"Using {len(feature_cols)} feature columns.")
    return feature_cols

def stratified_split(df: pd.DataFrame, feature_cols: List[str], test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, StandardScaler]:
    """Split data into train/test sets and scale features."""
    # Stratify based on binned target if continuous, or a categorical column if available.
    # Since 'energy_change' is continuous, we bin it for stratification.
    target = 'energy_change'
    if target not in df.columns:
        raise ValueError("Target column 'energy_change' not found.")

    # Create bins for stratification
    df['target_bin'] = pd.qcut(df[target], q=10, duplicates='drop')

    X = df[feature_cols]
    y = df[target]
    y_bin = df['target_bin']

    X_train, X_test, y_train, y_test, y_bin_train, y_bin_test = train_test_split(
        X, y, y_bin, test_size=test_size, random_state=random_state, stratify=y_bin
    )

    # Drop the temporary bin column
    X_train = X_train.drop(columns=['target_bin'], errors='ignore')
    X_test = X_test.drop(columns=['target_bin'], errors='ignore')

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info(f"Train set size: {len(X_train)}, Test set size: {len(X_test)}")
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler

def train_linear_baseline(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[LinearRegression, Dict[str, float]]:
    """Train a simple linear regression baseline."""
    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    metrics = {
        "model_type": "LinearRegression",
        "r2": r2,
        "mae": mae
    }
    logger.info(f"Linear Baseline - R²: {r2:.4f}, MAE: {mae:.4f}")
    return model, metrics

def train_xgboost_nested_cv(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[xgb.XGBRegressor, Dict[str, float]]:
    """
    Train XGBoost with nested cross-validation.
    Inner loop: Grid search for hyperparameters.
    Outer loop: Evaluation of the best model on the test set.
    """
    # Define parameter grid
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'n_estimators': [50, 100, 200]  # Using specific values <= 200 as requested
    }

    # Base XGBoost model
    base_model = xgb.XGBRegressor(
        objective='reg:squarederror',
        random_state=42,
        verbosity=0
    )

    # Inner loop: Grid Search CV
    # Using KFold for inner CV since we are doing hyperparameter tuning on the training set
    inner_cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    logger.info("Starting inner grid search for XGBoost hyperparameters...")
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=inner_cv,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )

    grid_search.fit(X_train, y_train)

    best_params = grid_search.best_params_
    best_score = grid_search.best_score_
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best inner CV R² score: {best_score:.4f}")

    # Train the final model with best parameters on the full training set
    best_model = xgb.XGBRegressor(
        **best_params,
        objective='reg:squarederror',
        random_state=42,
        verbosity=0
    )
    best_model.fit(X_train, y_train)

    # Outer loop: Evaluation on the hold-out test set
    y_pred = best_model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    metrics = {
        "model_type": "XGBoost",
        "best_params": best_params,
        "inner_cv_best_r2": best_score,
        "test_r2": r2,
        "test_mae": mae
    }
    logger.info(f"XGBoost Final - Test R²: {r2:.4f}, Test MAE: {mae:.4f}")
    
    return best_model, metrics

def save_split_metadata(X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray, scaler: StandardScaler) -> None:
    """Save metadata about the train/test split and scaler."""
    output_path = get_output_path()
    meta_dir = output_path / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "train_size": len(X_train),
        "test_size": len(X_test),
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist()
    }

    with open(meta_dir / "split_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved split metadata to {meta_dir / 'split_metadata.json'}")

def save_model(model: Any, model_name: str) -> None:
    """Save the trained model to the code/models directory."""
    project_root = get_project_root()
    models_dir = project_root / "code" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = models_dir / model_name
    # XGBoost models can be saved as JSON or binary. Using JSON for readability as per FR-004.
    if isinstance(model, xgb.XGBRegressor):
        model.save_model(str(file_path))
    else:
        joblib.dump(model, file_path)
    
    logger.info(f"Saved {model_name} to {file_path}")

def main():
    """Main entry point for training pipeline."""
    setup_logging()
    logger.info("Starting Model Training (Task T025/T026)")

    try:
        # 1. Load Data
        df = load_aligned_dataset()
        feature_cols = get_feature_columns(df)
        
        # 2. Split and Scale
        X_train, X_test, y_train, y_test, scaler = stratified_split(df, feature_cols)
        
        # 3. Save Metadata
        save_split_metadata(X_train, X_test, y_train, y_test, scaler)

        # 4. Train Linear Baseline (T025)
        # Note: T025 is implemented here as part of the flow, but the specific task T026 focuses on XGBoost.
        # We run both to ensure the pipeline is complete for T027 (evaluation).
        linear_model, linear_metrics = train_linear_baseline(X_train, y_train, X_test, y_test)
        
        # 5. Train XGBoost with Nested CV (T026)
        xgb_model, xgb_metrics = train_xgboost_nested_cv(X_train, y_train, X_test, y_test)

        # 6. Save Models
        save_model(linear_model, "best_linear_baseline.joblib")
        save_model(xgb_model, "best_xgboost.json") # FR-004 requirement

        # 7. Save Metrics Summary (for downstream tasks)
        output_path = get_output_path()
        metrics_summary = {
            "linear": linear_metrics,
            "xgboost": xgb_metrics
        }
        with open(output_path / "train_metrics.json", 'w') as f:
            json.dump(metrics_summary, f, indent=2)
        
        logger.info("Training completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())