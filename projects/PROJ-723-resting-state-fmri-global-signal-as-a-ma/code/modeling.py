import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from utils import get_logger, read_csv, write_json

logger = get_logger(__name__)

def load_cleaned_data(filepath: str) -> pd.DataFrame:
    """Load the cleaned dataset from CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {filepath}")
    df = pd.read_csv(path)
    return df

def prepare_model_data(
    df: pd.DataFrame,
    y_col: str = "MWQ_Score",
    x_cols: List[str] = None
) -> Tuple[np.ndarray, np.ndarray, Dict[str, int]]:
    """
    Prepare X and y arrays.
    Returns X, y, and a mapping of feature names to indices.
    """
    if x_cols is None:
        # Default full model features
        x_cols = ["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"]
    
    # Ensure columns exist
    missing = [c for c in x_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in data: {missing}")
    
    X = df[x_cols].to_numpy()
    y = df[y_col].to_numpy()
    
    return X, y, {name: i for i, name in enumerate(x_cols)}

def run_ridge_regression_with_nested_cv(
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    alphas: Optional[np.ndarray] = None
) -> Tuple[float, float, float, RidgeCV, Dict[str, float]]:
    """
    Run Ridge Regression with nested 5-fold CV.
    Returns: mean MAE, mean Pearson r, mean R2, best model, metrics dict.
    """
    if alphas is None:
        alphas = np.logspace(-3, 3, 50)
    
    n_samples = X.shape[0]
    outer_cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    mae_scores = []
    r_scores = []
    r2_scores = []
    
    # We need to scale X per fold to avoid leakage
    scaler = StandardScaler()
    
    for train_idx, test_idx in outer_cv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Inner CV is handled by RidgeCV internally
        model = RidgeCV(alphas=alphas, store_cv_values=True)
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        
        # Metrics
        mae = np.mean(np.abs(y_test - y_pred))
        r = np.corrcoef(y_test, y_pred)[0, 1]
        ss_res = np.sum((y_test - y_pred) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        mae_scores.append(mae)
        r_scores.append(r)
        r2_scores.append(r2)
    
    # Fit final model on full data for return
    X_scaled = scaler.fit_transform(X)
    final_model = RidgeCV(alphas=alphas, store_cv_values=True)
    final_model.fit(X_scaled, y)
    
    return (
        np.mean(mae_scores),
        np.mean(r_scores),
        np.mean(r2_scores),
        final_model,
        {
            "mae": np.mean(mae_scores),
            "r": np.mean(r_scores),
            "r2": np.mean(r2_scores),
            "std_mae": np.std(mae_scores),
            "std_r": np.std(r_scores),
            "std_r2": np.std(r2_scores)
        }
    )

def run_reduced_model_analysis(
    df: pd.DataFrame,
    y_col: str = "MWQ_Score",
    reduced_features: List[str] = None,
    full_features: List[str] = None,
    n_splits: int = 5
) -> Dict[str, Any]:
    """
    Run Reduced Model (Y ~ FD + DVARS + Age + Sex) and compare to Full Model.
    Calculates Delta R2 = R2_full - R2_reduced.
    """
    if reduced_features is None:
        reduced_features = ["Mean_FD", "Mean_DVARS", "Age", "Sex"]
    
    if full_features is None:
        full_features = ["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"]
    
    # Validate columns
    for col in full_features + [y_col]:
        if col not in df.columns:
            raise ValueError(f"Required column missing for full model: {col}")
    
    X_full, y, _ = prepare_model_data(df, y_col=y_col, x_cols=full_features)
    X_reduced, _, _ = prepare_model_data(df, y_col=y_col, x_cols=reduced_features)
    
    # Run full model
    mae_full, r_full, r2_full, model_full, metrics_full = run_ridge_regression_with_nested_cv(
        X_full, y, n_splits=n_splits
    )
    
    # Run reduced model
    mae_red, r_red, r2_red, model_red, metrics_red = run_ridge_regression_with_nested_cv(
        X_reduced, y, n_splits=n_splits
    )
    
    delta_r2 = r2_full - r2_red
    
    logger.info(f"Full Model R2: {r2_full:.4f}")
    logger.info(f"Reduced Model R2: {r2_red:.4f}")
    logger.info(f"Delta R2 (Full - Reduced): {delta_r2:.4f}")
    
    return {
        "full_model": {
            "r2": r2_full,
            "mae": mae_full,
            "r": r_full,
            "features": full_features
        },
        "reduced_model": {
            "r2": r2_red,
            "mae": mae_red,
            "r": r_red,
            "features": reduced_features
        },
        "delta_r2": delta_r2,
        "metrics": {
            "full": metrics_full,
            "reduced": metrics_red
        }
    }

def calculate_delta_r2(result_dict: Dict[str, Any]) -> float:
    """Extract Delta R2 from the result dictionary."""
    return result_dict.get("delta_r2", 0.0)

def main():
    """
    Main entry point for T023: Reduced Model Analysis.
    Reads cleaned data, runs reduced vs full model, saves delta_r2.json.
    """
    # Paths
    data_path = "data/processed/cleaned_data.csv"
    output_dir = Path("data/results")
    output_path = output_dir / "delta_r2.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {data_path}")
    try:
        df = load_cleaned_data(data_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    logger.info(f"Loaded {len(df)} subjects")
    
    # Run analysis
    logger.info("Running Reduced Model Analysis (T023)...")
    results = run_reduced_model_analysis(df)
    
    # Save results
    logger.info(f"Saving results to {output_path}")
    write_json(output_path, results)
    
    logger.info("T023 Complete: delta_r2.json generated.")
    return results

if __name__ == "__main__":
    main()
