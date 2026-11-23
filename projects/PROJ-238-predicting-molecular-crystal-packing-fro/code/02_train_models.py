import os
import sys
import logging
import json
import hashlib
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Import from local utils/config if available, otherwise setup basic logging
try:
    from code.config import setup_logging, get_config
    logger = setup_logging("training_pipeline")
    config = get_config()
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    config = None

def load_split_data(data_dir: str = "data/processed") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the pre-split train, val, and test datasets."""
    train_path = Path(data_dir) / "train.csv"
    val_path = Path(data_dir) / "val.csv"
    test_path = Path(data_dir) / "test.csv"

    if not all(p.exists() for p in [train_path, val_path, test_path]):
        raise FileNotFoundError(f"Split data files not found in {data_dir}. Ensure T017 tasks are complete.")

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    logger.info(f"Loaded data: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    return train_df, val_df, test_df

def validate_columns(df: pd.DataFrame, required_cols: list) -> bool:
    """Ensure all required columns are present."""
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True

def validate_ids_unique_and_non_overlapping(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> None:
    """Ensure IDs are unique within and across splits."""
    all_ids = np.concatenate([train['id'].values, val['id'].values, test['id'].values])
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Duplicate IDs found across splits.")

def validate_target_distribution(df: pd.DataFrame, target_col: str = "packing_coefficient") -> None:
    """Basic sanity check on target distribution."""
    if df[target_col].isnull().any():
        raise ValueError(f"Target column '{target_col}' contains null values.")

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, random_state: int = 42) -> RandomForestRegressor:
    """Train a Random Forest regressor with default hyperparameters."""
    logger.info("Training Random Forest...")
    model = RandomForestRegressor(random_state=random_state)
    model.fit(X_train, y_train)
    return model

def train_gradient_boosting(X_train: np.ndarray, y_train: np.ndarray, random_state: int = 42) -> GradientBoostingRegressor:
    """Train a Gradient Boosting regressor with default hyperparameters."""
    logger.info("Training Gradient Boosting...")
    model = GradientBoostingRegressor(random_state=random_state)
    model.fit(X_train, y_train)
    return model

def train_mean_baseline(y_train: np.ndarray) -> float:
    """
    Train Mean Predictor baseline.
    Returns the mean of the training set target values.
    """
    logger.info("Computing Mean Baseline (training set mean)...")
    mean_val = float(np.mean(y_train))
    return mean_val

def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray, model_name: str) -> Dict[str, float]:
    """Evaluate a model and return R2, MAE, RMSE."""
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    logger.info(f"{model_name} - R2: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    return {"r2": r2, "mae": mae, "rmse": rmse}

def evaluate_baseline(mean_val: float, y_test: np.ndarray) -> Dict[str, float]:
    """Evaluate the mean baseline predictor."""
    y_pred = np.full_like(y_test, mean_val, dtype=float)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    logger.info(f"Mean Baseline - R2: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    return {"r2": r2, "mae": mae, "rmse": rmse}

def save_model(model: Any, path: Path, model_name: str) -> None:
    """Save model to disk."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Saved {model_name} to {path}")

def save_metrics(metrics: Dict[str, Any], path: Path) -> None:
    """Save metrics to JSON."""
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {path}")

def main():
    """Main execution pipeline for training and baseline."""
    # Configuration
    data_dir = "data/processed"
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    # 1. Load Data
    try:
        train_df, val_df, test_df = load_split_data(data_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 2. Validate
    feature_cols = [col for col in train_df.columns if col not in ['id', 'packing_coefficient']]
    target_col = "packing_coefficient"

    for name, df in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        validate_columns(df, ['id', target_col] + feature_cols)
        validate_target_distribution(df, target_col)

    validate_ids_unique_and_non_overlapping(train_df, val_df, test_df)

    # 3. Prepare Arrays
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values

    # 4. Train Models
    rf_model = train_random_forest(X_train, y_train)
    gb_model = train_gradient_boosting(X_train, y_train)
    mean_baseline_value = train_mean_baseline(y_train)

    # 5. Evaluate Models
    rf_metrics = evaluate_model(rf_model, X_test, y_test, "RandomForest")
    gb_metrics = evaluate_model(gb_model, X_test, y_test, "GradientBoosting")
    baseline_metrics = evaluate_baseline(mean_baseline_value, y_test)

    # 6. Save Artifacts
    save_model(rf_model, output_dir / "rf_model.pkl", "RandomForest")
    save_model(gb_model, output_dir / "gb_model.pkl", "GradientBoosting")
    # Save baseline as a simple value file or pickled float if needed, but here we store in metrics
    
    all_metrics = {
        "RandomForest": rf_metrics,
        "GradientBoosting": gb_metrics,
        "MeanBaseline": baseline_metrics,
        "mean_baseline_value": mean_baseline_value
    }
    
    save_metrics(all_metrics, output_dir / "training_metrics.json")
    logger.info("Training pipeline completed successfully.")

if __name__ == "__main__":
    main()