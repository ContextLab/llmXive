"""
User Story 2: Predictive Model Training and Validation.
Implements Random Forest Regressor training with CPU-only execution,
5-fold CV, and held-out test set evaluation.
"""
import json
import os
import sys
import pickle
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import KBinsDiscretizer

# Import project utilities and config
from config import get_project_root, get_max_rows, get_random_seed, get_data_split_ratio
from utils import validate_physical_bounds, detect_type_confusion

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def load_final_dataset(filepath: Path) -> pd.DataFrame:
    """Load the final engineered dataset."""
    if not filepath.exists():
        raise FileNotFoundError(f"Final dataset not found at {filepath}")
    df = pd.read_csv(filepath)
    return df

def split_data(df: pd.DataFrame, target_col: str, seed: int, test_ratio: float):
    """
    Split data into train and test sets.
    Stratify on binned target variable to handle low variance.
    """
    # Bin the target for stratification
    n_bins = 10
    try:
        discretizer = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy='uniform')
        # Ensure we have enough samples for stratification
        if len(df) < n_bins * 2:
            print(f"Warning: Dataset too small ({len(df)}) for {n_bins} bins. Using non-stratified split.")
            X_train, X_test, y_train, y_test = train_test_split(
                df.drop(columns=[target_col]),
                df[target_col],
                test_size=test_ratio,
                random_state=seed
            )
            return X_train, X_test, y_train, y_test

        y_binned = discretizer.fit_transform(df[[target_col]].values).ravel()

        # Check for empty bins after binning
        unique_bins = np.unique(y_binned)
        if len(unique_bins) < 2:
            print(f"Warning: Only {len(unique_bins)} unique bins found. Using non-stratified split.")
            X_train, X_test, y_train, y_test = train_test_split(
                df.drop(columns=[target_col]),
                df[target_col],
                test_size=test_ratio,
                random_state=seed
            )
        else:
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
            # We need to use train_test_split with stratify
            X_train, X_test, y_train, y_test = train_test_split(
                df.drop(columns=[target_col]),
                df[target_col],
                test_size=test_ratio,
                random_state=seed,
                stratify=y_binned
            )
    except Exception as e:
        print(f"Warning: Stratification failed ({e}). Using non-stratified split.")
        X_train, X_test, y_train, y_test = train_test_split(
            df.drop(columns=[target_col]),
            df[target_col],
            test_size=test_ratio,
            random_state=seed
        )

    return X_train, X_test, y_train, y_test

def detect_pure_aluminum(df: pd.DataFrame, composition_cols: List[str]) -> bool:
    """
    Check if all composition columns have near-zero standard deviation.
    Returns True if pure aluminum is detected.
    """
    if not composition_cols or not all(col in df.columns for col in composition_cols):
        # If columns missing, assume not pure aluminum (or handle as error)
        return False
    
    stds = df[composition_cols].std()
    # Check if all stds are effectively zero
    return (stds < 1e-9).all()

def train_model(X_train: pd.DataFrame, y_train: pd.Series, n_estimators: int = 100, max_depth: Optional[int] = None):
    """
    Train a Random Forest Regressor.
    Parameters set per T049: n_estimators=100, max_depth=None (default).
    """
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=get_random_seed(),
        n_jobs=-1  # Use all available CPU cores
    )
    model.fit(X_train, y_train)
    return model

def cross_validate_model(model, X: pd.DataFrame, y: pd.Series, n_splits: int = 5):
    """Perform k-fold cross-validation and return R2 scores."""
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=get_random_seed())
    # For regression, we can't stratify directly on y unless binned, but sklearn cross_val_score
    # doesn't take stratify. We'll just use KFold for R2.
    from sklearn.model_selection import KFold
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=get_random_seed())
    
    scores = cross_val_score(model, X, y, cv=kf, scoring='r2')
    return scores

def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series):
    """Evaluate model on test set and return MAE and R2."""
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    return mae, r2

def save_model(model: Any, filepath: Path):
    """Save model to pickle file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(model, f, protocol=4)

def load_baseline_stats(filepath: Path) -> Dict[str, Any]:
    """Load baseline statistics from JSON."""
    if not filepath.exists():
        raise FileNotFoundError(f"Baseline stats not found at {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_metrics(metrics: Dict[str, Any], filepath: Path):
    """Save metrics to JSON."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)

# --------------------------------------------------------------------------
# Pipeline Logic
# --------------------------------------------------------------------------

def run_training_pipeline():
    """
    Main training pipeline:
    1. Load final dataset.
    2. Enforce row cap.
    3. Detect pure aluminum.
    4. Split data.
    5. Train Interaction Model (n_estimators=100, max_depth=None).
    6. Cross-validate.
    7. Evaluate on test set.
    8. Save model and metrics.
    """
    project_root = get_project_root()
    final_dataset_path = project_root / "data" / "processed" / "final_dataset.csv"
    baseline_stats_path = project_root / "artifacts" / "reports" / "baseline_stats.json"
    model_path = project_root / "artifacts" / "models" / "kinetic_model.pkl"
    metrics_path = project_root / "artifacts" / "reports" / "training_metrics.json"

    # 1. Load Data
    print("Loading final dataset...")
    df = load_final_dataset(final_dataset_path)

    # 2. Enforce Row Cap (FR-003)
    max_rows = get_max_rows()
    if len(df) > max_rows:
        print(f"Warning: Dataset size ({len(df)}) exceeds cap ({max_rows}). Truncating.")
        # Keep first N rows for reproducibility in this context, or sample
        df = df.head(max_rows)

    # Define features and target
    target_col = "time_to_peak_min"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    # Define composition columns for pure aluminum check
    composition_cols = ["Mn_wt", "Mg_wt", "Si_wt", "Cu_wt"]
    interaction_cols = [c for c in df.columns if c.startswith("cold_work_") and c not in composition_cols and c != "cold_work_pct"]
    main_cols = [c for c in df.columns if c not in [target_col] + interaction_cols]
    
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # 3. Detect Pure Aluminum
    is_pure_al = detect_pure_aluminum(df, composition_cols)
    if is_pure_al:
        print("WARNING: Pure Aluminum detected (zero variance in composition). Interaction importance calculation will be skipped in downstream tasks.")

    # 4. Split Data
    print("Splitting data...")
    seed = get_random_seed()
    test_ratio = get_data_split_ratio()
    X_train, X_test, y_train, y_test = split_data(df, target_col, seed, test_ratio)

    # 5. Train Model
    # T049 Requirement: n_estimators=100, max_depth=None (default)
    print("Training Random Forest Regressor (n_estimators=100, max_depth=None)...")
    start_time = time.time()
    model = train_model(X_train, y_train, n_estimators=100, max_depth=None)
    train_time = time.time() - start_time
    print(f"Training completed in {train_time:.2f} seconds.")

    # 6. Cross-Validate
    print("Performing 5-fold cross-validation...")
    cv_scores = cross_validate_model(model, X_train, y_train)
    cv_r2_mean = float(np.mean(cv_scores))
    cv_r2_std = float(np.std(cv_scores))
    print(f"CV R2: {cv_r2_mean:.4f} (+/- {cv_r2_std:.4f})")

    # 7. Evaluate on Test Set
    print("Evaluating on test set...")
    test_mae, test_r2 = evaluate_model(model, X_test, y_test)
    print(f"Test MAE: {test_mae:.4f}, Test R2: {test_r2:.4f}")

    # 8. Save Model
    print(f"Saving model to {model_path}...")
    save_model(model, model_path)

    # 9. Calculate Threshold Check (SC-006)
    mae_pass = False
    threshold = None
    try:
        baseline_stats = load_baseline_stats(baseline_stats_path)
        baseline_mean = baseline_stats.get("baseline_mean", 0)
        # Threshold: e.g., 20% of baseline mean (common heuristic, or specific spec value)
        # Spec says: "fixed proportion of baseline_mean". Let's use 0.2 as a reasonable default if not specified.
        # If the spec had a specific fraction, we'd use that. Assuming 20% for now.
        threshold = baseline_mean * 0.2
        mae_pass = test_mae < threshold
        print(f"MAE Threshold Check: {test_mae:.4f} < {threshold:.4f} -> {mae_pass}")
    except FileNotFoundError:
        print("Warning: Baseline stats not found. Skipping MAE threshold check.")

    # 10. Save Metrics
    metrics = {
        "cv_r2_mean": cv_r2_mean,
        "cv_r2_std": cv_r2_std,
        "test_mae": test_mae,
        "test_r2": test_r2,
        "pure_aluminum_flag": is_pure_al,
        "train_time_seconds": train_time,
        "n_estimators": 100,
        "max_depth": None,
        "mae_threshold_check": {
            "passed": mae_pass,
            "threshold": threshold,
            "actual_mae": test_mae
        }
    }
    print(f"Saving metrics to {metrics_path}...")
    save_metrics(metrics, metrics_path)

    print("Training pipeline completed successfully.")
    return metrics

def main():
    """Entry point for the training script."""
    try:
        run_training_pipeline()
    except Exception as e:
        print(f"Error during training pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()