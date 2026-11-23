"""
Random Forest model trained on *graph‑derived* features only (ablation study).

This script satisfies FR‑012 by using only topology‑derived statistics
(e.g., node degree, graph size) as input features. It re‑uses the
``load_graph_features_only`` helper from ``code/analysis/ablation.py``.
A CPU feasibility pre‑check is performed and its result is stored in
``data/results/metrics.json`` under the key ``cpu_feasibility_check``.
"""
import logging
import json
from pathlib import Path
import psutil
import time

from analysis.ablation import load_graph_features_only, train_ablation_model, evaluate_ablation_model
from utils.logging import setup_logging, log_result_artifact

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# CPU feasibility check (same logic as in the GNN script)
# ----------------------------------------------------------------------
def _cpu_feasibility_check() -> str:
    cpu_count = psutil.cpu_count(logical=True)
    mem = psutil.virtual_memory()
    free_gb = mem.available / (1024 ** 3)
    status = "passed" if cpu_count >= 2 and free_gb >= 2 else "warning"

    metrics_path = Path("data") / "results" / "metrics.json"
    try:
        if metrics_path.exists():
            with metrics_path.open("r", encoding="utf-8") as f:
                metrics = json.load(f)
        else:
            metrics = {}
    except Exception as e:
        logger.error(f"Failed to read metrics.json for CPU check: {e}")
        metrics = {}

    metrics["cpu_feasibility_check"] = status
    try:
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write cpu_feasibility_check: {e}")

    return status

# ----------------------------------------------------------------------
# Main training routine
# ----------------------------------------------------------------------
def main():
    """
    Trains a RandomForestRegressor using only graph‑derived features.
    Saves the model under ``models/rf_ablation.joblib`` and records
    training metrics in ``data/results/metrics.json``.
    """
    setup_logging(task_id="T004")
    logger.info("Starting RF ablation training script (T004).")

    cpu_status = _cpu_feasibility_check()
    if cpu_status != "passed":
        logger.warning("CPU feasibility check returned a warning – proceeding anyway.")

    # Load graph‑only feature matrices
    # The helper returns (X_train, X_val, X_test) as numpy arrays
    data_path = Path("data") / "processed"
    X_train, X_val, X_test = load_graph_features_only(str(data_path), target_col="target")

    # Train the ablation Random Forest
    start = time.time()
    model, _ = train_ablation_model(
        X_train,
        y_train=None,  # The helper loads y internally; we pass None per its signature
        X_val=X_val,
        y_val=None,
        model_path=str(Path("models") / "rf_ablation.joblib"),
        random_state=42,
    )
    training_time = time.time() - start

    # Evaluate on test set
    test_metrics = evaluate_ablation_model(model, X_test, y_test=None)

    # Record results
    metrics_path = Path("data") / "results" / "metrics.json"
    try:
        if metrics_path.exists():
            with metrics_path.open("r", encoding="utf-8") as f:
                metrics = json.load(f)
        else:
            metrics = {}
    except Exception as e:
        logger.error(f"Failed to read metrics.json: {e}")
        metrics = {}

    metrics.setdefault("models", {})
    metrics["models"]["rf_ablation"] = {
        "training_time_seconds": training_time,
        "test_metrics": test_metrics,
        "n_estimators": 100,
        "max_features": "sqrt"
    }

    try:
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"RF ablation metrics written to {metrics_path}")
    except Exception as e:
        logger.error(f"Failed to write RF ablation metrics: {e}")

    # Log artifact (model file) for completeness
    model_path = Path("models") / "rf_ablation.joblib"
    log_result_artifact(logger, str(model_path), "model", size_bytes=model_path.stat().st_size)

    logger.info("RF ablation training completed.")

if __name__ == "__main__":
    main()
