import os
import sys
import json
import logging
import traceback
import time
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_absolute_error
from sklearn.model_selection import cross_val_score
import joblib

from config import (
    get_path_data, get_path_results, get_path_models,
    get_path_processed_data, load_runtime_config
)
from logging_config import get_logger, log_event
from modeling.timeout_handler import enforce_timeout, log_timeout_action, calculate_optimized_trees

logger = get_logger(__name__)

# --- Timeouts and Signals ---

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Training timeout exceeded")

# --- Data Loading Helpers ---

def load_split_indices(split_file: str = "split_indices.json") -> Dict[str, List[int]]:
    """Load split indices from JSON file."""
    path = Path(get_path_processed_data()) / split_file
    if not path.exists():
        raise FileNotFoundError(f"Split indices file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_dataset(dataset_file: str = "grouped_dataset.csv") -> pd.DataFrame:
    """Load the preprocessed dataset."""
    path = Path(get_path_processed_data()) / dataset_file
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    return pd.read_csv(path)

def extract_features_targets(df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
    """Extract features (fingerprints) and targets from DataFrame."""
    # Features are assumed to be columns starting with 'fp_' or similar, or we parse a 'fingerprints' column
    # Based on typical pipeline, let's assume a 'fingerprints' column contains lists/arrays, or individual bit columns
    # For robustness, we look for a column named 'fingerprints' and explode it, or use all numeric columns except targets
    if 'fingerprints' in df.columns:
        # Assuming fingerprints are stored as string representation of list or array
        # Or potentially already exploded into separate columns?
        # Let's assume a column 'fingerprints' holds the list/array
        X = np.vstack(df['fingerprints'].values)
    else:
        # Fallback: assume all numeric columns except target are features
        feature_cols = [c for c in df.columns if c not in [target_col] and df[c].dtype in [np.float64, np.int64]]
        X = df[feature_cols].values

    y = df[target_col].values
    return X, y

# --- Model Training Functions ---

def train_random_forest(X: np.ndarray, y: np.ndarray, timeout_seconds: int = 21600, n_estimators: Optional[int] = None) -> RandomForestClassifier:
    """Train a Random Forest classifier."""
    if n_estimators is None:
        n_estimators = calculate_optimized_trees(X.shape[0])
    logger.info(f"Training Random Forest with {n_estimators} trees...")

    model = RandomForestClassifier(n_estimators=n_estimators, random_state=42, n_jobs=-1)

    def run_training():
        return model.fit(X, y)

    return enforce_timeout(run_training, timeout_seconds, "RandomForest")

def train_gradient_boosting(X: np.ndarray, y: np.ndarray, timeout_seconds: int = 21600) -> GradientBoostingClassifier:
    """Train a Gradient Boosting classifier."""
    logger.info("Training Gradient Boosting...")
    model = GradientBoostingClassifier(n_estimators=100, random_state=42)

    def run_training():
        return model.fit(X, y)

    return enforce_timeout(run_training, timeout_seconds, "GradientBoosting")

def train_ridge_regression(X: np.ndarray, y: np.ndarray, timeout_seconds: int = 21600) -> Ridge:
    """Train a Ridge Regression model."""
    logger.info("Training Ridge Regression...")
    model = Ridge(random_state=42)

    def run_training():
        return model.fit(X, y)

    return enforce_timeout(run_training, timeout_seconds, "Ridge")

def save_model(model, path: str):
    """Save model to disk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    logger.info(f"Model saved to {path}")

# --- Baseline Calculations ---

def calculate_molecular_weight_baseline(X: np.ndarray, y: np.ndarray, df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Molecular Weight baseline for regression target (Lattice Parameters).
    Since MW is a property of the molecule (row), we use it as the predictor.
    We assume 'molecular_weight' column exists in df.
    """
    if 'molecular_weight' not in df.columns:
        logger.warning("Molecular Weight column not found. Skipping MW baseline.")
        return {"status": "skipped", "reason": "molecular_weight column missing"}

    mw = df['molecular_weight'].values
    # Simple baseline: predict mean MW for all? Or use MW directly?
    # The task says "Molecular Weight baseline regression logic".
    # Usually, this means predicting the target using MW as the single feature.
    # But if it's a baseline, it might just be predicting the mean of Y.
    # Let's interpret as: Predict Y using MW (single feature regression).
    # However, standard "baseline" often implies a trivial predictor (mean).
    # Let's calculate the R2 of a model that just predicts the mean of Y (trivial baseline)
    # AND potentially a simple linear model using MW if the spec implies MW is the feature.
    # Given the phrasing "Molecular Weight baseline", it likely means using MW as the predictor.
    
    # Let's implement: Predict Y using MW as the single feature.
    # We need to reshape MW for sklearn
    mw_reshaped = mw.reshape(-1, 1)
    
    baseline_model = Ridge()
    baseline_model.fit(mw_reshaped, y)
    y_pred = baseline_model.predict(mw_reshaped)
    
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    return {
        "baseline_type": "molecular_weight_regression",
        "r2": float(r2),
        "mae": float(mae),
        "description": "Ridge regression using Molecular Weight as single feature"
    }

def calculate_molecular_weight_baseline_from_df(df: pd.DataFrame, target_col: str = "lattice_parameters") -> Dict[str, float]:
    """
    Wrapper to calculate MW baseline specifically for the regression target.
    Assumes 'lattice_parameters' is the target.
    """
    # Extract features (MW) and target (Lattice Params)
    if 'molecular_weight' not in df.columns:
        return {"status": "skipped", "reason": "molecular_weight column missing"}
    
    X = df['molecular_weight'].values.reshape(-1, 1)
    # Parse lattice parameters if it's a string representation of a list/array
    # Or if it's already numeric? Assuming it might be a string or needs parsing.
    # For now, assuming y is numeric or can be cast.
    # If lattice_parameters is a complex target (e.g. multiple params), this baseline might be ill-defined.
    # Let's assume target is a single numeric value or we are predicting the first parameter.
    # If the target is a string like "[1.2, 3.4]", we need to parse it.
    # Given the ambiguity, let's assume the target column is numeric for this baseline.
    
    y = df[target_col]
    if isinstance(y.iloc[0], str):
        # Try to parse as list and take first element, or mean?
        # This is risky. Let's assume the dataset builder already flattened this to a single numeric target for regression.
        # If not, we skip.
        logger.error(f"Target column {target_col} contains strings. Cannot compute simple MW baseline.")
        return {"status": "skipped", "reason": "target column is not numeric"}
    
    y = y.values
    
    baseline_model = Ridge()
    baseline_model.fit(X, y)
    y_pred = baseline_model.predict(X)
    
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    return {
        "baseline_type": "molecular_weight_regression",
        "r2": float(r2),
        "mae": float(mae),
        "description": "Ridge regression using Molecular Weight as single feature"
    }

def calculate_majority_class_baseline(df: pd.DataFrame, target_col: str = "space_group") -> Dict[str, Any]:
    """
    Calculate Majority Class baseline for classification target (Space Group).
    Returns the accuracy of predicting the most frequent class for all samples.
    """
    if target_col not in df.columns:
        logger.error(f"Target column {target_col} not found in dataset.")
        return {"status": "error", "reason": f"column {target_col} missing"}
    
    y = df[target_col]
    value_counts = y.value_counts()
    majority_class = value_counts.index[0]
    majority_count = value_counts.iloc[0]
    total_count = len(y)
    
    # Predict majority class for all
    y_pred = [majority_class] * total_count
    
    accuracy = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred, average='macro', zero_division=0)
    
    return {
        "baseline_type": "majority_class",
        "target": target_col,
        "majority_class": str(majority_class),
        "majority_count": int(majority_count),
        "total_samples": int(total_count),
        "accuracy": float(accuracy),
        "macro_f1": float(f1),
        "description": f"Predicting the majority class '{majority_class}' for all samples"
    }

def evaluate_model(model, X_test, y_test, model_type: str) -> Dict[str, float]:
    """Evaluate a model on test data."""
    y_pred = model.predict(X_test)
    
    metrics = {}
    if model_type == "classifier":
        metrics["accuracy"] = float(accuracy_score(y_test, y_pred))
        metrics["macro_f1"] = float(f1_score(y_test, y_pred, average='macro', zero_division=0))
    elif model_type == "regressor":
        metrics["r2"] = float(r2_score(y_test, y_pred))
        metrics["mae"] = float(mean_absolute_error(y_test, y_pred))
    
    return metrics

def main():
    """
    Main entry point for training and baseline calculation.
    Handles both Space Group (classification) and Lattice Parameters (regression) targets.
    Specifically implements T017b: Majority Class Baseline for Space Group.
    """
    logger.info("Starting training and baseline calculation pipeline.")
    
    # Load runtime config for device and timeout
    runtime_config = load_runtime_config()
    device = runtime_config.get("training_device", "cpu")
    timeout_seconds = 21600 # 6 hours default, or from config
    
    # Load data
    try:
        split_indices = load_split_indices()
        dataset = load_dataset("grouped_dataset.csv")
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    
    # Separate indices
    train_idx = split_indices.get("train", [])
    test_idx = split_indices.get("test", [])
    
    df_train = dataset.iloc[train_idx]
    df_test = dataset.iloc[test_idx]
    
    # --- 1. Majority Class Baseline (T017b) ---
    logger.info("Calculating Majority Class Baseline for Space Group...")
    majority_baseline = calculate_majority_class_baseline(df_test, target_col="space_group")
    
    # Save Majority Class Baseline Metrics
    majority_output_path = Path(get_path_results()) / "majority_class_baseline_metrics.json"
    os.makedirs(majority_output_path.parent, exist_ok=True)
    with open(majority_output_path, 'w') as f:
        json.dump(majority_baseline, f, indent=2)
    logger.info(f"Majority Class Baseline saved to {majority_output_path}")
    
    # --- 2. Molecular Weight Baseline (T017) ---
    # Assuming 'lattice_parameters' is the regression target
    logger.info("Calculating Molecular Weight Baseline for Lattice Parameters...")
    mw_baseline = calculate_molecular_weight_baseline_from_df(df_test, target_col="lattice_parameters")
    
    mw_output_path = Path(get_path_results()) / "mw_baseline_metrics.json"
    with open(mw_output_path, 'w') as f:
        json.dump(mw_baseline, f, indent=2)
    logger.info(f"MW Baseline saved to {mw_output_path}")
    
    # --- 3. Train Models (T016 continuation) ---
    # Extract features for Space Group (Classification)
    X_train_sg, y_train_sg = extract_features_targets(df_train, "space_group")
    X_test_sg, y_test_sg = extract_features_targets(df_test, "space_group")
    
    # Train RF and GB for Space Group
    rf_model_sg = train_random_forest(X_train_sg, y_train_sg, timeout_seconds)
    gb_model_sg = train_gradient_boosting(X_train_sg, y_train_sg, timeout_seconds)
    
    # Evaluate
    rf_metrics_sg = evaluate_model(rf_model_sg, X_test_sg, y_test_sg, "classifier")
    gb_metrics_sg = evaluate_model(gb_model_sg, X_test_sg, y_test_sg, "classifier")
    
    # Save Models
    save_model(rf_model_sg, str(Path(get_path_models()) / "rf_model_sg.pkl"))
    save_model(gb_model_sg, str(Path(get_path_models()) / "gb_model_sg.pkl"))
    
    # Extract features for Lattice Parameters (Regression)
    # Assuming we have a specific target column for regression
    X_train_lp, y_train_lp = extract_features_targets(df_train, "lattice_parameters")
    X_test_lp, y_test_lp = extract_features_targets(df_test, "lattice_parameters")
    
    # Train Ridge for Lattice Parameters
    ridge_model_lp = train_ridge_regression(X_train_lp, y_train_lp, timeout_seconds)
    
    # Evaluate
    ridge_metrics_lp = evaluate_model(ridge_model_lp, X_test_lp, y_test_lp, "regressor")
    
    # Save Model
    save_model(ridge_model_lp, str(Path(get_path_models()) / "ridge_model_lp.pkl"))
    
    # --- 4. Aggregate Metrics (Partial for T019) ---
    final_metrics = {
        "space_group": {
            "rf": rf_metrics_sg,
            "gb": gb_metrics_sg,
            "majority_baseline": majority_baseline
        },
        "lattice_parameters": {
            "ridge": ridge_metrics_lp,
            "mw_baseline": mw_baseline
        }
    }
    
    metrics_output_path = Path(get_path_results()) / "model_metrics_partial.json"
    with open(metrics_output_path, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    logger.info(f"Partial model metrics saved to {metrics_output_path}")
    
    logger.info("Training and baseline calculation completed successfully.")

if __name__ == "__main__":
    main()