"""
src/models/evaluate.py
----------------------

Evaluates the best model (lowest mean CV RMSE) on the held‑out test set,
computes performance metrics, a bootstrap confidence interval for RMSE,
a paired two‑sided t‑test, and generates a scatter plot.
"""

import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import compute_checksum

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_cv_metrics(cv_path: Path) -> dict:
    with cv_path.open() as f:
        return json.load(f)


def _select_best_model(cv_metrics: dict) -> str:
    """
    Choose the model name with the lowest mean RMSE.
    """
    best = None
    best_rmse = float("inf")
    for model_name, metrics in cv_metrics.items():
        rmse_mean = metrics["rmse"]["mean"]
        if rmse_mean < best_rmse:
            best_rmse = rmse_mean
            best = model_name
    return best


def _model_path_for_name(model_name: str) -> Path:
    """
    Map a model identifier to its pickle file.
    """
    model_file = f"{model_name.lower()}_cv.pkl"
    return paths.root / "models" / model_file


def _load_model(model_path: Path):
    return joblib.load(model_path)


def _prepare_test_data(test_path: Path, target_col: str = "formation_energy"):
    df = pd.read_csv(test_path)
    X = df.drop(columns=[target_col, "composition"])
    y = df[target_col].values
    return X, y


def _bootstrap_rmse_ci(y_true: np.ndarray, y_pred: np.ndarray, n_boot: int = 10000, ci: float = 0.95):
    """
    Bootstrap confidence interval for RMSE.
    """
    rng = np.random.default_rng(42)
    boot_rmses = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y_true), len(y_true))
        rmse = np.sqrt(((y_true[idx] - y_pred[idx]) ** 2).mean())
        boot_rmses.append(rmse)
    lower = np.percentile(boot_rmses, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_rmses, (1 + ci) / 2 * 100)
    return lower, upper


def _paired_t_test(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Perform a paired two‑sided t‑test between predictions and true values.
    Returns the p‑value.
    """
    t_stat, p_val = stats.ttest_rel(y_true, y_pred)
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
    performance = {
        "model": model_name,
        "test_metrics": {"rmse": rmse, "mae": mae, "r2": r2},
        "bootstrap_ci": {"rmse_lower": rmse_ci[0], "rmse_upper": rmse_ci[1]},
        "paired_ttest": {"p_value": p_value},
        "fallback_needed": not (rmse <= 0.5 and r2 >= 0.70),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(performance, f, indent=2)

    # Compute checksum for the JSON file.
    checksum_path = paths.data("checksums", "performance.sha256")
    compute_checksum(out_path, checksum_path)


def _plot_predictions(y_true: np.ndarray, y_pred: np.ndarray, out_path: Path) -> None:
    plt.figure(figsize=(6, 6))
    plt.scatter(y_true, y_pred, alpha=0.7)
    max_val = max(y_true.max(), y_pred.max())
    min_val = min(y_true.min(), y_pred.min())
    plt.plot([min_val, max_val], [min_val, max_val], "r--", label="1:1 line")
    plt.xlabel("DFT formation energy (eV)")
    plt.ylabel("Predicted formation energy (eV)")
    plt.title("Predicted vs. actual defect formation energies")
    plt.legend()
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path)
    plt.close()


def main() -> None:
    """
    CLI entry point used by ``python -m src.models.evaluate``.
    Expected positional arguments:
        1. Path to the training CSV (unused but kept for API compatibility)
        2. Path to the test CSV
        3. Path to the output performance JSON
    """
    if len(sys.argv) != 4:
        raise RuntimeError(
            "Usage: python -m src.models.evaluate <train.csv> <test.csv> <performance.json>"
        )
    # train_path = Path(sys.argv[1])  # not needed for evaluation
    test_path = Path(sys.argv[2])
    perf_path = Path(sys.argv[3])

    # Load CV metrics and select the best model.
    cv_metrics_path = paths.data("processed", "cv_metrics.json")
    cv_metrics = _load_cv_metrics(cv_metrics_path)
    best_model_name = _select_best_model(cv_metrics)

    # Load the corresponding model pickle.
    model_path = _model_path_for_name(best_model_name)
    model = _load_model(model_path)

    # Load test data.
    X_test, y_test = _prepare_test_data(test_path)

    # Predict and compute metrics.
    y_pred = model.predict(X_test)
    rmse = np.sqrt(((y_test - y_pred) ** 2).mean())
    mae = np.mean(np.abs(y_test - y_pred))
    r2 = 1 - ((y_test - y_pred) ** 2).sum() / ((y_test - y_test.mean()) ** 2).sum()

    # Bootstrap CI for RMSE.
    rmse_ci = _bootstrap_rmse_ci(y_test, y_pred)

    # Paired t‑test.
    p_val = _paired_t_test(y_test, y_pred)

    # Save JSON performance report.
    _save_performance_json(
        perf_path, best_model_name, rmse, mae, r2, rmse_ci, p_val
    )

    # Generate scatter plot.
    plot_path = paths.figures("pred_vs_actual.png")
    _plot_predictions(y_test, y_pred, plot_path)

    log.info("Evaluation completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)
