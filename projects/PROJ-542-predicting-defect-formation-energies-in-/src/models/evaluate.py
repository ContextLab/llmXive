"""
src/models/evaluate.py
---------------------

Evaluation script for the perovskite defect formation energy project.
It selects the best model (lowest mean CV RMSE), predicts on the held‑out
test set, computes performance metrics, a bootstrap confidence interval for
RMSE, a paired two‑sided t‑test, and writes a JSON performance report.
It also generates a scatter plot of predictions vs. actual values and
writes a SHA‑256 checksum for the JSON artifact.
"""

import argparse
import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import compute_checksum, write_checksum

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_cv_metrics(cv_path: Path) -> dict:
    """Load the cross‑validation metrics JSON produced by ``src.models.train``."""
    if not cv_path.is_file():
        raise FileNotFoundError(f"CV metrics file not found at {cv_path}")
    with cv_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _select_best_model(cv_metrics: dict) -> str:
    """
    Choose the model identifier with the lowest mean RMSE.

    The ``cv_metrics`` dict follows the schema in
    ``contracts/model_performance.schema.yaml`` – it contains a top‑level
    ``cv_metrics`` key with entries for ``RandomForest`` and
    ``GradientBoosting``.  Each entry includes ``rmse_mean``.
    """
    if "cv_metrics" not in cv_metrics:
        raise KeyError("Missing 'cv_metrics' key in CV metrics JSON")
    model_rmse = {
        name: metrics["rmse_mean"]
        for name, metrics in cv_metrics["cv_metrics"].items()
    }
    best_model = min(model_rmse, key=model_rmse.get)
    log.info(f"Best model based on CV RMSE: {best_model} (RMSE={model_rmse[best_model]:.4f})")
    return best_model

def _model_path_for_name(model_name: str) -> Path:
    """Map a model name to its pickle file."""
    mapping = {
        "RandomForest": Path("models/rf_cv.pkl"),
        "GradientBoosting": Path("models/gb_cv.pkl"),
    }
    if model_name not in mapping:
        raise ValueError(f"Unrecognised model name '{model_name}'. Expected one of {list(mapping)}")
    return mapping[model_name]

def _load_model(model_path: Path):
    """Deserialize a scikit‑learn model from disk."""
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    return joblib.load(model_path)

def _prepare_test_data(test_path: Path, target_col: str = "formation_energy"):
    """Load the test CSV and split into features (X) and target (y)."""
    if not test_path.is_file():
        raise FileNotFoundError(f"Test CSV not found at {test_path}")
    df = pd.read_csv(test_path)
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not present in test data")
    y = df[target_col].to_numpy()
    # Drop target and any non‑feature columns (e.g. composition)
    X = df.drop(columns=[target_col])
    return X, y

def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.sqrt(np.mean((y_true - y_pred) ** 2))

def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.mean(np.abs(y_true - y_pred))

def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot != 0 else float("nan")

def _bootstrap_rmse_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_boot: int = 10000,
    ci: float = 0.95,
) -> tuple[float, float]:
    """
    Bootstrap confidence interval for RMSE.

    Resamples the *indices* of the test set with replacement,
    recomputes RMSE for each bootstrap sample and returns the
    lower/upper percentile bounds.
    """
    rng = np.random.default_rng(42)
    rmses = np.empty(n_boot, dtype=float)
    n = len(y_true)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        rmses[i] = _rmse(y_true[idx], y_pred[idx])
    lower = np.percentile(rmses, (1 - ci) / 2 * 100)
    upper = np.percentile(rmses, (1 + ci) / 2 * 100)
    return lower, upper

def _paired_t_test(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Perform a paired two‑sided t‑test between true and predicted values.
    Returns the p‑value.
    """
    t_stat, p_val = ttest_rel(y_true, y_pred)
    return float(p_val)

def _save_performance_json(
    out_path: Path,
    cv_metrics: dict,
    model_name: str,
    rmse: float,
    mae: float,
    r2: float,
    rmse_ci: tuple[float, float],
    p_value: float,
    fallback_needed: bool,
) -> None:
    """Assemble the JSON structure required by the schema and write it."""
    performance = {
        "cv_metrics": cv_metrics["cv_metrics"],
        "test_metrics": {
            "model_name": model_name,
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
        },
        "bootstrap_ci": {
            "rmse_lower": rmse_ci[0],
            "rmse_upper": rmse_ci[1],
            "confidence": 0.95,
        },
        "paired_ttest": {
            "t_statistic": float(ttest_rel(np.array([]), np.array([]))[0])  # placeholder, will be overwritten below
            # The actual t‑statistic is not required by the schema for validation,
            # but we include a sensible value for completeness.
        },
        "feature_importances": [],  # placeholder – populated later by T009
        "fallback_needed": fallback_needed,
    }

    # Insert the correct t‑statistic (computed together with the p‑value)
    t_stat, _ = ttest_rel(np.array([]), np.array([]))  # dummy to keep type‑checker happy
    # Re‑compute with real data below
    # (We cannot compute here because we only have p_value; the caller supplies the t‑statistic)
    # The caller will update the dict directly before writing.

    # Write JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(performance, f, indent=2)

def _update_paired_ttest_fields(performance_path: Path, t_stat: float, p_value: float) -> None:
    """Utility to insert the actual t‑statistic and p‑value into the JSON file."""
    with performance_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["paired_ttest"] = {
        "t_statistic": t_stat,
        "p_value": p_value,
        "alpha": 0.05,
    }
    with performance_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _plot_predictions(y_true: np.ndarray, y_pred: np.ndarray, out_path: Path) -> None:
    """Create a scatter plot of predictions vs. actual values with a 1:1 line."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 6))
    plt.scatter(y_true, y_pred, alpha=0.6, edgecolor="k")
    max_val = max(y_true.max(), y_pred.max())
    min_val = min(y_true.min(), y_pred.min())
    plt.plot([min_val, max_val], [min_val, max_val], "r--", label="1:1 line")
    plt.xlabel("DFT formation energy (eV)")
    plt.ylabel("Predicted formation energy (eV)")
    plt.title("Predicted vs. Actual Defect Formation Energies")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the best‑performing model on the held‑out test set."
    )
    parser.add_argument(
        "train_path",
        type=Path,
        help="Path to the training CSV (kept for API compatibility, not used).",
    )
    parser.add_argument(
        "test_path",
        type=Path,
        help="Path to the test CSV.",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Path where the performance JSON will be written.",
    )
    return parser.parse_args()

def main() -> None:
    args = _parse_cli_args()

    # 1. Load CV metrics and pick the best model.
    cv_metrics_path = paths.data("processed", "cv_metrics.json")
    cv_metrics = _load_cv_metrics(cv_metrics_path)
    best_model_name = _select_best_model(cv_metrics)

    # 2. Load the corresponding model.
    model_path = _model_path_for_name(best_model_name)
    model = _load_model(model_path)

    # 3. Load test data.
    X_test, y_test = _prepare_test_data(args.test_path)

    # 4. Predict.
    y_pred = model.predict(X_test)

    # 5. Compute metrics.
    rmse_val = _rmse(y_test, y_pred)
    mae_val = _mae(y_test, y_pred)
    r2_val = _r2(y_test, y_pred)

    # 6. Bootstrap CI for RMSE.
    rmse_lower, rmse_upper = _bootstrap_rmse_ci(y_test, y_pred)

    # 7. Paired t‑test.
    p_val = _paired_t_test(y_test, y_pred)
    if p_val <= 0.05:
        raise RuntimeError(
            f"Paired t‑test p‑value ({p_val:.4f}) ≤ 0.05 – statistical significance detected (SC‑003)."
        )
    t_stat, _ = ttest_rel(y_test, y_pred)

    # 8. Decision rule for fallback.
    fallback_needed = (rmse_val > 0.5) or (r2_val < 0.70)

    # 9. Write performance JSON.
    _save_performance_json(
        out_path=args.output_path,
        cv_metrics=cv_metrics,
        model_name=best_model_name,
        rmse=rmse_val,
        mae=mae_val,
        r2=r2_val,
        rmse_ci=(rmse_lower, rmse_upper),
        p_value=p_val,
        fallback_needed=fallback_needed,
    )

    # 10. Insert the correct t‑statistic and p‑value into the JSON.
    _update_paired_ttest_fields(args.output_path, float(t_stat), float(p_val))

    # 11. Generate scatter plot.
    fig_path = paths.figures("pred_vs_actual.png")
    _plot_predictions(y_test, y_pred, fig_path)

    # 12. Write checksum for the performance JSON.
    checksum_path = paths.data("checksums", "performance.sha256")
    compute_checksum(args.output_path, checksum_path)

    log.info("Evaluation completed successfully.")
    print("Evaluation completed successfully")

if __name__ == "__main__":
    main()
