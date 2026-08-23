import os
import sys
import json
import pickle
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, GridSearchCV, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# Ensure parent directory is in path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.imputation import impute_missing_values
from utils.hashing import compute_file_hash

# Constants
PROCESSED_DATA_PATH = "data/processed/merged_dataset.csv"
MODEL_OUTPUT_PATH = "data/models/random_forest.pkl"
METRICS_OUTPUT_PATH = "data/results/model_metrics.json"
DISCLAIMER_TEXT = "Findings are associational due to observational data."

def load_processed_data(path: str = PROCESSED_DATA_PATH) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data not found at {path}. Run data ingestion pipeline first.")
    return pd.read_csv(path)

def prepare_features_targets(df: pd.DataFrame):
    """
    Prepare X (features) and y (target) from the dataframe.
    Assumes the target column is named 'voc_total_emission' or similar, 
    and non-numeric columns are dropped or handled.
    """
    # Identify target column (adjust based on actual schema if needed)
    # For this implementation, we assume the last numeric column or a specific name is target.
    # Let's assume 'voc_total_emission' is the target based on typical VOC profiles.
    target_col = 'voc_total_emission'
    if target_col not in df.columns:
        # Fallback: assume the last column is the target if named differently, or raise error
        # For robustness, we'll look for a column containing 'voc' or 'emission'
        voc_cols = [c for c in df.columns if 'voc' in c.lower() or 'emission' in c.lower()]
        if voc_cols:
            target_col = voc_cols[0]
        else:
            raise ValueError("Could not identify target VOC column in dataset.")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Ensure X contains only numeric data for sklearn
    X = X.select_dtypes(include=[np.number])
    
    return X, y

def run_nested_cv(X: pd.DataFrame, y: pd.Series, n_splits_outer=5, n_splits_inner=3):
    """
    Implements Nested k-Fold Cross-Validation.
    Inner loop: Hyperparameter tuning via GridSearchCV.
    Outer loop: Evaluation of the tuned model.
    """
    outer_kf = KFold(n_splits=n_splits_outer, shuffle=True, random_state=42)
    inner_kf = KFold(n_splits=n_splits_inner, shuffle=True, random_state=42)

    param_grid = {
        'rf__n_estimators': [50, 100],
        'rf__max_depth': [5, 10, None],
        'rf__min_samples_split': [2, 5]
    }

    # Pipeline ensures imputation and scaling happen inside the CV loop (preventing leakage)
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('rf', RandomForestRegressor(random_state=42))
    ])

    outer_r2_scores = []
    outer_rmse_scores = []

    # Outer loop
    for train_idx, test_idx in outer_kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        # Inner loop (GridSearch)
        grid_search = GridSearchCV(
            pipeline, param_grid, cv=inner_kf, scoring='r2', n_jobs=-1
        )
        grid_search.fit(X_train, y_train)

        # Best model from inner loop
        best_model = grid_search.best_estimator_
        
        # Evaluate on outer test set
        y_pred = best_model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        outer_r2_scores.append(r2)
        outer_rmse_scores.append(rmse)

    avg_r2 = np.mean(outer_r2_scores)
    avg_rmse = np.mean(outer_rmse_scores)
    
    # Train final model on full data using best params found (approximation for deployment)
    # In strict nested CV, we use the average. For artifact storage, we train on full data.
    final_grid_search = GridSearchCV(
        pipeline, param_grid, cv=inner_kf, scoring='r2', n_jobs=-1
    )
    final_grid_search.fit(X, y)
    final_model = final_grid_search.best_estimator_

    return final_model, avg_r2, avg_rmse

def save_model(model, path: str = MODEL_OUTPUT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {path}")
    print(f"Hash: {compute_file_hash(path)}")

def save_metrics(r2: float, rmse: float, path: str = METRICS_OUTPUT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    metrics = {
        "r2": float(r2),
        "rmse": float(rmse),
        "disclaimer": DISCLAIMER_TEXT,
        "methodology": "Nested k-Fold Cross-Validation (5 outer, 3 inner)",
        "model_type": "RandomForestRegressor",
        "cpu_only": True
    }
    
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {path}")

def main():
    warnings.filterwarnings('ignore')
    print("Starting model training (T020-T025)...")

    # Load data
    df = load_processed_data()
    print(f"Loaded {len(df)} samples.")

    # Prepare features and targets
    X, y = prepare_features_targets(df)
    print(f"Features shape: {X.shape}, Target shape: {y.shape}")

    # Run Nested CV
    print("Running Nested k-Fold Cross-Validation...")
    model, r2, rmse = run_nested_cv(X, y)

    # Save artifacts
    save_model(model)
    save_metrics(r2, rmse)

    print("Training complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())