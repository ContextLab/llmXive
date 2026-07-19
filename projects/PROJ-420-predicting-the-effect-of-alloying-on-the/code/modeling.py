import logging
import pickle
import json
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_absolute_error

from config import get_config
from logging_config import get_logger
from schemas.alloy_record import ModelMetrics

logger = get_logger(__name__)
config = get_config()

def load_features_and_target() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the ILR-transformed features and the target variable (Poisson's ratio)
    from the cleaned dataset.
    """
    data_path = config.data_processed / "filtered_alloys.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Required input file not found: {data_path}")

    df = pd.read_csv(data_path)

    # Identify ILR columns (usually prefixed with 'ilr_' or similar based on T019)
    # Assuming T019 creates columns named 'ilr_0', 'ilr_1', etc. or similar.
    # We look for the target column specifically.
    target_col = "poissons_ratio"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in {data_path}")

    # Select feature columns: exclude target and any non-feature columns
    # Based on T019, we expect ILR transformed columns.
    # We assume the DataFrame contains the ILR columns and the target.
    feature_cols = [col for col in df.columns if col != target_col and col != "material_id"]
    
    X = df[feature_cols]
    y = df[target_col]

    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features.")
    return X, y

def train_random_forest_with_cv(X: pd.DataFrame, y: pd.Series, cv_folds: int = 5) -> RandomForestRegressor:
    """
    Train a Random Forest Regressor with k-fold cross-validation.
    Returns the trained model.
    """
    logger.info(f"Starting Random Forest training with {cv_folds}-fold CV.")
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=config.random_seed,
        n_jobs=-1
    )

    # Perform cross-validation
    cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring='neg_mean_absolute_error')
    mae_scores = -cv_scores
    mean_mae = np.mean(mae_scores)
    std_mae = np.std(mae_scores)

    logger.info(f"CV MAE: {mean_mae:.4f} (+/- {std_mae:.4f})")

    # Train on full data
    model.fit(X, y)
    logger.info("Random Forest model trained successfully.")
    return model

def evaluate_model_on_test(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """
    Evaluate the trained model on a held-out test set.
    Returns the Mean Absolute Error (MAE).
    """
    logger.info("Evaluating model on test set...")
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    logger.info(f"Test Set MAE: {mae:.4f}")
    return mae

def save_model(model: RandomForestRegressor, output_path: Optional[Path] = None) -> Path:
    """
    Serialize the trained model to disk.
    """
    if output_path is None:
        output_path = config.models_dir / "rf_model.pkl"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Model saved to {output_path}")
    return output_path

def save_model_metrics(metrics_dict: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the ModelMetrics object (as a dictionary) to a JSON file.
    This satisfies T025: saving results to docs/outputs/model_metrics.json.
    """
    if output_path is None:
        output_path = config.docs_outputs / "model_metrics.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure the directory exists
    with open(output_path, 'w') as f:
        json.dump(metrics_dict, f, indent=2)
    
    logger.info(f"Model metrics saved to {output_path}")
    return output_path

def run_modeling_pipeline() -> Dict[str, Any]:
    """
    Orchestrate the modeling pipeline:
    1. Load features and target
    2. Train/test split
    3. Train model with CV
    4. Evaluate on test set
    5. Save model
    6. Save metrics (T025)
    """
    logger.info("Starting modeling pipeline...")
    
    # 1. Load Data
    X, y = load_features_and_target()
    
    # 2. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=config.random_seed
    )
    logger.info(f"Split data: {len(X_train)} train, {len(X_test)} test.")
    
    # 3. Train Model
    model = train_random_forest_with_cv(X_train, y_train)
    
    # 4. Evaluate
    test_mae = evaluate_model_on_test(model, X_test, y_test)
    
    # 5. Save Model
    save_model(model)
    
    # 6. Prepare and Save Metrics (T025)
    metrics_dict = {
        "model_type": "RandomForestRegressor",
        "cv_folds": 5,
        "cv_mae_mean": float(np.mean(cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_absolute_error') * -1)),
        "cv_mae_std": float(np.std(cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_absolute_error') * -1)),
        "test_mae": float(test_mae),
        "n_train_samples": len(X_train),
        "n_test_samples": len(X_test),
        "random_seed": config.random_seed,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Convert to ModelMetrics if needed, but saving dict is sufficient for JSON
    # The schema defines ModelMetrics, we can instantiate it for validation if desired,
    # but saving the dict directly is robust.
    # Let's validate against the schema to be safe, then save.
    try:
        metrics_obj = ModelMetrics(**metrics_dict)
        metrics_dict = metrics_obj.model_dump()
    except Exception as e:
        logger.warning(f"Metrics object validation warning: {e}. Saving raw dict.")
    
    save_model_metrics(metrics_dict)
    
    logger.info("Modeling pipeline completed successfully.")
    return metrics_dict

def main():
    """
    Entry point for the modeling script.
    """
    setup = get_logger("main")
    setup.info("Running modeling main...")
    try:
        run_modeling_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
