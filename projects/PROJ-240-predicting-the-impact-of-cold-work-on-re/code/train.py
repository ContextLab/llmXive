import json
import os
import sys
import pickle
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import warnings

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score

# Import config helpers
from config import (
    get_random_seed,
    get_data_split_ratio,
    get_min_rows,
    get_max_rows,
)
from utils import calculate_vif

def load_final_dataset() -> pd.DataFrame:
    """Load the final processed dataset."""
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "processed" / "final_dataset.csv"
    if not path.exists():
        raise FileNotFoundError(f"Final dataset not found at {path}")
    return pd.read_csv(path)

def split_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into train and test sets."""
    seed = get_random_seed()
    ratio = get_data_split_ratio()
    train, test = train_test_split(df, test_size=1 - ratio, random_state=seed)
    return train, test

def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """Train a Random Forest Regressor."""
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=get_random_seed(),
        n_jobs=-1,
        max_depth=None,
    )
    model.fit(X_train, y_train)
    return model

def evaluate_model(
    model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series
) -> Dict[str, float]:
    """Evaluate model on test set."""
    y_pred = model.predict(X_test)
    return {
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "r2": float(r2_score(y_test, y_pred)),
    }

def cross_validate_model(
    model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series
) -> Dict[str, float]:
    """Perform k-fold cross-validation."""
    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    return {
        "mean_r2": float(np.mean(scores)),
        "std_r2": float(np.std(scores)),
    }

def save_model(model: RandomForestRegressor, path: Path) -> None:
    """Save the trained model to disk."""
    with open(path, "wb") as f:
        pickle.dump(model, f)

def save_metrics(metrics: Dict[str, Any], path: Path) -> None:
    """Save metrics to a JSON file."""
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)

def run_training_pipeline() -> Dict[str, Any]:
    """Run the full training pipeline."""
    # Load data
    df = load_final_dataset()

    # Separate features and target
    # Assuming target column is 'time_to_peak_minutes' based on context
    target_col = "time_to_peak_minutes"
    if target_col not in df.columns:
        # Fallback if column name differs, look for time-related target
        candidates = [c for c in df.columns if "time" in c.lower() and "peak" in c.lower()]
        if candidates:
            target_col = candidates[0]
        else:
            raise ValueError(f"Target column '{target_col}' not found in dataset.")

    y = df[target_col]
    X = df.drop(columns=[target_col])

    # Check for pure aluminum (zero variance in composition features)
    # Identify composition columns (likely containing 'Mn', 'Mg', 'Si', 'Cu' or 'content')
    composition_cols = [
        c for c in X.columns
        if any(kw in c.lower() for kw in ["mn", "mg", "si", "cu", "content"])
    ]

    zero_variance_composition = False
    if composition_cols:
        for col in composition_cols:
            if X[col].var() == 0:
                zero_variance_composition = True
                break

    if zero_variance_composition:
        warnings.warn(
            "Dataset appears to be pure aluminum (zero variance in composition features). "
            "Skipping interaction feature importance analysis as per T029. "
            "Training will proceed with main effects only."
        )
        # Log this warning to a file or stdout if needed, but do not crash.
        # The model training continues, but downstream analysis (T035/T036)
        # should handle this flag if it checks for composition variance.

    # Enforce row cap if necessary
    max_rows = get_max_rows()
    if len(X) > max_rows:
        X = X.head(max_rows)
        y = y.head(max_rows)

    # Split data
    X_train, X_test = split_data(X)
    y_train, y_test = split_data(y)

    # Train model
    model = train_model(X_train, y_train)

    # Cross-validate
    cv_results = cross_validate_model(model, X_train, y_train)

    # Evaluate on test set
    test_results = evaluate_model(model, X_test, y_test)

    # Save model
    root = Path(__file__).resolve().parent.parent
    model_path = root / "artifacts" / "models" / "kinetic_model.pkl"
    save_model(model, model_path)

    # Prepare metrics report
    metrics_report = {
        "cv_mean_r2": cv_results["mean_r2"],
        "cv_std_r2": cv_results["std_r2"],
        "test_mae": test_results["mae"],
        "test_r2": test_results["r2"],
        "n_train": len(X_train),
        "n_test": len(X_test),
        "zero_variance_composition": zero_variance_composition,
    }

    # Save metrics
    metrics_path = root / "artifacts" / "reports" / "training_metrics.json"
    save_metrics(metrics_report, metrics_path)

    return metrics_report

def main():
    """Entry point for the training script."""
    try:
        results = run_training_pipeline()
        print("Training pipeline completed successfully.")
        print(f"CV R²: {results['cv_mean_r2']:.4f} (+/- {results['cv_std_r2']:.4f})")
        print(f"Test MAE: {results['test_mae']:.4f}")
        print(f"Test R²: {results['test_r2']:.4f}")
        if results.get('zero_variance_composition'):
            print("WARNING: Pure aluminum detected. Interaction importance analysis skipped.")
    except Exception as e:
        print(f"Training pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()