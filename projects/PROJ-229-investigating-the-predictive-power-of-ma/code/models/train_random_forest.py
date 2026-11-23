"""
Train a Random Forest regressor on the processed dataset.

The script expects the following files to exist:
  - ``data/processed/graph_features.npy``   – NumPy array of shape (n_samples, n_features)
  - ``data/processed/targets.npy``          – NumPy array of shape (n_samples,)

It will:
  1. Load the feature matrix and target vector.
  2. Split the data into a training and validation set (80/20).
  3. Train ``sklearn.ensemble.RandomForestRegressor`` on the training set.
  4. Compute the R² score on the validation set.
  5. Log the R² score and the total execution time.
  6. Fail loudly if execution time exceeds 2 hours or if R² ≤ 0.0.
  7. Persist the fitted model to ``data/models/rf_model.pkl`` using ``joblib``.

The script can be run directly:
    ``python code/models/train_random_forest.py``
or imported and called via ``train_random_forest()``.
"""

import os
import time
from pathlib import Path
import logging

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import joblib

# Project‑wide logger utilities
from utils.logger import get_pipeline_logger, log_info, log_error

# Constants
FEATURES_PATH = Path("data/processed/graph_features.npy")
TARGETS_PATH = Path("data/processed/targets.npy")
MODEL_OUTPUT_PATH = Path("data/models/rf_model.pkl")
MAX_TIME_SECONDS = 2 * 60 * 60  # 2 hours


def _load_data() -> tuple[np.ndarray, np.ndarray]:
    """Load feature matrix and target vector from the expected locations.

    Returns
    -------
    X : np.ndarray
        Feature matrix of shape (n_samples, n_features).
    y : np.ndarray
        Target vector of shape (n_samples,).

    Raises
    ------
    FileNotFoundError
        If either the feature or target file does not exist.
    """
    if not FEATURES_PATH.is_file():
        raise FileNotFoundError(f"Feature file not found: {FEATURES_PATH}")
    if not TARGETS_PATH.is_file():
        raise FileNotFoundError(f"Target file not found: {TARGETS_PATH}")

    X = np.load(FEATURES_PATH)
    y = np.load(TARGETS_PATH)

    if X.shape[0] != y.shape[0]:
        raise ValueError(
            f"Feature/target sample mismatch: {X.shape[0]} vs {y.shape[0]}"
        )
    return X, y


def train_random_forest(
    n_estimators: int = 200,
    max_depth: int | None = None,
    random_state: int = 42,
    test_size: float = 0.2,
) -> tuple[RandomForestRegressor, float, float]:
    """Train a RandomForestRegressor and return model, R² and elapsed time.

    Parameters
    ----------
    n_estimators : int, optional
        Number of trees in the forest. Default is 200.
    max_depth : int | None, optional
        Maximum depth of each tree. ``None`` means unlimited depth.
    random_state : int, optional
        Seed for reproducibility.
    test_size : float, optional
        Fraction of data to hold out for validation.

    Returns
    -------
    model : RandomForestRegressor
        The fitted model.
    r2 : float
        R² score on the validation set.
    elapsed_seconds : float
        Total training time in seconds.
    """
    logger = get_pipeline_logger(__name__)
    start = time.time()
    logger.info("Loading processed data for Random Forest training.")
    X, y = _load_data()

    logger.info(
        "Splitting data into train/validation (test_size=%.2f).", test_size
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    logger.info(
        "Training RandomForestRegressor (n_estimators=%d, max_depth=%s).",
        n_estimators,
        str(max_depth),
    )
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    logger.info("Predicting on validation set.")
    y_pred = model.predict(X_val)
    r2 = r2_score(y_val, y_pred)

    elapsed = time.time() - start
    logger.info(
        "Random Forest training completed in %.2f seconds. Validation R² = %.4f",
        elapsed,
        r2,
    )
    return model, r2, elapsed


def _ensure_output_dir(path: Path) -> None:
    """Make sure the parent directory for *path* exists."""
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Entry point for script execution."""
    logger = get_pipeline_logger(__name__)

    try:
        model, r2, elapsed = train_random_forest()
    except Exception as exc:
        log_error("Random Forest training failed.", exc_info=exc)
        raise

    # Enforce runtime constraint
    if elapsed > MAX_TIME_SECONDS:
        msg = (
            f"Training exceeded time limit of {MAX_TIME_SECONDS/3600:.1f} h "
            f"({elapsed/3600:.2f} h)."
        )
        log_error(msg)
        raise RuntimeError(msg)

    # Enforce performance constraint
    if r2 <= 0.0:
        msg = f"Model R² not positive (R²={r2:.4f}); training considered a failure."
        log_error(msg)
        raise RuntimeError(msg)

    # Persist the model
    _ensure_output_dir(MODEL_OUTPUT_PATH)
    joblib.dump(model, MODEL_OUTPUT_PATH)
    log_info(f"Random Forest model saved to {MODEL_OUTPUT_PATH}")

    # Log final summary
    log_info(
        "Random Forest training succeeded. R²=%.4f, elapsed=%.2f s",
        r2,
        elapsed,
    )


if __name__ == "__main__":
    main()