"""
Train a Gradient Boosting Regressor on the processed materials dataset.

This script follows the same constraints as the Random Forest baseline
(task T017a):
  * Execution time must be ≤ 2 hours.
  * The test‑set R² score must be > 0.0.
If either constraint is violated a ``ModelTrainingError`` is raised.
The trained model is persisted as ``data/models/gb_model.pkl``.
"""

import json
import logging
import os
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

# Project‑specific utilities
from utils.logger import get_pipeline_logger, log_info, log_error, log_warning
from utils.error_handling import ModelTrainingError

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_target_column() -> str:
    """
    Load the target column name from ``data/results/target_decision.json``.
    The JSON file is expected to contain a key ``target`` or ``target_column``.
    """
    target_path = Path("data/results/target_decision.json")
    if not target_path.is_file():
        raise FileNotFoundError(f"Target decision file not found: {target_path}")

    with target_path.open("r", encoding="utf-8") as fp:
        decision = json.load(fp)

    # Accept either naming convention
    target = decision.get("target") or decision.get("target_column")
    if not target:
        raise KeyError(
            "Target column name not found in target decision JSON (expected "
            "'target' or 'target_column')."
        )
    return target


def _load_processed_dataset() -> pd.DataFrame:
    """
    Load the processed dataset CSV from ``data/processed``.
    The first CSV file encountered is used.  An explicit error is raised
    if no CSV is present.
    """
    processed_dir = Path("data/processed")
    if not processed_dir.is_dir():
        raise FileNotFoundError(f"Processed data directory missing: {processed_dir}")

    csv_files = list(processed_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in processed data directory: {processed_dir}"
        )

    # Use the first CSV file (project conventions ensure there is only one)
    dataset_path = csv_files[0]
    return pd.read_csv(dataset_path)


def _prepare_features_and_target(
    df: pd.DataFrame, target_column: str
) -> tuple[np.ndarray, np.ndarray]:
    """
    Split the DataFrame into feature matrix ``X`` and target vector ``y``.
    All columns except the target are used as features.  Non‑numeric columns
    are dropped to avoid model errors.
    """
    if target_column not in df.columns:
        raise KeyError(
            f"Target column '{target_column}' not found in processed dataset."
        )

    y = df[target_column].values
    X = df.drop(columns=[target_column])

    # Keep only numeric columns (GradientBoostingRegressor requires numeric input)
    numeric_X = X.select_dtypes(include=[np.number])
    if numeric_X.empty:
        raise ValueError("No numeric feature columns available for training.")

    return numeric_X.values, y


# ----------------------------------------------------------------------
# Core training routine
# ----------------------------------------------------------------------


def train_gradient_boosting(random_state: int = 42) -> Path:
    """
    Train a GradientBoostingRegressor and persist the model.

    Parameters
    ----------
    random_state : int, optional
        Seed for reproducibility of the train‑test split.

    Returns
    -------
    Path
        Path to the saved model file (``data/models/gb_model.pkl``).

    Raises
    ------
    ModelTrainingError
        If execution time exceeds 2 hours or R² ≤ 0.0.
    """
    logger = get_pipeline_logger(__name__)
    start_time = time.time()
    logger.info("Starting Gradient Boosting training pipeline.")

    # ------------------------------------------------------------------
    # Load data and target
    # ------------------------------------------------------------------
    try:
        target_col = _load_target_column()
        logger.debug(f"Target column identified as '{target_col}'.")
        df = _load_processed_dataset()
        logger.debug(f"Processed dataset loaded with shape {df.shape}.")
        X, y = _prepare_features_and_target(df, target_col)
    except Exception as exc:
        logger.exception("Failed to load or prepare data.")
        raise ModelTrainingError("Data loading/preparation failed.") from exc

    # ------------------------------------------------------------------
    # Train / test split
    # ------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    logger.info(
        f"Data split: {X_train.shape[0]} train samples, {X_test.shape[0]} test samples."
    )

    # ------------------------------------------------------------------
    # Model training
    # ------------------------------------------------------------------
    model = GradientBoostingRegressor(random_state=random_state)

    try:
        model.fit(X_train, y_train)
    except Exception as exc:
        logger.exception("Model fitting failed.")
        raise ModelTrainingError("Gradient Boosting model training failed.") from exc

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    elapsed = time.time() - start_time

    logger.info(f"Gradient Boosting R² on test set: {r2:.4f}")
    logger.info(f"Training elapsed time: {elapsed:.2f} seconds")

    # ------------------------------------------------------------------
    # Constraint checks
    # ------------------------------------------------------------------
    max_seconds = 2 * 60 * 60  # 2 hours
    if elapsed > max_seconds:
        msg = f"Training exceeded time limit of 2 h ({elapsed:.2f} s)."
        logger.error(msg)
        raise ModelTrainingError(msg)

    if r2 <= 0.0:
        msg = f"Model R² ({r2:.4f}) not greater than 0.0."
        logger.error(msg)
        raise ModelTrainingError(msg)

    # ------------------------------------------------------------------
    # Persist model
    # ------------------------------------------------------------------
    model_dir = Path("data/models")
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "gb_model.pkl"
    joblib.dump(model, model_path)
    logger.info(f"Gradient Boosting model saved to {model_path}")

    return model_path


def main() -> None:
    """
    Entry‑point for ``python -m code.models.train_gradient_boosting``.
    """
    try:
        train_gradient_boosting()
    except ModelTrainingError as e:
        log_error(str(e))
        raise
    except Exception as e:
        # Unexpected failures are also logged
        log_error(f"Unexpected error during Gradient Boosting training: {e}")
        raise


if __name__ == "__main__":
    main()