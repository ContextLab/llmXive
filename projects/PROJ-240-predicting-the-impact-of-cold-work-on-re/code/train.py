"""
Train Random Forest model, perform CV, evaluate, and save metrics (T024, T025, T026, T027).
This script produces the model artifact and the internal metrics file required by T028.
"""
import json
import os
import sys
import pickle
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_project_root, get_random_seed, get_data_split_ratio

def load_final_dataset(data_path: Path) -> pd.DataFrame:
    """Load the final dataset from T020."""
    if not data_path.exists():
        raise FileNotFoundError(f"Final dataset not found: {data_path}")
    return pd.read_csv(data_path)

def split_data(df: pd.DataFrame, target_col: str = "time_to_peak_min") -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into train/test sets (80/20) stratified on binned target.
    """
    seed = get_random_seed()
    ratio = get_data_split_ratio() # e.g., 0.2 for test size

    # Create bins for stratification
    df_temp = df.copy()
    df_temp['bin'] = pd.qcut(df_temp[target_col], q=5, duplicates='drop')

    train_df, test_df = train_test_split(
        df_temp,
        test_size=ratio,
        random_state=seed,
        stratify=df_temp['bin']
    )

    # Drop the bin column before returning features
    train_features = train_df.drop(columns=[target_col, 'bin'])
    test_features = test_df.drop(columns=[target_col, 'bin'])
    train_target = train_df[target_col]
    test_target = test_df[target_col]

    return train_features, test_features, train_target, test_target

def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """Train a Random Forest Regressor."""
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=get_random_seed(),
        n_jobs=-1 # Use all available CPU cores
    )
    model.fit(X_train, y_train)
    return model

def cross_validate_model(model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series) -> Tuple[float, float]:
    """
    Perform 5-fold cross-validation.
    Returns mean R2 and std R2.
    """
    scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    return scores.mean(), scores.std()

def evaluate_model(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple[float, float]:
    """
    Evaluate model on held-out test set.
    Returns MAE and R2.
    """
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    return mae, r2

def save_model(model: RandomForestRegressor, model_path: Path):
    """Save model to pickle file (T027)."""
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f, protocol=4)

def save_metrics(metrics: Dict[str, Any], metrics_path: Path):
    """Save metrics to JSON file (internal for T028)."""
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def detect_pure_aluminum(df: pd.DataFrame) -> bool:
    """
    Detect if the dataset is pure aluminum (zero variance in composition columns).
    """
    composition_cols = ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    # Check if all composition columns exist
    if not all(col in df.columns for col in composition_cols):
        return False
    
    # Check if standard deviation is zero for all composition columns
    for col in composition_cols:
        if df[col].std() != 0:
            return False
    return True

def run_training_pipeline():
    """
    Orchestrate the training pipeline:
    1. Load final dataset
    2. Detect pure aluminum
    3. Split data
    4. Train model
    5. Cross-validate
    6. Evaluate
    7. Save model and metrics
    """
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "final_dataset.csv"
    model_path = project_root / "artifacts" / "models" / "kinetic_model.pkl"
    metrics_path = project_root / "artifacts" / "reports" / "training_metrics_internal.json"

    if not data_path.exists():
        raise FileNotFoundError(f"Final dataset not found at {data_path}. Run T020 first.")

    # 1. Load data
    df = load_final_dataset(data_path)
    print(f"Loaded dataset with {len(df)} rows.")

    # 2. Detect pure aluminum
    pure_aluminum = detect_pure_aluminum(df)
    if pure_aluminum:
        print("WARNING: Pure aluminum dataset detected (zero variance in composition).")
        print("Skipping interaction importance calculation (handled in T029/T038).")

    # 3. Split data
    X_train, X_test, y_train, y_test = split_data(df)
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # 4. Train model
    print("Training Random Forest model...")
    model = train_model(X_train, y_train)

    # 5. Cross-validate
    print("Performing 5-fold cross-validation...")
    cv_mean, cv_std = cross_validate_model(model, X_train, y_train)
    print(f"CV R2: {cv_mean:.4f} (+/- {cv_std:.4f})")

    # 6. Evaluate
    print("Evaluating on test set...")
    test_mae, test_r2 = evaluate_model(model, X_test, y_test)
    print(f"Test MAE: {test_mae:.4f}, Test R2: {test_r2:.4f}")

    # 7. Save artifacts
    save_model(model, model_path)
    print(f"Model saved to {model_path}")

    metrics = {
        "cv_r2_mean": cv_mean,
        "cv_r2_std": cv_std,
        "test_mae": test_mae,
        "test_r2": test_r2,
        "pure_aluminum_flag": pure_aluminum
    }
    save_metrics(metrics, metrics_path)
    print(f"Internal metrics saved to {metrics_path}")

    return metrics

def main():
    try:
        run_training_pipeline()
    except Exception as e:
        print(f"Error in training pipeline: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
