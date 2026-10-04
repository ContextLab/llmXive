from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from compositional import ilr
from joblib import load, dump
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import mean_absolute_error

from config import get_config
from logging_config import get_logger, log_operation

# --- Constants & Config ---
CONFIG = get_config()
logger = get_logger("modeling")

# --- Data Loading Helpers ---
def load_parquet_safe(path: str) -> pd.DataFrame:
    """Load a parquet file, handling missing files."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")
    return pd.read_parquet(p)

def load_json_safe(path: str) -> Any:
    """Load a JSON file, handling missing files."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required JSON file not found: {path}")
    with open(p, "r") as f:
        return json.load(f)

def load_features_and_target(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Extract features and target from a dataframe."""
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y

def apply_ilr_transformation(df: pd.DataFrame, elements: List[str]) -> pd.DataFrame:
    """Apply ILR transformation to compositional columns."""
    df = df.copy()
    # Ensure columns exist
    missing = [e for e in elements if e not in df.columns]
    if missing:
        raise ValueError(f"Missing composition columns: {missing}")

    # Extract composition matrix
    comp_cols = df[elements]
    # compositional.ilr expects a matrix where rows are observations
    ilr_coords = ilr(comp_cols.values)
    
    # Create new dataframe with ILR coordinates
    ilr_df = pd.DataFrame(
        ilr_coords,
        columns=[f"ilr_{i}" for i in range(ilr_coords.shape[1])],
        index=df.index
    )
    
    # Concatenate with original dataframe (dropping old composition cols)
    # We keep target and other metadata, but drop the raw composition cols used for ILR
    result = pd.concat([df.drop(columns=elements), ilr_df], axis=1)
    return result

def split_dataset(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, List[int], List[int]]:
    """Split dataset into train and test sets, returning indices."""
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=random_state, stratify=None
    )
    
    # Get original indices
    train_indices = train_df.index.tolist()
    test_indices = test_df.index.tolist()
    
    # Save indices to JSON for reproducibility
    indices_path = Path(CONFIG.data_processed) / "split_indices.json"
    indices_path.parent.mkdir(parents=True, exist_ok=True)
    with open(indices_path, "w") as f:
        json.dump({"train_indices": train_indices, "test_indices": test_indices}, f)
    
    return train_df, test_df, train_indices, test_indices

def load_split_indices() -> Tuple[List[int], List[int]]:
    """Load split indices from the saved JSON file."""
    data = load_json_safe(str(Path(CONFIG.data_processed) / "split_indices.json"))
    return data["train_indices"], data["test_indices"]

def train_random_forest_with_cv(
    X: np.ndarray,
    y: np.ndarray,
    cv_folds: int = 5
) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """Train RF with GridSearchCV and compute cross-validation metrics."""
    param_grid = {
        'n_estimators': [100],
        'max_depth': [None]
    }
    
    rf = RandomForestRegressor(random_state=42)
    grid_search = GridSearchCV(
        rf, param_grid, cv=cv_folds, scoring='neg_mean_absolute_error', n_jobs=-1
    )
    grid_search.fit(X, y)
    
    # Calculate MAE for each fold
    cv_results = grid_search.cv_results_
    mae_scores = -cv_results['mean_test_score']
    
    # Compute confidence interval (95%)
    cv_mae = np.mean(mae_scores)
    cv_std = np.std(mae_scores)
    cv_ci_lower = cv_mae - 1.96 * cv_std
    cv_ci_upper = cv_mae + 1.96 * cv_std
    
    best_params = grid_search.best_params_
    
    metrics = {
        "cv_mae": float(cv_mae),
        "cv_ci_lower": float(cv_ci_lower),
        "cv_ci_upper": float(cv_ci_upper),
        "best_params": best_params
    }
    
    # Save CV metrics
    metrics_path = Path(CONFIG.results) / "cv_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    return grid_search.best_estimator_, metrics

def load_best_hyperparameters() -> Dict[str, Any]:
    """Load best hyperparameters from saved CV metrics."""
    metrics = load_json_safe(str(Path(CONFIG.results) / "cv_metrics.json"))
    return metrics["best_params"]

def save_best_hyperparameters(params: Dict[str, Any]) -> None:
    """Save best hyperparameters to a JSON file."""
    path = Path(CONFIG.results) / "cv_best_hyperparameters.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(params, f, indent=2)

def extract_best_hyperparameters() -> None:
    """Extract and save best hyperparameters from CV metrics."""
    metrics = load_json_safe(str(Path(CONFIG.results) / "cv_metrics.json"))
    save_best_hyperparameters(metrics["best_params"])

def train_and_serialize_model(
    train_df: pd.DataFrame,
    target_col: str,
    ilr_elements: List[str],
    hyperparams: Dict[str, Any]
) -> None:
    """Train final model on full training set and serialize."""
    X, y = load_features_and_target(train_df, [f"ilr_{i}" for i in range(len(ilr_elements))], target_col)
    
    model = RandomForestRegressor(**hyperparams, random_state=42)
    model.fit(X, y)
    
    # Save model
    model_path = Path(CONFIG.models) / "rf_model.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    dump(model, str(model_path), compress=3, protocol=3)
    logger.info(f"Model saved to {model_path}")

def load_model() -> RandomForestRegressor:
    """Load the trained model."""
    model_path = Path(CONFIG.models) / "rf_model.pkl"
    return load(str(model_path))

def save_model_metrics(metrics: Dict[str, Any]) -> None:
    """Save model metrics to JSON."""
    path = Path(CONFIG.results) / "model_metrics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)

def save_residuals(residuals: Dict[str, Any]) -> None:
    """Save residuals to JSON."""
    path = Path(CONFIG.results) / "residuals.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(residuals, f, indent=2)

def save_methodological_flags(flags: Dict[str, Any]) -> None:
    """Save methodological flags to JSON."""
    path = Path(CONFIG.results) / "methodological_flags.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(flags, f, indent=2)

def aggregate_model_metrics(
    cv_mae: float,
    cv_ci_lower: float,
    cv_ci_upper: float,
    test_mae: float
) -> Dict[str, Any]:
    """Aggregate CV and Test metrics into a single dictionary."""
    return {
        "cv_mae": float(cv_mae),
        "cv_ci_lower": float(cv_ci_lower),
        "cv_ci_upper": float(cv_ci_upper),
        "test_mae": float(test_mae)
    }

def evaluate_model_on_test(
    model: RandomForestRegressor,
    test_df: pd.DataFrame,
    target_col: str,
    ilr_elements: List[str]
) -> Tuple[float, Dict[str, Any]]:
    """Evaluate model on test set and compute metrics."""
    X_test, y_test = load_features_and_target(test_df, [f"ilr_{i}" for i in range(len(ilr_elements))], target_col)
    y_pred = model.predict(X_test)
    
    test_mae = mean_absolute_error(y_test, y_pred)
    
    # Compute residuals
    residuals = {
        "observed": y_test.tolist(),
        "predicted": y_pred.tolist(),
        "residuals": (y_test - y_pred).tolist()
    }
    
    return test_mae, residuals

def run_modeling_pipeline() -> None:
    """Run the full modeling pipeline."""
    # Load data
    clean_data_path = Path(CONFIG.data_processed) / "alloys_clean.parquet"
    df = load_parquet_safe(str(clean_data_path))
    
    # Split data
    _, test_df, train_indices, test_indices = split_dataset(df)
    
    # Apply ILR transformation (using fixed order for reproducibility)
    ilr_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    # We need to apply ILR to the full dataset first to get indices, 
    # but we only use training indices for training
    df_ilr = apply_ilr_transformation(df, ilr_elements)
    
    # Filter to training set
    train_df_ilr = df_ilr.loc[train_indices]
    test_df_ilr = df_ilr.loc[test_indices]
    
    target_col = 'poisson_ratio'
    
    # Load best hyperparameters
    hyperparams = load_best_hyperparameters()
    
    # Train final model
    train_and_serialize_model(train_df_ilr, target_col, ilr_elements, hyperparams)
    
    # Load model
    model = load_model()
    
    # Evaluate on test set
    test_mae, residuals = evaluate_model_on_test(model, test_df_ilr, target_col, ilr_elements)
    save_residuals(residuals)
    
    # Load CV metrics
    cv_metrics = load_json_safe(str(Path(CONFIG.results) / "cv_metrics.json"))
    
    # Aggregate metrics
    aggregated_metrics = aggregate_model_metrics(
        cv_metrics["cv_mae"],
        cv_metrics["cv_ci_lower"],
        cv_metrics["cv_ci_upper"],
        test_mae
    )
    save_model_metrics(aggregated_metrics)
    
    # Check for methodological flags
    cv_mae = cv_metrics["cv_mae"]
    mae_flag = cv_mae > 0.05
    narrative = ""
    if mae_flag:
        narrative = "Methodological Concern: Cross-validation MAE exceeds 0.05 threshold, indicating potential model instability or insufficient signal."
    
    flags = {
        "mae_flag": mae_flag,
        "cv_mae": cv_mae,
        "narrative_limitation": narrative
    }
    save_methodological_flags(flags)
    
    logger.info(f"Modeling pipeline completed. Test MAE: {test_mae:.4f}")

def main() -> None:
    """Main entry point for modeling pipeline."""
    log_operation("modeling_pipeline_start")
    run_modeling_pipeline()
    log_operation("modeling_pipeline_end")

if __name__ == "__main__":
    main()
