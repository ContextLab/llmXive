import json
import os
import sys
import pickle
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from config import get_project_root, get_random_seed, get_data_split_ratio

def load_final_dataset(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load the final processed dataset."""
    if filepath is None:
        project_root = get_project_root()
        filepath = os.path.join(project_root, "data", "processed", "final_dataset.csv")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Final dataset not found at {filepath}")
    
    return pd.read_csv(filepath)

def split_data(df: pd.DataFrame, target_col: str = "time_to_peak_min") -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into train/test sets.
    Stratifies on binned target variable to ensure distribution preservation.
    """
    seed = get_random_seed()
    test_size = get_data_split_ratio()
    
    # Bin the target for stratification if variance exists
    if df[target_col].std() > 0:
        try:
            # Create 10 bins for stratification
            bins = pd.qcut(df[target_col], q=10, duplicates='drop')
            stratify = bins
        except ValueError:
            # Fallback if qcut fails (e.g., too few unique values)
            stratify = None
            print("Warning: Stratification failed, using non-stratified split.")
    else:
        stratify = None
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=stratify
    )
    
    return X_train, X_test, y_train, y_test

def detect_pure_aluminum(df: pd.DataFrame) -> bool:
    """
    Detect if the dataset represents pure aluminum (zero variance in composition).
    Checks Mn, Mg, Si, Cu columns.
    """
    composition_cols = ["Mn_wt", "Mg_wt", "Si_wt", "Cu_wt"]
    # Ensure columns exist
    if not all(col in df.columns for col in composition_cols):
        return False
    
    # Check if std dev is effectively zero for all composition columns
    return all(df[col].std() < 1e-9 for col in composition_cols)

def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """
    Train a Random Forest Regressor.
    Parameters: n_estimators=100, max_depth=None (default) to ensure runtime < 60 min on 10k rows.
    """
    # T043: Explicitly set n_estimators=100 and max_depth=None
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=get_random_seed(),
        n_jobs=-1  # Use all available CPU cores
    )
    model.fit(X_train, y_train)
    return model

def cross_validate_model(model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series) -> Tuple[float, float]:
    """
    Perform 5-fold cross-validation.
    Returns mean R2 and standard deviation.
    """
    scores = cross_val_score(model, X, y, cv=5, scoring='r2', n_jobs=-1)
    return scores.mean(), scores.std()

def evaluate_model(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple[float, float]:
    """
    Evaluate model on test set.
    Returns MAE and R2.
    """
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    return mae, r2

def save_model(model: RandomForestRegressor, filepath: Optional[str] = None):
    """Save the trained model using pickle protocol 4."""
    if filepath is None:
        project_root = get_project_root()
        filepath = os.path.join(project_root, "artifacts", "models", "kinetic_model.pkl")
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        pickle.dump(model, f, protocol=4)

def save_metrics(metrics: Dict[str, Any], filepath: Optional[str] = None):
    """Save training metrics to JSON."""
    if filepath is None:
        project_root = get_project_root()
        filepath = os.path.join(project_root, "artifacts", "reports", "training_metrics.json")
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(metrics, f, indent=2)

def run_training_pipeline():
    """
    Main pipeline for training:
    1. Load data
    2. Split data
    3. Detect pure aluminum
    4. Train model
    5. Cross-validate
    6. Evaluate on test set
    7. Save model and metrics
    """
    print("Starting training pipeline...")
    
    # 1. Load Data
    df = load_final_dataset()
    print(f"Loaded dataset with {len(df)} rows.")
    
    # Validate size limit (FR-003)
    if len(df) > 10000:
        print(f"Warning: Dataset size {len(df)} exceeds 10000. Truncating.")
        df = df.head(10000)
    
    # 2. Split Data
    X_train, X_test, y_train, y_test = split_data(df)
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # 3. Detect Pure Aluminum
    is_pure_al = detect_pure_aluminum(df)
    if is_pure_al:
        print("Detected Pure Aluminum dataset (zero variance in composition).")
        print("Warning: Interaction terms may be invalid. Proceeding with main effects only logic if applicable.")
    
    # 4. Train Model
    start_time = time.time()
    model = train_model(X_train, y_train)
    training_duration = time.time() - start_time
    print(f"Model training completed in {training_duration:.2f} seconds.")
    
    # 5. Cross-Validate
    cv_mean, cv_std = cross_validate_model(model, X_train, y_train)
    print(f"Cross-Validation R2: {cv_mean:.4f} (+/- {cv_std:.4f})")
    
    # 6. Evaluate
    test_mae, test_r2 = evaluate_model(model, X_test, y_test)
    print(f"Test MAE: {test_mae:.4f}, Test R2: {test_r2:.4f}")
    
    # 7. Save Artifacts
    metrics = {
        "cv_r2_mean": float(cv_mean),
        "cv_r2_std": float(cv_std),
        "test_mae": float(test_mae),
        "test_r2": float(test_r2),
        "pure_aluminum_flag": is_pure_al,
        "training_duration_seconds": float(training_duration),
        "n_estimators": 100,
        "max_depth": None
    }
    
    save_model(model)
    save_metrics(metrics)
    
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