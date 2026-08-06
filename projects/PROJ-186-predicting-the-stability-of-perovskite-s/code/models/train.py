import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Import from local project structure
from data.preprocess import load_raw_data, split_data
from utils.logging_config import get_logger, log_pipeline_event
from utils.model_metadata import save_model_metadata
from utils.config import get_config_summary

logger = get_logger(__name__)

# Constants matching task requirements
TARGET_COL = "decomposition_energy"
FEATURE_COLS = [
    "tolerance_factor",
    "octahedral_factor",
    "ionic_radius_mismatch",
    "electronegativity_difference",
    "ionic_radius_A",
    "ionic_radius_B",
    "electronegativity_A",
    "electronegativity_B",
]

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the processed features, split into train/test sets.
    Returns X_train, X_test, y_train, y_test.
    """
    data_path = Path("data/processed/features.csv")
    if not data_path.exists():
        raise FileNotFoundError(
            f"Processed data file not found at {data_path}. "
            "Please run the data ingestion pipeline first."
        )

    df = pd.read_csv(data_path)

    # Validate required columns
    missing_cols = [c for c in FEATURE_COLS + [TARGET_COL] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in features.csv: {missing_cols}")

    # Drop rows with NaN in target or features
    initial_count = len(df)
    df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with NaN values in features or target.")

    # Split data (80/20)
    # Using the split_data helper from preprocess if available, otherwise inline
    # The split_data function in preprocess.py handles the 80/20 split
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    log_pipeline_event(
        logger,
        "data_split_complete",
        {
            "train_size": len(X_train),
            "test_size": len(X_test),
            "total_initial": initial_count,
        },
    )

    return X_train, X_test, y_train, y_test

def inner_loop_cv_selection(
    X_train: pd.DataFrame, y_train: pd.Series
) -> Dict[str, Any]:
    """
    Perform inner-loop 5-fold CV grid search to select best hyperparameters.
    Grid: max_depth {10, 15, 20}, min_samples_leaf {1, 2, 4}.
    Returns the best parameters and the GridSearchCV object.
    """
    param_grid = {
        "max_depth": [10, 15, 20],
        "min_samples_leaf": [1, 2, 4],
    }

    base_model = RandomForestRegressor(random_state=42, n_jobs=-1)

    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=5,
        scoring="neg_mean_squared_error",
        n_jobs=-1,
        verbose=1,
    )

    logger.info("Starting GridSearchCV with 5-fold cross-validation...")
    grid_search.fit(X_train, y_train)

    best_params = grid_search.best_params_
    best_score = -grid_search.best_score_  # Convert back to positive MSE

    log_pipeline_event(
        logger,
        "cv_selection_complete",
        {
            "best_params": best_params,
            "best_cv_mse": best_score,
            "best_cv_rmse": np.sqrt(best_score),
        },
    )

    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV RMSE: {np.sqrt(best_score):.4f} eV/atom")

    return best_params, grid_search

def train_model(X_train: pd.DataFrame, y_train: pd.Series, best_params: Dict[str, Any]) -> RandomForestRegressor:
    """
    Train the final model using the best parameters on the full training set.
    """
    logger.info("Training final model on full training set...")
    model = RandomForestRegressor(
        **best_params,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    logger.info("Final model training complete.")
    return model

def evaluate_model(
    model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series
) -> Dict[str, float]:
    """
    Evaluate the model on the held-out test set.
    Returns a dictionary of metrics.
    """
    y_pred = model.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    metrics = {
        "test_rmse": float(rmse),
        "test_r2": float(r2),
        "test_mse": float(mean_squared_error(y_test, y_pred)),
        "n_test_samples": len(y_test),
    }

    log_pipeline_event(
        logger,
        "evaluation_complete",
        {
            "test_rmse": rmse,
            "test_r2": r2,
        },
    )

    logger.info(f"Test RMSE: {rmse:.4f} eV/atom")
    logger.info(f"Test R²: {r2:.4f}")

    # Low confidence flagging (Task T027)
    if rmse > 0.15:
        logger.warning(f"Model confidence LOW: Test RMSE ({rmse:.4f}) > 0.15 eV/atom threshold.")
        metrics["confidence_flag"] = "low"
    else:
        metrics["confidence_flag"] = "high"

    return metrics

def save_artifacts(
    model: RandomForestRegressor,
    metrics: Dict[str, Any],
    best_params: Dict[str, Any],
) -> None:
    """
    Save the trained model to results/model.pkl and metrics to results/metrics.json.
    Also saves metadata via utils.model_metadata.
    """
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    model_path = results_dir / "model.pkl"
    metrics_path = results_dir / "metrics.json"

    # Save model
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

    # Save metrics
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    # Save model metadata (Task T045 requirement)
    config_summary = get_config_summary()
    metadata = {
        "model_type": "RandomForestRegressor",
        "best_params": best_params,
        "metrics": metrics,
        "dft_functional": "PBE",
        "training_samples": config_summary.get("training_samples", "unknown"),
        "feature_columns": FEATURE_COLS,
        "target_column": TARGET_COL,
    }
    save_model_metadata(metadata, model_path)
    logger.info(f"Metadata embedded in {model_path}")

def main():
    """
    Main entry point for the training pipeline.
    Executes data loading, CV selection, training, evaluation, and artifact saving.
    """
    log_pipeline_event(logger, "pipeline_start", {"task": "T031_Model_Training"})

    try:
        # 1. Load Data
        X_train, X_test, y_train, y_test = load_data()

        # 2. Inner-loop CV Selection
        best_params, _ = inner_loop_cv_selection(X_train, y_train)

        # 3. Train Final Model
        model = train_model(X_train, y_train, best_params)

        # 4. Evaluate
        metrics = evaluate_model(model, X_test, y_test)

        # 5. Save Artifacts (T031 Core Requirement)
        save_artifacts(model, metrics, best_params)

        log_pipeline_event(logger, "pipeline_complete", {"status": "success"})

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        log_pipeline_event(logger, "pipeline_complete", {"status": "failed", "error": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()