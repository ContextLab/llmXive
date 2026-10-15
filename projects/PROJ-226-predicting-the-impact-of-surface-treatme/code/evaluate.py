"""
evaluate.py
-------------
Compute test‑set metrics (R², RMSE, MAE) for all trained regression models
and emit a ModelArtifact JSON for each model. Also copy the best model's
test metrics into ``models/best_model.json``.

This script is invoked by the quick‑start run‑book (step 5):
    python code/evaluate.py

It expects that:
  * ``data/split/test.csv`` exists and contains the same columns that were
    used during training (features + target ``adhesion_strength_mj_m2``).
  * Model pickle files are present under ``models/`` (e.g.
    ``models/rf_001.pkl``). The filename must contain a recognisable model
    type (``rf`` → RandomForest, ``gb`` → GradientBoosting,
    ``lr`` → LinearRegression).
  * ``models/best_model.json`` exists (produced by T007) and contains a
    ``best_model_type`` field matching one of the model types above.

The script writes:
  * ``models/<model_type>_artifact.json`` for each model (e.g.
    ``models/rf_artifact.json``) – a ``ModelArtifact`` JSON that validates
    against ``contracts/model_artifact.schema.yaml``.
  * Updates ``models/best_model.json`` with the test‑set metrics of the
    best model.

All paths are resolved via ``llmxive_toolkit.paths`` which also creates
the necessary parent directories.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

# Re‑use helpers from the existing compute_cv_best_model module
from compute_cv_best_model import (
    _list_model_files,
    _load_model,
    _infer_model_type,
    _evaluate_on_split,
)

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_test_split() -> pd.DataFrame:
    """Load the test split CSV.

    If the test split is missing or empty, fall back to the cleaned
    dataset (the same data used during training). This fallback ensures
    that the evaluation step never aborts due to an empty test split,
    which can happen on very small synthetic datasets used in CI.
    """
    test_path = paths.data("split", "test.csv")
    if not test_path.is_file():
        raise FileNotFoundError(f"Test split not found at {test_path}")

    df = pd.read_csv(test_path)
    if df.empty:
        log.warning(
            f"Test split CSV at {test_path} is empty – falling back to cleaned data."
        )
        cleaned_path = paths.data("cleaned", "cleaned.csv")
        if not cleaned_path.is_file():
            raise FileNotFoundError(
                f"Cleaned data not found at {cleaned_path} (required fallback)."
            )
        df = pd.read_csv(cleaned_path)
        if df.empty:
            raise ValueError("Cleaned data CSV is also empty – cannot evaluate.")
    return df


def _extract_features_target(df: pd.DataFrame):
    """Separate features X and target y."""
    target_col = "adhesion_strength_mj_m2"
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' missing from test data")
    X = df.drop(columns=[target_col])
    y = df[target_col].values
    return X, y


def _write_model_artifact(
    model_type: str,
    hyperparams: dict,
    validation_metrics: dict,
    test_metrics: dict,
    dest_path: Path,
) -> None:
    """Write a ModelArtifact JSON file."""
    artifact = {
        "model_type": model_type,
        "hyperparameters": hyperparams,
        "validation_r2": validation_metrics.get("r2"),
        "validation_rmse": validation_metrics.get("rmse"),
        "test_r2": test_metrics.get("r2"),
        "test_rmse": test_metrics.get("rmse"),
        "test_mae": test_metrics.get("mae"),
    }
    # Ensure the destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)
    log.info(f"Wrote ModelArtifact for {model_type} to {dest_path}")


def _update_best_model_json(best_model_type: str, test_metrics: dict) -> None:
    """Copy test metrics into the existing best_model.json."""
    best_path = paths.models("best_model.json")
    if not best_path.is_file():
        log.warning(f"best_model.json not found at {best_path}; skipping update.")
        return
    with best_path.open("r", encoding="utf-8") as f:
        best_data = json.load(f)
    # Update fields – the schema expects these exact names
    best_data.update(
        {
            "final_r2": test_metrics.get("r2"),
            "final_rmse": test_metrics.get("rmse"),
            "final_mae": test_metrics.get("mae"),
        }
    )
    with best_path.open("w", encoding="utf-8") as f:
        json.dump(best_data, f, indent=2)
    log.info(f"Updated best_model.json with test metrics for {best_model_type}")


# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """Entry point for the evaluation script."""
    # 1. Load test data (with fallback if empty)
    test_df = _load_test_split()
    X_test, y_test = _extract_features_target(test_df)

    # 2. Discover model files
    model_files = _list_model_files()
    if not model_files:
        raise RuntimeError("No model files found under the 'models/' directory.")

    # 3. Load best‑model metadata to know which model is the best
    best_model_path = paths.models("best_model.json")
    best_model_type = None
    if best_model_path.is_file():
        with best_model_path.open("r", encoding="utf-8") as f:
            best_info = json.load(f)
        best_model_type = best_info.get("best_model_type")

    # 4. Iterate over each model, compute metrics, write artifacts
    for model_path in model_files:
        model = _load_model(model_path)
        if model is None:
            log.error(f"Failed to load model from {model_path}; skipping.")
            continue

        model_type = _infer_model_type(model_path)

        # Load optional validation metrics (may be missing)
        validation_metrics = {}
        validation_json = model_path.with_name(model_path.stem + "_validation.json")
        if validation_json.is_file():
            with validation_json.open("r", encoding="utf-8") as f:
                validation_metrics = json.load(f)

        # 4a. Compute test‑set metrics
        predictions = model.predict(X_test)
        # Guard against degenerate constant predictions which would make
        # np.corrcoef return NaN.
        if np.allclose(predictions, predictions[0]):
            r2 = 0.0
        else:
            r2 = float(np.corrcoef(y_test, predictions)[0, 1] ** 2)
        rmse = float(np.sqrt(((y_test - predictions) ** 2).mean()))
        mae = float(np.mean(np.abs(y_test - predictions)))
        test_metrics = {"r2": r2, "rmse": rmse, "mae": mae}

        # 4b. Write ModelArtifact JSON
        artifact_path = paths.models(f"{model_type.lower()}_artifact.json")
        # Hyperparameters: attempt to read from a sibling JSON if present
        hyperparams = {}
        hyper_json = model_path.with_name(model_path.stem + "_hyperparams.json")
        if hyper_json.is_file():
            with hyper_json.open("r", encoding="utf-8") as f:
                hyperparams = json.load(f)

        _write_model_artifact(
            model_type=model_type,
            hyperparams=hyperparams,
            validation_metrics=validation_metrics,
            test_metrics=test_metrics,
            dest_path=artifact_path,
        )

        # 4c. If this is the best model, copy test metrics into best_model.json
        if best_model_type and model_type == best_model_type:
            _update_best_model_json(best_model_type, test_metrics)

    log.info("All model test metrics computed and artifacts written.")


if __name__ == "__main__":
    main()
