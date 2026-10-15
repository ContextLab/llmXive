"""
compute_cv_best_model.py

This script implements Task T007: it computes k‑fold cross‑validated R² for each
trained model, selects the best model (highest mean CV R²), and writes a JSON
summary ``models/best_model.json`` containing:

  * best_model_type – string identifier (e.g., "RandomForest")
  * hyperparameters   – the model's ``get_params()`` dictionary
  * validation_r2     – R² on the validation split (if available)
  * validation_rmse   – RMSE on the validation split (if available)
  * cv_r2_mean        – mean CV R² across folds
  * cv_r2_std         – standard deviation of CV R² across folds
  * null_result       – true when ``cv_r2_mean`` < 0.5 or when no data is
                        available for a meaningful evaluation
  * timestamp         – ISO‑8601 timestamp of when the file was created

The script is deliberately defensive: if any required artifact (cleaned data,
model files, or validation split) is missing or empty, it still produces a
``best_model.json`` that satisfies the schema required by downstream tasks.
"""

import json
import pathlib
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold

# The project provides helper ``paths`` to locate files inside the repo.
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_cleaned_dataframe() -> pd.DataFrame:
    """Load the unified cleaned data set."""
    cleaned_path = paths.data("cleaned", "cleaned.csv")
    if not cleaned_path.is_file():
        log.error(f"Cleaned data not found at {cleaned_path}")
        return pd.DataFrame()
    df = pd.read_csv(cleaned_path)
    log.info(f"Loaded cleaned data with shape {df.shape}")
    return df

def _load_split(split_name: str) -> pd.DataFrame:
    """Load a CSV split (train / val / test). Returns empty DataFrame if missing."""
    split_path = paths.data("split", f"{split_name}.csv")
    if not split_path.is_file():
        log.warning(f"{split_name} split not found at {split_path}")
        return pd.DataFrame()
    df = pd.read_csv(split_path)
    log.info(f"Loaded {split_name} split with shape {df.shape}")
    return df

def _list_model_files() -> list[pathlib.Path]:
    """Return a list of all model pickle files under ``models/``."""
    model_dir = paths.models()
    if not model_dir.is_dir():
        log.warning(f"Model directory {model_dir} does not exist")
        return []
    model_files = list(model_dir.glob("*.pkl"))
    log.info(f"Discovered {len(model_files)} model file(s)")
    return model_files

def _load_model(model_path: pathlib.Path):
    """Load a scikit‑learn model from a pickle file."""
    try:
        import joblib
    except Exception as exc:
        log.error("joblib is required to load model files")
        raise exc
    try:
        model = joblib.load(model_path)
        log.info(f"Loaded model from {model_path.name}")
        return model
    except Exception as exc:
        log.error(f"Failed to load model {model_path}: {exc}")
        return None

def _infer_model_type(model_path: pathlib.Path) -> str:
    """Infer a human‑readable model type from the filename."""
    name = model_path.stem.lower()
    if "rf" in name or "randomforest" in name:
        return "RandomForest"
    if "gb" in name or "gradientboost" in name:
        return "GradientBoosting"
    if "lr" in name or "linearregression" in name:
        return "LinearRegression"
    # Fallback – use the class name of the loaded model if possible
    model = _load_model(model_path)
    if model is not None:
        return model.__class__.__name__
    return "UnknownModel"

def _evaluate_on_split(model, X, y) -> dict:
    """Return R² and RMSE for the supplied features/target."""
    if X.empty or y.empty:
        return {"r2": None, "rmse": None}
    try:
        preds = model.predict(X)
    except Exception as exc:
        log.error(f"Prediction failed: {exc}")
        return {"r2": None, "rmse": None}
    r2 = r2_score(y, preds)
    rmse = np.sqrt(mean_squared_error(y, preds))
    return {"r2": r2, "rmse": rmse}

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    # Load the full cleaned dataset – this is the source for CV.
    df_clean = _load_cleaned_dataframe()
    if df_clean.empty:
        log.warning("Cleaned dataset is empty – proceeding with null result.")
    target_col = "adhesion_strength_mj_m2"
    feature_cols = [c for c in df_clean.columns if c != target_col]

    # Load validation split for validation metrics (if present)
    df_val = _load_split("val")
    val_metrics = {"r2": None, "rmse": None}
    if not df_val.empty:
        X_val = df_val[feature_cols]
        y_val = df_val[target_col]
        # Validation metrics will be computed later per model.

    # Discover trained model files.
    model_files = _list_model_files()
    if not model_files:
        log.error("No model files found – creating a default null result.")
    
    results = []

    for model_path in model_files:
        model = _load_model(model_path)
        if model is None:
            continue

        # ------------------------------------------------------------------
        # Cross‑validation on the *cleaned* data.
        # ------------------------------------------------------------------
        cv_r2_scores = []
        if not df_clean.empty and len(df_clean) >= 5:
            # Use KFold with 5 splits (deterministic seed)
            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            X = df_clean[feature_cols].values
            y = df_clean[target_col].values
            for train_idx, test_idx in kf.split(X):
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                # Fit a *fresh* copy of the model on the training fold.
                # Many scikit‑learn models support ``set_params`` + ``fit``.
                try:
                    # Clone to avoid contaminating the original trained model.
                    from sklearn.base import clone
                    model_clone = clone(model)
                    model_clone.fit(X_train, y_train)
                    preds = model_clone.predict(X_test)
                    cv_r2 = r2_score(y_test, preds)
                    cv_r2_scores.append(cv_r2)
                except Exception as exc:
                    log.error(f"CV fold failed for {model_path.name}: {exc}")
                    continue
        else:
            log.warning(
                f"Insufficient data for CV (rows={len(df_clean)}). "
                "Skipping CV for this model."
            )

        cv_mean = np.mean(cv_r2_scores) if cv_r2_scores else None
        cv_std = np.std(cv_r2_scores, ddof=1) if len(cv_r2_scores) > 1 else None

        # ------------------------------------------------------------------
        # Validation metrics (if validation split exists)
        # ------------------------------------------------------------------
        val_r2 = None
        val_rmse = None
        if not df_val.empty:
            X_val = df_val[feature_cols]
            y_val = df_val[target_col]
            val_metrics = _evaluate_on_split(model, X_val, y_val)
            val_r2 = val_metrics["r2"]
            val_rmse = val_metrics["rmse"]

        results.append(
            {
                "model_path": model_path,
                "model_type": _infer_model_type(model_path),
                "hyperparameters": model.get_params(),
                "cv_r2_mean": cv_mean,
                "cv_r2_std": cv_std,
                "validation_r2": val_r2,
                "validation_rmse": val_rmse,
            }
        )

    # ----------------------------------------------------------------------
    # Select the best model according to mean CV R².
    # ----------------------------------------------------------------------
    if results:
        # Prefer models with a defined mean CV R²; treat None as -inf.
        def _sort_key(item):
            return item["cv_r2_mean"] if item["cv_r2_mean"] is not None else -np.inf

        best = max(results, key=_sort_key)
    else:
        # No models – fabricate a minimal placeholder.
        best = {
            "model_path": None,
            "model_type": None,
            "hyperparameters": {},
            "cv_r2_mean": None,
            "cv_r2_std": None,
            "validation_r2": None,
            "validation_rmse": None,
        }

    # Determine the null_result flag.
    null_result = (
        best["cv_r2_mean"] is None or best["cv_r2_mean"] < 0.5
    )

    # ----------------------------------------------------------------------
    # Assemble the JSON payload.
    # ----------------------------------------------------------------------
    summary = {
        "best_model_type": best["model_type"],
        "hyperparameters": best["hyperparameters"],
        "validation_r2": best["validation_r2"],
        "validation_rmse": best["validation_rmse"],
        "cv_r2_mean": best["cv_r2_mean"],
        "cv_r2_std": best["cv_r2_std"],
        "null_result": null_result,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Write to ``models/best_model.json``.
    out_path = paths.models("best_model.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)

    log.info(f"Wrote best model summary to {out_path}")

if __name__ == "__main__":
    sys.exit(main())
