import os
import sys
import json
import logging
import traceback
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.externals import joblib

# Project imports based on API surface
from config import get_path_absolute, get_path_results, ensure_directory
from ingestion.models import ModelMetrics
from exceptions import DownloadError, MemoryErrorHandled

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_split_indices(split_path: str) -> Dict[str, List[int]]:
    """Load split indices from JSON file."""
    if not os.path.exists(split_path):
        raise FileNotFoundError(f"Split indices file not found: {split_path}")
    with open(split_path, 'r') as f:
        return json.load(f)

def load_dataset(dataset_path: str) -> pd.DataFrame:
    """Load the processed dataset."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    return pd.read_csv(dataset_path)

def extract_features_targets(df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """Extract features and targets from dataframe."""
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, n_estimators: int = 100) -> RandomForestRegressor:
    """Train a Random Forest regressor."""
    logger.info(f"Training Random Forest with {n_estimators} estimators...")
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    return model

def train_gradient_boosting(X_train: np.ndarray, y_train: np.ndarray, n_estimators: int = 100) -> GradientBoostingRegressor:
    """Train a Gradient Boosting regressor."""
    logger.info(f"Training Gradient Boosting with {n_estimators} estimators...")
    model = GradientBoostingRegressor(n_estimators=n_estimators, random_state=42)
    model.fit(X_train, y_train)
    return model

def train_ridge_regression(X_train: np.ndarray, y_train: np.ndarray, alpha: float = 1.0) -> Ridge:
    """Train a Ridge Regression model."""
    logger.info("Training Ridge Regression...")
    model = Ridge(alpha=alpha, random_state=42)
    model.fit(X_train, y_train)
    return model

def save_model(model: Any, model_path: str) -> None:
    """Save a trained model to disk."""
    ensure_directory(model_path)
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")

def calculate_molecular_weight_baseline(df: pd.DataFrame, target_col: str, feature_col: str = 'molecular_weight') -> Dict[str, float]:
    """
    Calculate baseline metrics using Molecular Weight as the sole predictor for Lattice Parameters.
    
    This implements a simple baseline where the prediction for a sample is its own molecular weight
    (or a scaled version). For this implementation, we assume a direct linear relationship:
    Prediction = Molecular Weight.
    
    If the target is 'Lattice Parameters' (which might be a string representation or a specific column),
    we ensure we are comparing numeric values.
    
    Args:
        df: The dataset dataframe.
        target_col: The name of the target column (e.g., 'lattice_volume' or similar).
        feature_col: The name of the molecular weight column.
        
    Returns:
        Dictionary with 'r2' and 'mae' metrics.
    """
    if feature_col not in df.columns:
        logger.warning(f"Feature column '{feature_col}' not found. Cannot calculate MW baseline.")
        return {'r2': 0.0, 'mae': float('inf'), 'status': 'failed', 'reason': f"Column {feature_col} missing"}

    if target_col not in df.columns:
        logger.warning(f"Target column '{target_col}' not found. Cannot calculate MW baseline.")
        return {'r2': 0.0, 'mae': float('inf'), 'status': 'failed', 'reason': f"Column {target_col} missing"}

    # Clean data: drop rows with NaN in MW or Target
    clean_df = df[[feature_col, target_col]].dropna()
    
    if len(clean_df) == 0:
        return {'r2': 0.0, 'mae': float('inf'), 'status': 'failed', 'reason': "No valid data rows"}

    X = clean_df[feature_col].values
    y = clean_df[target_col].values

    # Baseline strategy: Predict y using X directly (Identity mapping or simple linear fit)
    # For a true "baseline" often we just predict the mean of y, but the task specifies
    # "Molecular Weight baseline regression", implying MW is the predictor.
    # We will perform a simple linear regression (slope=1, intercept=0) as a naive physics-informed baseline,
    # or fit a Ridge(0) to see how much MW explains variance.
    # Let's fit a simple Ridge with alpha=0 (equivalent to OLS with no regularization) to measure 
    # how well MW *predicts* the target, which is the baseline performance.
    
    # However, a "baseline" usually implies a simple heuristic. 
    # Heuristic 1: Predict mean of y.
    # Heuristic 2: Predict y = MW * k.
    # Let's fit a Ridge model with MW as the single feature to get the best possible R2/MAE for MW.
    
    X_reshaped = X.reshape(-1, 1)
    model = Ridge(alpha=0.0) # No regularization to see max fit
    model.fit(X_reshaped, y)
    
    y_pred = model.predict(X_reshaped)
    
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    logger.info(f"Molecular Weight Baseline - R2: {r2:.4f}, MAE: {mae:.4f}, Coeff: {model.coef_[0]:.4f}")
    
    return {
        'r2': float(r2),
        'mae': float(mae),
        'coefficient': float(model.coef_[0]),
        'intercept': float(model.intercept_),
        'status': 'success',
        'method': 'Ridge(alpha=0) with Molecular Weight as sole feature'
    }

def calculate_majority_class_baseline(df: pd.DataFrame, target_col: str) -> Dict[str, Any]:
    """
    Calculate majority class baseline for classification tasks.
    
    Args:
        df: The dataset dataframe.
        target_col: The name of the target column.
        
    Returns:
        Dictionary with accuracy and distribution metrics.
    """
    if target_col not in df.columns:
        return {'accuracy': 0.0, 'status': 'failed', 'reason': f"Column {target_col} missing"}

    # Only proceed if target is categorical
    if not pd.api.types.is_categorical_dtype(df[target_col]) and not pd.api.types.is_object_dtype(df[target_col]):
        # Check if it's numeric but discrete (like space group numbers)
        try:
            # If it's numeric, we still treat it as classes for this baseline
            pass
        except:
            return {'accuracy': 0.0, 'status': 'skipped', 'reason': 'Target is not categorical'}

    # For the full dataset, the majority class accuracy is the frequency of the most common class
    value_counts = df[target_col].value_counts()
    if len(value_counts) == 0:
        return {'accuracy': 0.0, 'status': 'failed', 'reason': 'No data'}
        
    majority_count = value_counts.iloc[0]
    total_count = len(df)
    accuracy = majority_count / total_count
    
    return {
        'accuracy': float(accuracy),
        'majority_class': str(value_counts.index[0]),
        'majority_count': int(majority_count),
        'total_samples': int(total_count),
        'status': 'success'
    }

def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray, model_name: str) -> Dict[str, float]:
    """Evaluate a model and return metrics."""
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    logger.info(f"{model_name} - R2: {r2:.4f}, MAE: {mae:.4f}")
    return {'r2': float(r2), 'mae': float(mae)}

def main():
    """
    Main entry point for training models and calculating baselines.
    This function specifically implements T017 (MW Baseline) and T017b (Majority Baseline)
    as part of the training pipeline.
    """
    # Paths
    dataset_path = get_path_absolute("data/processed/grouped_dataset.csv")
    split_path = get_path_absolute("data/processed/split_indices.json")
    results_dir = get_path_results()
    ensure_directory(results_dir)
    
    mw_baseline_path = get_path_absolute("data/results/mw_baseline_metrics.json")
    majority_baseline_path = get_path_absolute("data/results/majority_class_baseline_metrics.json")

    logger.info("Starting training and baseline calculation...")

    try:
        # Load Data
        logger.info(f"Loading dataset from {dataset_path}")
        df = load_dataset(dataset_path)
        
        logger.info(f"Loading split indices from {split_path}")
        splits = load_split_indices(split_path)
        
        train_idx = splits['train']
        test_idx = splits['test']
        
        df_train = df.iloc[train_idx]
        df_test = df.iloc[test_idx]

        # Define targets and features
        # Assuming 'molecular_weight' is in the dataset from T011/T012
        # Assuming lattice parameters are in a column named 'lattice_volume' or similar.
        # The task specifies 'Lattice Parameters' as the target.
        # We will look for a column that represents lattice volume/parameters.
        # If the column is a string representation, we might need to parse it, but assuming numeric for now.
        
        # Check for common lattice columns
        possible_lattice_cols = ['lattice_volume', 'lattice_parameters', 'volume']
        target_col = None
        for col in possible_lattice_cols:
            if col in df.columns:
                target_col = col
                break
        
        if not target_col:
            # Fallback: try to find a column with 'lattice' in the name
            lattice_cols = [c for c in df.columns if 'lattice' in c.lower()]
            if lattice_cols:
                target_col = lattice_cols[0]
            else:
                raise ValueError("Could not identify Lattice Parameters target column in dataset.")

        feature_cols = [c for c in df.columns if c.startswith('fingerprint_') or c == 'molecular_weight']
        
        if 'molecular_weight' not in feature_cols:
            raise ValueError("Molecular Weight column not found in features.")

        # --- T017: Molecular Weight Baseline for Regression (Lattice Parameters) ---
        logger.info("Calculating Molecular Weight Baseline for Lattice Parameters...")
        mw_metrics = calculate_molecular_weight_baseline(df_test, target_col, 'molecular_weight')
        
        with open(mw_baseline_path, 'w') as f:
            json.dump(mw_metrics, f, indent=2)
        logger.info(f"Molecular Weight baseline metrics saved to {mw_baseline_path}")

        # --- T017b: Majority Class Baseline for Classification (Space Group) ---
        logger.info("Calculating Majority Class Baseline for Space Group...")
        if 'space_group' in df.columns:
            majority_metrics = calculate_majority_class_baseline(df_test, 'space_group')
            with open(majority_baseline_path, 'w') as f:
                json.dump(majority_metrics, f, indent=2)
            logger.info(f"Majority class baseline metrics saved to {majority_baseline_path}")
        else:
            logger.warning("Space Group column not found. Skipping majority class baseline.")
            with open(majority_baseline_path, 'w') as f:
                json.dump({'status': 'skipped', 'reason': 'Space Group column missing'}, f)

        # --- Train Full Models (T016 continuation) ---
        # Extract features and targets for full training
        X_train, y_train = extract_features_targets(df_train, target_col, feature_cols)
        X_test, y_test = extract_features_targets(df_test, target_col, feature_cols)

        # Train models
        rf_model = train_random_forest(X_train, y_train)
        gb_model = train_gradient_boosting(X_train, y_train)
        ridge_model = train_ridge_regression(X_train, y_train)

        # Save models
        models_dir = get_path_absolute("data/models")
        ensure_directory(models_dir)
        save_model(rf_model, get_path_absolute("data/models/rf_model.pkl"))
        save_model(gb_model, get_path_absolute("data/models/gb_model.pkl"))
        save_model(ridge_model, get_path_absolute("data/models/ridge_model.pkl"))

        # Evaluate models
        rf_metrics = evaluate_model(rf_model, X_test, y_test, "RandomForest")
        gb_metrics = evaluate_model(gb_model, X_test, y_test, "GradientBoosting")
        ridge_metrics = evaluate_model(ridge_model, X_test, y_test, "Ridge")

        # Save full metrics (partial implementation for T019 context)
        full_metrics = {
            'random_forest': rf_metrics,
            'gradient_boosting': gb_metrics,
            'ridge_regression': ridge_metrics,
            'baselines': {
                'molecular_weight': mw_metrics,
                'majority_class': majority_metrics if 'space_group' in df.columns else None
            }
        }
        
        metrics_path = get_path_absolute("data/results/model_metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump(full_metrics, f, indent=2)
        
        logger.info("Training and evaluation complete.")

    except Exception as e:
        logger.error(f"Error during training/baseline calculation: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()