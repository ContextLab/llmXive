"""
Random Forest Regressor implementation for molecular permeability prediction.

This module provides the Random Forest baseline model as specified in the
project requirements. It trains on the full descriptor vector
(MW, logP, TPSA, HBA, HBD, rotatable bonds) with the required hyper‑parameters,
saves the trained model to ``code/models/rf.pkl`` and offers helper functions
for prediction and evaluation.
"""
import logging
from pathlib import Path
from typing import Union, Tuple, Dict, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Configure module logger
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Core training function
# ----------------------------------------------------------------------
def train_random_forest(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    n_estimators: int = 200,
    max_features: Union[int, str] = "sqrt",
    random_state: int = 42,
) -> RandomForestRegressor:
    """
    Train a RandomForestRegressor on the provided descriptor matrix.

    Parameters
    ----------
    X : np.ndarray or pd.DataFrame
        Feature matrix containing exactly the six descriptor columns:
        ``mw``, ``logp``, ``tpsa``, ``hba``, ``hbd``, ``rotatable_bonds``.
    y : np.ndarray or pd.Series
        Target vector (permeability coefficient).
    n_estimators : int, optional
        Number of trees in the forest (default 200 as required by FR‑005).
    max_features : int or str, optional
        Number of features to consider at each split. ``'sqrt'`` is the
        required setting for FR‑005.
    random_state : int, optional
        Seed for reproducibility.

    Returns
    -------
    RandomForestRegressor
        The fitted Random Forest model.
    """
    logger.info(
        f"Training Random Forest: n_estimators={n_estimators}, max_features={max_features}"
    )

    # Convert pandas objects to numpy arrays if necessary
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, pd.Series):
        y = y.values

    if X.shape[0] != y.shape[0]:
        raise ValueError(
            f"Shape mismatch: X has {X.shape[0]} rows but y has {y.shape[0]} entries."
        )
    if X.shape[0] == 0:
        raise ValueError("Empty training data supplied to Random Forest.")

    # Instantiate and fit the model
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_features=max_features,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X, y)

    logger.info(
        f"Random Forest training complete. Feature importances shape: {model.feature_importances_.shape}"
    )
    return model

# ----------------------------------------------------------------------
# Prediction helper
# ----------------------------------------------------------------------
def predict(
    model: RandomForestRegressor,
    X: Union[np.ndarray, pd.DataFrame],
) -> np.ndarray:
    """
    Generate predictions using a trained Random Forest model.

    Parameters
    ----------
    model : RandomForestRegressor
        Trained model.
    X : np.ndarray or pd.DataFrame
        Feature matrix.

    Returns
    -------
    np.ndarray
        Predicted target values.
    """
    if isinstance(X, pd.DataFrame):
        X = X.values
    return model.predict(X)

# ----------------------------------------------------------------------
# Evaluation helper
# ----------------------------------------------------------------------
def evaluate_model(
    model: RandomForestRegressor,
    X_test: Union[np.ndarray, pd.DataFrame],
    y_test: Union[np.ndarray, pd.Series],
) -> Dict[str, float]:
    """
    Compute regression metrics for a Random Forest model.

    Returns a dictionary with ``rmse``, ``mae`` and ``r2``.
    """
    y_pred = predict(model, X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))
    logger.info(
        f"Evaluation metrics – RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}"
    )
    return {"rmse": rmse, "mae": mae, "r2": r2}

# ----------------------------------------------------------------------
# CLI entry point – trains on the project’s processed data
# ----------------------------------------------------------------------
def main() -> None:
    """
    Command‑line interface for training the Random Forest baseline.

    The script:
    1. Loads ``data/processed/train.csv``.
    2. Selects the six required descriptor columns.
    3. Trains the Random Forest with the prescribed hyper‑parameters.
    4. Saves the model to ``code/models/rf.pkl``.
    5. Logs basic training information.
    """
    import sys
    import yaml
    from llmxive_toolkit import paths, get_logger

    # Initialise a project‑wide logger
    log = get_logger(__name__, log_file=str(paths.results("logs", "rf_training.log")))
    log.setLevel(logging.INFO)

    # Resolve paths
    project_root = Path(__file__).parents[2]  # <project>/code/models/..
    train_path = project_root / "data" / "processed" / "train.csv"
    model_path = project_root / "code" / "models" / "rf.pkl"

    if not train_path.is_file():
        log.error(f"Training data not found at {train_path}.")
        sys.exit(1)

    # Load training data
    df = pd.read_csv(train_path)
    log.info(f"Loaded training data with {len(df)} rows and {len(df.columns)} columns.")

    # Expected descriptor columns (lower‑case as written by preprocess)
    descriptor_cols = [
        "mw",
        "logp",
        "tpsa",
        "hba",
        "hbd",
        "rotatable_bonds",
    ]

    missing = [c for c in descriptor_cols if c not in df.columns]
    if missing:
        log.error(f"Missing required descriptor columns: {missing}")
        sys.exit(1)

    X = df[descriptor_cols]
    # Identify target column – the preprocessing step stores the experimental
    # permeability under the generic name ``target``.
    if "target" not in df.columns:
        log.error("Target column 'target' not found in training data.")
        sys.exit(1)

    y = df["target"]

    # Train model
    model = train_random_forest(X, y)

    # Verify that the model has exactly six importances (one per descriptor)
    if model.feature_importances_.shape[0] != len(descriptor_cols):
        log.warning(
            f"Unexpected number of feature importances: "
            f"{model.feature_importances_.shape[0]} (expected {len(descriptor_cols)})"
        )

    # Save the model
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    log.info(f"Random Forest model saved to {model_path}")

    # Optional: write a tiny JSON summary for downstream steps
    summary_path = project_root / "results" / "rf_training_summary.json"
    summary = {
        "model_path": str(model_path),
        "descriptor_columns": descriptor_cols,
        "n_estimators": 200,
        "max_features": "sqrt",
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(summary, f)
    log.info(f"Training summary written to {summary_path}")

if __name__ == "__main__":
    main()