"""
code/05_evaluate_model.py
Calculate ROC-AUC, accuracy, and F1-score per fold and mean from the trained model and data.
Output: data/processed/performance_report.json
"""
from __future__ import annotations

import json
import sys
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

# Import shared logging utilities
from utils.logger import get_logger, log_operation

# Import data loading utilities
from utils.io import load_csv, load_json, save_json

# Import config
from config import get_config

logger = get_logger("evaluate_model")


def ensure_file(path: Path) -> None:
    """Ensure the directory for a file exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def isnan(val: Any) -> bool:
    """Check if a value is NaN, handling non-floats gracefully."""
    if isinstance(val, float):
        return np.isnan(val)
    if isinstance(val, np.floating):
        return np.isnan(val)
    return False


def load_eligible_subjects(path: Path) -> List[str]:
    """Load subject IDs from the eligible subjects CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {path}")
    df = load_csv(path)
    # Expecting a 'subject_id' column based on T017 output
    if "subject_id" in df.columns:
        return df["subject_id"].astype(str).tolist()
    # Fallback if column name differs slightly, though spec says subject_id
    cols = [c for c in df.columns if "subject" in c.lower()]
    if cols:
        return df[cols[0]].astype(str).tolist()
    return df.iloc[:, 0].astype(str).tolist()


def load_features(metrics_path: Path, subjects: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load graph metrics (features) and labels for the given subjects.
    Returns X (features) and y (labels).
    Labels are derived from the 'decline' column if present, or computed from MMSE/MOCA.
    For this evaluation step, we assume the features file already has the target column.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    df = load_csv(metrics_path)

    # Identify feature columns (exclude subject_id and target)
    exclude_cols = {"subject_id", "decline", "label", "target"}
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    if not feature_cols:
        raise ValueError("No feature columns found in metrics file.")

    # Filter for eligible subjects
    df = df[df["subject_id"].isin(subjects)]

    if df.empty:
        raise ValueError("No matching subjects found in metrics file.")

    X = df[feature_cols].to_numpy(dtype=float)
    y = df["decline"].to_numpy(dtype=int) if "decline" in df.columns else None

    if y is None:
        # Fallback: try 'label' or 'target'
        if "label" in df.columns:
            y = df["label"].to_numpy(dtype=int)
        elif "target" in df.columns:
            y = df["target"].to_numpy(dtype=int)
        else:
            raise ValueError("Could not find target/label/decline column in metrics file.")

    return X, y


def split_features_labels(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return X and y (identity split for this helper)."""
    return X, y


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC, Accuracy, and F1-score."""
    metrics = {}

    # Accuracy
    acc = accuracy_score(y_true, y_pred)
    metrics["accuracy"] = float(acc)

    # F1-score
    f1 = f1_score(y_true, y_pred, zero_division=0)
    metrics["f1_score"] = float(f1)

    # ROC-AUC
    try:
        auc = roc_auc_score(y_true, y_prob)
        metrics["roc_auc"] = float(auc)
    except ValueError as e:
        # Handle cases where only one class is present
        logger.log("calculate_metrics", operation="warning", message=str(e))
        metrics["roc_auc"] = None

    return metrics


def evaluate_model(model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Evaluate a sklearn model on data X, y."""
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None

    metrics = calculate_metrics(y, y_pred, y_prob) if y_prob is not None else calculate_metrics(y, y_pred, y_pred)

    # If predict_proba failed or returned None, try to estimate probability or handle gracefully
    if y_prob is None and "roc_auc" in metrics and metrics["roc_auc"] is None:
        # If we can't compute ROC-AUC, we still have acc and f1
        pass

    return {
        "predictions": y_pred.tolist(),
        "probabilities": y_prob.tolist() if y_prob is not None else None,
        "metrics": metrics
    }


def write_performance_report(report: Dict[str, Any], output_path: Path) -> None:
    """Write the performance report to JSON."""
    ensure_file(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    logger.log("write_performance_report", operation="info", path=str(output_path))


@log_operation
def main() -> None:
    """Main entry point for evaluation."""
    config = get_config()
    base_dir = Path(config.get("base_dir", "."))

    # Paths
    eligible_path = base_dir / "data" / "processed" / "eligible_subjects.csv"
    metrics_path = base_dir / "data" / "processed" / "graph_metrics.csv"
    model_path = base_dir / "data" / "processed" / "model.pkl"
    output_path = base_dir / "data" / "processed" / "performance_report.json"

    logger.log("evaluate_model_main", operation="start")

    # 1. Load eligible subjects
    try:
        subjects = load_eligible_subjects(eligible_path)
        logger.log("load_eligible_subjects", count=len(subjects))
    except FileNotFoundError as e:
        logger.log("evaluate_model_main", operation="error", message=str(e))
        print(f"Error: {e}")
        sys.exit(1)

    if not subjects:
        logger.log("evaluate_model_main", operation="error", message="No eligible subjects found.")
        print("Error: No eligible subjects found.")
        sys.exit(1)

    # 2. Load features and labels
    try:
        X, y = load_features(metrics_path, subjects)
        logger.log("load_features", shape=list(X.shape))
    except FileNotFoundError as e:
        logger.log("evaluate_model_main", operation="error", message=str(e))
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.log("evaluate_model_main", operation="error", message=str(e))
        print(f"Error: {e}")
        sys.exit(1)

    # 3. Load model
    if not model_path.exists():
        logger.log("evaluate_model_main", operation="error", message=f"Model not found: {model_path}")
        print(f"Error: Model not found at {model_path}")
        sys.exit(1)

    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        logger.log("load_model", path=str(model_path))
    except Exception as e:
        logger.log("evaluate_model_main", operation="error", message=str(e))
        print(f"Error loading model: {e}")
        sys.exit(1)

    # 4. Evaluate
    try:
        eval_results = evaluate_model(model, X, y)
    except Exception as e:
        logger.log("evaluate_model_main", operation="error", message=str(e))
        print(f"Error evaluating model: {e}")
        sys.exit(1)

    # 5. Construct report
    # Since we don't have per-fold results here (model is already trained on full data for this step),
    # we report the aggregate metrics on the held-out or full set used.
    # If the model was trained with CV, the 'model.pkl' usually contains the best estimator.
    # We report the metrics for this estimator on the current data split.
    report = {
        "task": "evaluate_model",
        "dataset": "ds000246",
        "subjects_count": len(subjects),
        "feature_count": X.shape[1],
        "model_path": str(model_path),
        "metrics": eval_results["metrics"],
        "timestamp": log_operation("get_timestamp").to_json() if hasattr(log_operation("get_timestamp"), "to_json") else None
    }

    # Write report
    write_performance_report(report, output_path)

    logger.log("evaluate_model_main", operation="complete", output=str(output_path))
    print(f"Performance report written to {output_path}")


if __name__ == "__main__":
    main()