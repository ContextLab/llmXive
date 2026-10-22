"""
src/models/evaluate.py
-----------------------

This module evaluates the selected model on a held‑out test set.  The original
implementation expected exactly two command‑line arguments (the full feature
matrix CSV and the output JSON path).  The pipeline, however, passed three
arguments (train CSV, test CSV, and the performance JSON), causing a
``RuntimeError`` during execution.

The module now supports both calling conventions:

* **CLI style** – ``python -m src.models.evaluate <train.csv> <test.csv>
  <performance.json>`` (the three‑argument form used by the pipeline).
* **Programmatic style** – ``main(train_path=Path(...), test_path=Path(...),
  performance_path=Path(...))``.

The function loads the previously trained models (``rf_cv.pkl`` and
``gb_cv.pkl``), selects the best one based on mean CV RMSE, predicts on the
test set, computes performance metrics, writes a JSON performance file,
and creates a scatter‑plot of predictions vs. actual values.
"""

import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_cv_metrics(cv_path: Path) -> dict:
    """Load the CV metrics JSON file."""
    with cv_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _select_best_model(cv_metrics: dict) -> str:
    """Select the model name with the lowest mean RMSE."""
    best = None
    best_rmse = float("inf")
    for name, data in cv_metrics.items():
        rmse = data["aggregate"]["mean_rmse"]
        if rmse < best_rmse:
            best_rmse = rmse
            best = name
    if best is None:
        raise RuntimeError("No model information found in CV metrics.")
    return best


def _model_path_for_name(model_name: str) -> Path:
    """Map a model name to its pickle file."""
    mapping = {
        "RandomForest": paths.path("models", "rf_cv.pkl"),
        "GradientBoosting": paths.path("models", "gb_cv.pkl"),
    }
    try:
        return mapping[model_name]
    except KeyError as exc:
        raise RuntimeError(f"Unknown model name '{model_name}'.") from exc


def _load_model(model_path: Path):
    """Load a scikit‑learn model from a pickle file."""
    if not model_path.is_file():
        raise RuntimeError(f"Model file not found: {model_path}")
    return joblib.load(model_path)


def _prepare_test_data(test_path: Path, target_col: str = "formation_energy"):
    """Load the test CSV, separate features from the target."""
    df = pd.read_csv(test_path)
    if target_col not in df.columns:
        raise RuntimeError(f"Target column '{target_col}' missing from test data.")
    X_test = df.drop(columns=[target_col, "composition"])
    y_test = df[target_col].values
    return X_test, y_test


def _bootstrap_rmse_ci(
    y_true: np.ndarray, y_pred: np.ndarray, n_boot: int = 10000, ci: float = 0.95
) -> tuple:
    """Bootstrap a confidence interval for RMSE."""
    rng = np.random.default_rng(42)
    rmses = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y_true), len(y_true))
        rmse = mean_squared_error(y_true[idx], y_pred[idx], squared=False)
        rmses.append(rmse)
    lower = np.percentile(rmses, (1 - ci) / 2 * 100)
    upper = np.percentile(rmses, (1 + ci) / 2 * 100)
    return float(lower), float(upper)


def _paired_t_test(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Perform a paired two‑sided t‑test."""
    from scipy.stats import ttest_rel

    t_stat, p_val = ttest_rel(y_true, y_pred)
    return float(p_val)


def _save_performance_json(
    out_path: Path,
    model_name: str,
    rmse: float,
    mae: float,
    r2: float,
    rmse_ci: tuple,
    p_value: float,
) -> None:
    """Write the performance dictionary to ``out_path``."""
    perf = {
        "model": model_name,
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "rmse_ci": {"lower": rmse_ci[0], "upper": rmse_ci[1]},
        "p_value": p_value,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(perf, f, indent=2)
    log.info(f"Performance written to {out_path}")


def _plot_predictions(
    y_true: np.ndarray, y_pred: np.ndarray, out_path: Path
) -> None:
    """Scatter plot of predicted vs. actual values with a 1:1 line."""
    plt.figure(figsize=(6, 6))
    plt.scatter(y_true, y_pred, alpha=0.6, edgecolor="k")
    max_val = max(y_true.max(), y_pred.max())
    min_val = min(y_true.min(), y_pred.min())
    plt.plot([min_val, max_val], [min_val, max_val], "r--", lw=2)
    plt.xlabel("DFT formation energy (eV)")
    plt.ylabel("Predicted formation energy (eV)")
    plt.title("Predicted vs. Actual Defect Formation Energies")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path)
    plt.close()
    log.info(f"Prediction scatter plot saved to {out_path}")


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------
def main(*args, **kwargs) -> None:
    """
    Entry point for model evaluation.

    Supports two calling conventions:

    * **CLI (three‑argument)** – ``python -m src.models.evaluate <train.csv>
      <test.csv> <performance.json>`` (the form used by the pipeline).

    * **Programmatic** – ``main(train_path=Path(...), test_path=Path(...),
      performance_path=Path(...))``.
    """
    if args and kwargs:
        raise RuntimeError(
            "Provide either positional arguments *or* keyword arguments, not both."
        )

    # CLI style (three arguments)
    if args:
        if len(args) != 3:
            raise RuntimeError(
                "Usage: python -m src.models.evaluate <train.csv> <test.csv> <performance.json>"
            )
        train_path = Path(args[0])
        test_path = Path(args[1])
        performance_path = Path(args[2])
    else:
        # Programmatic style
        try:
            train_path = kwargs["train_path"]
            test_path = kwargs["test_path"]
            performance_path = kwargs["performance_path"]
        except KeyError as exc:
            raise RuntimeError(
                "Programmatic call requires 'train_path', 'test_path', and 'performance_path' keyword arguments."
            ) from exc

    # Load CV metrics to decide which model to use.
    cv_path = paths.data("processed", "cv_metrics.json")
    cv_metrics = _load_cv_metrics(cv_path)
    best_model_name = _select_best_model(cv_metrics)
    model_path = _model_path_for_name(best_model_name)
    model = _load_model(model_path)

    # Prepare test data
    X_test, y_test = _prepare_test_data(test_path)

    # Predict and compute metrics
    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Bootstrap CI and paired t‑test
    rmse_ci = _bootstrap_rmse_ci(y_test, y_pred)
    p_val = _paired_t_test(y_test, y_pred)

    # Save performance JSON
    _save_performance_json(
        performance_path,
        best_model_name,
        rmse,
        mae,
        r2,
        rmse_ci,
        p_val,
    )

    # Plot predictions
    plot_path = paths.figures("pred_vs_actual.png")
    _plot_predictions(y_test, y_pred, plot_path)


if __name__ == "__main__":
    # Forward CLI arguments (excluding the script name) to ``main``.
    main(*sys.argv[1:])
