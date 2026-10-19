"""
src/models/evaluate.py
-----------------------

Evaluate the best performing model (selected from the cross‑validation
metrics) on the held‑out test set, compute performance statistics,
bootstrap a 95 % confidence interval for RMSE, perform a paired two‑sided
t‑test, and generate a scatter plot of predictions vs. actual values.

The script is intended to be executed via:

    python -m src.models.evaluate <features_csv> <performance_json>

where ``<features_csv>`` is the full feature matrix (including the target
column) and ``<performance_json>`` is the file that will receive the
evaluation results.  The test split is expected at
``data/processed/test.csv`` (produced by ``src.models.split``).  The
cross‑validation metrics are read from ``data/processed/cv_metrics.json``
(produced by ``src.models.train``) to decide which model (Random Forest
or Gradient Boosting) has the lowest mean RMSE and should be used for
evaluation.

The output JSON conforms to ``contracts/model_performance.schema.yaml``.
The scatter plot is saved as ``figures/pred_vs_actual.png``.
"""

import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_cv_metrics(cv_path: Path) -> dict:
    """
    Load the CV metrics JSON file.

    Expected format (example):
    {
        "RandomForest": {"mean_rmse": 0.42, "std_rmse": 0.05, ...},
        "GradientBoosting": {"mean_rmse": 0.48, "std_rmse": 0.06, ...}
    }
    """
    if not cv_path.is_file():
        raise FileNotFoundError(f"CV metrics file not found at {cv_path}")

    with cv_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("CV metrics JSON must be a dictionary mapping model names to metrics.")
    return data

def _select_best_model(cv_metrics: dict) -> str:
    """
    Select the model name with the lowest mean RMSE.
    Returns the key used in ``cv_metrics`` (e.g. ``RandomForest``).
    """
    best_name = None
    best_rmse = float("inf")
    for name, metrics in cv_metrics.items():
        mean_rmse = metrics.get("mean_rmse")
        if mean_rmse is None:
            raise KeyError(f"Model '{name}' entry missing 'mean_rmse'.")
        if mean_rmse < best_rmse:
            best_rmse = mean_rmse
            best_name = name
    if best_name is None:
        raise RuntimeError("Unable to determine the best model from CV metrics.")
    log.info(f"Best model according to CV: {best_name} (mean RMSE = {best_rmse:.4f})")
    return best_name

def _model_path_for_name(model_name: str) -> Path:
    """
    Map a model name (as used in CV metrics) to the corresponding
    pickle file on disk.
    """
    mapping = {
        "RandomForest": paths.path("models", "rf_cv.pkl"),
        "GradientBoosting": paths.path("models", "gb_cv.pkl"),
    }
    if model_name not in mapping:
        raise ValueError(f"Unrecognised model name '{model_name}'. Expected one of {list(mapping)}.")
    return mapping[model_name]

def _load_model(model_path: Path):
    """
    Load a scikit‑learn model from a pickle file.
    """
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    return joblib.load(model_path)

def _prepare_test_data(test_path: Path, target_col: str = "formation_energy"):
    """
    Load the test CSV, separate features from the target, and return
    ``X_test`` (DataFrame) and ``y_test`` (Series).
    """
    if not test_path.is_file():
        raise FileNotFoundError(f"Test split not found at {test_path}")
    df = pd.read_csv(test_path)
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' missing from test data.")
    y = df[target_col]
    X = df.drop(columns=[target_col])
    return X, y

def _bootstrap_rmse_ci(y_true: np.ndarray, y_pred: np.ndarray, n_boot: int = 10_000, ci: float = 0.95):
    """
    Compute a bootstrap confidence interval for RMSE.

    Returns a tuple ``(lower, upper)`` corresponding to the two‑sided
    ``ci`` interval.
    """
    rng = np.random.default_rng()
    rmses = np.empty(n_boot)
    n = len(y_true)
    for i in range(n_boot):
        indices = rng.integers(0, n, n)  # sample with replacement
        rmse = np.sqrt(mean_squared_error(y_true[indices], y_pred[indices]))
        rmses[i] = rmse
    lower = np.percentile(rmses, (1 - ci) / 2 * 100)
    upper = np.percentile(rmses, (1 + ci) / 2 * 100)
    return float(lower), float(upper)

def _paired_t_test(y_true: np.ndarray, y_pred: np.ndarray):
    """
    Perform a paired two‑sided t‑test between predictions and true values.
    Returns the p‑value.
    """
    t_stat, p_val = stats.ttest_rel(y_pred, y_true)
    return float(p_val)

def _save_performance_json(
    out_path: Path,
    model_name: str,
    rmse: float,
    mae: float,
    r2: float,
    rmse_ci: tuple,
    p_value: float,
):
    """
    Write the performance dictionary to ``out_path``.
    """
    performance = {
        "model": model_name,
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "rmse_ci_95": {"lower": rmse_ci[0], "upper": rmse_ci[1]},
        "p_value": p_value,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(performance, f, indent=2)
    log.info(f"Wrote performance summary to {out_path}")

def _plot_predictions(y_true: np.ndarray, y_pred: np.ndarray, out_path: Path):
    """
    Scatter plot of predicted vs. actual values with a 1:1 reference line.
    """
    plt.figure(figsize=(6, 6))
    plt.scatter(y_true, y_pred, alpha=0.7, edgecolor="k", linewidth=0.5)
    max_val = max(y_true.max(), y_pred.max())
    min_val = min(y_true.min(), y_pred.min())
    plt.plot([min_val, max_val], [min_val, max_val], "r--", label="1:1 line")
    plt.xlabel("DFT formation energy (eV)")
    plt.ylabel("Predicted formation energy (eV)")
    plt.title("Predicted vs. Actual Defect Formation Energies")
    plt.legend()
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()
    log.info(f"Saved prediction scatter plot to {out_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Expected positional arguments:
        1. Path to the full feature matrix CSV (used only to locate the
           target column name – defaults to ``formation_energy``).
        2. Path where the performance JSON should be written.
    """
    if len(sys.argv) != 3:
        sys.stderr.write(
            "Usage: python -m src.models.evaluate <features_csv> <performance_json>\\n"
        )
        sys.exit(1)

    features_csv = Path(sys.argv[1])
    performance_json = Path(sys.argv[2])

    # ------------------------------------------------------------------
    # 1. Determine the best model from CV metrics
    # ------------------------------------------------------------------
    cv_metrics_path = paths.data("processed", "cv_metrics.json")
    cv_metrics = _load_cv_metrics(cv_metrics_path)
    best_model_name = _select_best_model(cv_metrics)

    # ------------------------------------------------------------------
    # 2. Load the selected model
    # ------------------------------------------------------------------
    model_path = _model_path_for_name(best_model_name)
    model = _load_model(model_path)

    # ------------------------------------------------------------------
    # 3. Load the test split
    # ------------------------------------------------------------------
    test_path = paths.data("processed", "test.csv")
    X_test, y_test = _prepare_test_data(test_path)

    # ------------------------------------------------------------------
    # 4. Predict and compute basic metrics
    # ------------------------------------------------------------------
    y_pred = model.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    log.info(f"Test RMSE: {rmse:.4f}")
    log.info(f"Test MAE: {mae:.4f}")
    log.info(f"Test R²: {r2:.4f}")

    # ------------------------------------------------------------------
    # 5. Bootstrap confidence interval for RMSE
    # ------------------------------------------------------------------
    rmse_ci = _bootstrap_rmse_ci(y_test.values, y_pred, n_boot=10_000, ci=0.95)
    log.info(f"95 % CI for RMSE: [{rmse_ci[0]:.4f}, {rmse_ci[1]:.4f}]")

    # ------------------------------------------------------------------
    # 6. Paired two‑sided t‑test
    # ------------------------------------------------------------------
    p_val = _paired_t_test(y_test.values, y_pred)
    log.info(f"Paired t‑test p‑value: {p_val:.4g}")

    # ------------------------------------------------------------------
    # 7. Write performance JSON
    # ------------------------------------------------------------------
    _save_performance_json(
        performance_json,
        model_name=best_model_name,
        rmse=rmse,
        mae=mae,
        r2=r2,
        rmse_ci=rmse_ci,
        p_value=p_val,
    )

    # ------------------------------------------------------------------
    # 8. Generate scatter plot
    # ------------------------------------------------------------------
    figure_path = paths.figures("pred_vs_actual.png")
    _plot_predictions(y_test.values, y_pred, figure_path)

    # Final message for quickstart verification
    print("Pipeline completed successfully")

if __name__ == "__main__":
    main()