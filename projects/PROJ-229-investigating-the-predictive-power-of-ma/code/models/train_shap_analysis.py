"""
Train a model (or load an existing baseline model) and compute SHAP values
for the processed feature set. The resulting summary is written to
`data/models/shap_summary.json`.

This script is intended to be run as part of the US2 pipeline after the
descriptor computation step (T012) and baseline model training (T017a/b).
It relies on real processed data; if the expected file is missing the script
will raise an informative error.
"""

import json
import logging
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestRegressor

# Project utilities
from utils.logger import get_pipeline_logger, log_error, log_info

# Configuration helper (optional – can be extended later)
try:
    from config import get_config
except Exception:  # pragma: no cover
    # If config utilities are not available, fall back to defaults.
    def get_config():
        return {}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_processed_data(csv_path: Path) -> pd.DataFrame:
    """
    Load the processed feature matrix. The CSV is expected to contain all
    feature columns and a single target column named ``target`` (or the
    last column if ``target`` is absent).

    Parameters
    ----------
    csv_path: Path
        Path to the processed CSV file.

    Returns
    -------
    pd.DataFrame
        Dataframe with features and target.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Processed data file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"Processed data file is empty: {csv_path}")

    return df

def separate_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Split a DataFrame into features (X) and target (y). The function looks
    for a column named ``target``; if not present it assumes the last column
    is the target.

    Returns
    -------
    X, y
    """
    if "target" in df.columns:
        target_col = "target"
    else:
        target_col = df.columns[-1]

    X = df.drop(columns=[target_col])
    y = df[target_col]

    return X, y

def load_or_train_model(X: pd.DataFrame, y: pd.Series, model_path: Path) -> object:
    """
    Load a pre‑trained model from ``model_path`` if it exists; otherwise,
    train a quick RandomForestRegressor and persist it.

    Parameters
    ----------
    X, y : training data
    model_path : where the model should be stored/loaded from

    Returns
    -------
    model object
    """
    if model_path.is_file():
        log_info(f"Loading existing model from {model_path}")
        model = joblib.load(model_path)
    else:
        log_info("Training a new RandomForestRegressor for SHAP analysis")
        model = RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X, y)
        # Persist the model for downstream use
        joblib.dump(model, model_path)
        log_info(f"Model saved to {model_path}")

    return model

def compute_shap_summary(model, X: pd.DataFrame) -> dict:
    """
    Compute mean absolute SHAP values for each feature.

    Returns a dictionary:
        {
            "features": [list of feature names],
            "mean_abs_shap": [list of float values]
        }
    """
    # TreeExplainer works with many tree‑based models (RF, GB, etc.)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # For regression models shap_values is a 2‑D array (samples, features)
    if isinstance(shap_values, list):
        # Some models return a list with a single element
        shap_values = shap_values[0]

    mean_abs = np.mean(np.abs(shap_values), axis=0)
    summary = {
        "features": list(X.columns),
        "mean_abs_shap": mean_abs.tolist(),
    }
    return summary

def write_shap_summary(summary: dict, out_path: Path):
    """
    Write the SHAP summary dictionary to a JSON file.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2)
    log_info(f"SHAP summary written to {out_path}")

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """
    Execute the SHAP analysis pipeline.
    """
    logger = get_pipeline_logger(__name__)

    try:
        # Resolve paths relative to the project root
        project_root = Path(__file__).resolve().parents[2]  # code/models/..
        processed_csv = project_root / "data" / "processed" / "processed_data.csv"
        model_path = project_root / "data" / "models" / "rf_model.pkl"
        shap_output = project_root / "data" / "models" / "shap_summary.json"

        # Load data
        df = load_processed_data(processed_csv)
        X, y = separate_features_target(df)

        # Load (or train) a model
        model = load_or_train_model(X, y, model_path)

        # Compute SHAP values
        summary = compute_shap_summary(model, X)

        # Persist summary
        write_shap_summary(summary, shap_output)

    except Exception as exc:  # pragma: no cover
        log_error(f"SHAP analysis failed: {exc}")
        raise

if __name__ == "__main__":
    main()
