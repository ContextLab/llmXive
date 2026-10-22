"""
src/models/evaluate.py
-----------------------

Evaluation script for the held‑out test set.

This module implements the full evaluation pipeline required by task **T008**:
1. Load cross‑validation metrics and select the best‑performing model.
2. Load the corresponding fitted model (pickle file).
3. Predict on the test set and compute RMSE, MAE, and R².
4. Bootstrap 10 000 resamples of the residuals to obtain a 95 % confidence
   interval for RMSE.
5. Perform a paired two‑sided t‑test (α = 0.05) between predictions and the
   DFT ground‑truth values.
6. Assemble a JSON performance report that conforms to
   ``contracts/model_performance.schema.yaml`` and write it to
   ``data/processed/performance.json``.
7. Compute a SHA‑256 checksum for the JSON file.
8. Generate a scatter plot of predictions vs. actual values
   (``figures/pred_vs_actual.png``).

The script aborts with a non‑zero exit code if the paired t‑test p‑value is
≤ 0.05 (requirement SC‑003).  All paths are resolved via ``llmxive_toolkit.paths``.
"""

import argparse
import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import write_checksum

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions (signatures match the public API described in the spec)
# ----------------------------------------------------------------------
def _load_cv_metrics(cv_path: Path) -> dict:
    """Load the cross‑validation metrics JSON produced by ``src.models.train``."""
    if not cv_path.is_file():
        raise FileNotFoundError(f"CV metrics file not found at {cv_path}")
    with cv_path.open() as f:
        data = json.load(f)
    return data

def _select_best_model(cv_metrics: dict) -> str:
    """Choose the model identifier with the lowest mean RMSE."""
    best_name = None
    best_rmse = float("inf")
    for model_name, metrics in cv_metrics.get("cv_metrics", {}).items():
        rmse = metrics.get("rmse_mean")
        if rmse is None:
            continue
        if rmse < best_rmse:
            best_rmse = rmse
            best_name = model_name
    if best_name is None:
        raise RuntimeError("No model with RMSE information found in CV metrics.")
    log.info(f"Selected best model: {best_name} (RMSE mean = {best_rmse})")
    return best_name

def _model_path_for_name(model_name: str) -> Path:
    """Map a model name to its pickle file."""
    mapping = {
        "RandomForest": Path("models/rf_cv.pkl"),
        "GradientBoosting": Path("models/gb_cv.pkl"),
    }
    if model_name not in mapping:
        raise ValueError(f"Unknown model name '{model_name}'. Expected one of {list(mapping)}")
    return mapping[model_name]

def _load_model(model_path: Path):
    """Deserialize a scikit‑learn model from disk."""
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    return joblib.load(model_path)

def _prepare_test_data(test_path: Path, target_col: str = "formation_energy"):
    """Load the test CSV and split into features (X) and target (y)."""
    if not test_path.is_file():
        raise FileNotFoundError(f"Test set not found at {test_path}")
    df = pd.read_csv(test_path)
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' missing from test set.")
    if "composition" not in df.columns:
        raise KeyError("Column 'composition' required for grouping, but missing.")
    y = df[target_col].to_numpy()
    X = df.drop(columns=[target_col, "composition"])
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
    n_boot: int = 10_000,
    ci: float = 0.95,
) -> tuple[float, float]:
    """Bootstrap confidence interval for RMSE."""
    residuals = y_true - y_pred
    rng = np.random.default_rng(seed=42)
    boot_rmse = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(residuals), len(residuals))
        sample_res = residuals[idx]
        boot_rmse.append(np.sqrt(np.mean(sample_res ** 2)))
    lower = np.percentile(boot_rmse, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_rmse, (1 + ci) / 2 * 100)
    return float(lower), float(upper)

def _paired_t_test(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Perform a paired two‑sided t‑test; return the p‑value."""
    t_stat, p_val = stats.ttest_rel(y_true, y_pred)
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
        "cv_metrics": cv_metrics.get("cv_metrics", {}),
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
            "t_statistic": None,  # will be filled later by the caller if needed
            "p_value": p_value,
            "alpha": 0.05,
        },
        "feature_importances": [],  # placeholder – filled later by T009
        "fallback_needed": fallback_needed,
    }
    # Write JSON with pretty formatting for readability.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(performance, indent=2))
    log.info(f"Performance report written to {out_path}")

def _update_paired_ttest_fields(performance_path: Path, t_stat: float, p_value: float) -> None:
    """Insert the actual t‑statistic and p‑value into the JSON file."""
    if not performance_path.is_file():
        raise FileNotFoundError(f"Performance JSON not found at {performance_path}")
    data = json.loads(performance_path.read_text())
    data["paired_ttest"]["t_statistic"] = float(t_stat)
    data["paired_ttest"]["p_value"] = float(p_value)
    performance_path.write_text(json.dumps(data, indent=2))
    log.info("Updated paired‑t‑test fields in performance JSON.")

def _plot_predictions(y_true: np.ndarray, y_pred: np.ndarray, out_path: Path) -> None:
    """Create a scatter plot of predictions vs. actual values with a 1:1 line."""
    plt.figure(figsize=(6, 6))
    plt.scatter(y_true, y_pred, alpha=0.7, edgecolor="k")
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
    log.info(f"Prediction scatter plot saved to {out_path}")

def _parse_cli_args() -> argparse.Namespace:
    """CLI arguments – kept minimal because paths are convention‑based."""
    parser = argparse.ArgumentParser(
        description="Evaluate the best model on the held‑out test set."
    )
    parser.add_argument(
        "--cv-metrics",
        type=Path,
        default=paths.data("processed", "cv_metrics.json"),
        help="Path to the cross‑validation metrics JSON.",
    )
    parser.add_argument(
        "--test-csv",
        type=Path,
        default=paths.data("processed", "test.csv"),
        help="Path to the test set CSV.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=paths.data("processed", "performance.json"),
        help="Path where the performance JSON will be written.",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=paths.figures("pred_vs_actual.png"),
        help="Path for the prediction‑vs‑actual scatter plot.",
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    args = _parse_cli_args()

    # 1. Load CV metrics and pick the best model.
    cv_metrics = _load_cv_metrics(args.cv_metrics)
    best_model_name = _select_best_model(cv_metrics)

    # 2. Load the corresponding model.
    model_path = _model_path_for_name(best_model_name)
    model = _load_model(model_path)

    # 3. Prepare test data.
    X_test, y_test = _prepare_test_data(args.test_csv)

    # 4. Predict and compute basic metrics.
    y_pred = model.predict(X_test)
    rmse_val = _rmse(y_test, y_pred)
    mae_val = _mae(y_test, y_pred)
    r2_val = _r2(y_test, y_pred)

    # 5. Bootstrap confidence interval for RMSE.
    rmse_lower, rmse_upper = _bootstrap_rmse_ci(y_test, y_pred)

    # 6. Paired t‑test.
    p_val = _paired_t_test(y_test, y_pred)

    # 7. Decision rule for fallback.
    fallback_needed = (rmse_val > 0.5) or (r2_val < 0.70)

    # 8. Write performance JSON (t‑statistic placeholder for now).
    _save_performance_json(
        out_path=args.output_json,
        cv_metrics=cv_metrics,
        model_name=best_model_name,
        rmse=rmse_val,
        mae=mae_val,
        r2=r2_val,
        rmse_ci=(rmse_lower, rmse_upper),
        p_value=p_val,
        fallback_needed=fallback_needed,
    )

    # 9. Compute and write checksum for the JSON.
    write_checksum(args.output_json, Path("data/checksums"))

    # 10. Update JSON with the actual t‑statistic.
    t_stat, _ = stats.ttest_rel(y_test, y_pred)
    _update_paired_ttest_fields(args.output_json, float(t_stat), p_val)

    # 11. Generate the scatter plot.
    _plot_predictions(y_test, y_pred, args.figure)

    # 12. Enforce SC‑003: fail if p‑value ≤ 0.05.
    if p_val <= 0.05:
        log.error(
            f"Paired t‑test p‑value {p_val:.4f} ≤ 0.05 – evaluation considered a failure."
        )
        raise RuntimeError(
            f"Paired t‑test p-value {p_val:.4f} ≤ 0.05 (SC‑003 requirement)."
        )

    log.info("Evaluation completed successfully.")

if __name__ == "__main__":
    main()