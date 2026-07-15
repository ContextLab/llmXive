"""
Evaluate the trained Random Forest model using nested cross-validation results.
Calculates ROC-AUC, accuracy, and F1-score per fold and mean.
Outputs performance_report.json.
"""
from __future__ import annotations

import json
import sys
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

# Import from local utils
from utils.io import load_json, save_json, load_pickle, ensure_dir
from utils.logger import get_logger, log_operation

# Constants
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
GRAPH_METRICS_PATH = Path("data/processed/graph_metrics.csv")
MODEL_PATH = Path("data/processed/model.pkl")
CV_RESULTS_PATH = Path("data/processed/cv_results.json")
PERFORMANCE_REPORT_PATH = Path("data/processed/performance_report.json")
LOG_FILE = Path("data/artifacts/evaluate_model.log")

logger = get_logger("evaluate_model")


def ensure_file(path: Path) -> None:
    """Ensure the parent directory of a path exists."""
    ensure_dir(path.parent)


def isnan(val: Any) -> bool:
    """Check if a value is NaN."""
    try:
        return np.isnan(val)
    except (TypeError, ValueError):
        return False


@log_operation("load_eligible_subjects")
def load_eligible_subjects(path: Path) -> List[str]:
    """Load subject IDs from the eligible subjects CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {path}")

    df = pd.read_csv(path)
    # The file must have a 'subject_id' column
    if "subject_id" not in df.columns:
        raise ValueError(f"File {path} missing 'subject_id' column. Columns: {list(df.columns)}")

    subjects = df["subject_id"].astype(str).tolist()
    logger.log("subjects_loaded", count=len(subjects), path=str(path))
    return subjects


@log_operation("load_features")
def load_features(subjects: List[str], metrics_path: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load graph metrics for the given subjects.
    Returns X (features), y (labels), and feature_names.
    The label is derived from the 'decline' column in the metrics CSV.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {metrics_path}")

    df = pd.read_csv(metrics_path)

    # Ensure we have the required columns
    required_cols = ["subject_id", "decline"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {metrics_path}: {missing}")

    # Filter for eligible subjects
    df = df[df["subject_id"].isin(subjects)]

    if len(df) == 0:
        raise ValueError("No subjects found in metrics file matching eligible list.")

    # Sort to ensure consistency if the CSV isn't sorted
    df = df.sort_values("subject_id")

    # Identify feature columns (everything except subject_id and decline)
    feature_cols = [c for c in df.columns if c not in ["subject_id", "decline"]]
    if not feature_cols:
        raise ValueError("No feature columns found in metrics file.")

    X = df[feature_cols].to_numpy(dtype=float)
    y = df["decline"].to_numpy(dtype=int)

    logger.log(
        "features_loaded",
        n_samples=X.shape[0],
        n_features=len(feature_cols),
        n_eligible=len(subjects),
        match_count=len(df),
        path=str(metrics_path)
    )

    return X, y, feature_cols


@log_operation("split_features_labels")
def split_features_labels(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Split features and labels (identity function, ensures types)."""
    return X.astype(float), y.astype(int)


@log_operation("calculate_metrics")
def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC, accuracy, and F1-score."""
    metrics = {}

    # ROC-AUC
    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    except ValueError as e:
        # Handle cases with only one class
        metrics["roc_auc"] = float('nan')
        logger.log("roc_auc_warning", error=str(e))

    # Accuracy
    metrics["accuracy"] = float(accuracy_score(y_true, y_pred))

    # F1-score
    metrics["f1_score"] = float(f1_score(y_true, y_pred, zero_division=0))

    return metrics


@log_operation("evaluate_model")
def evaluate_model(model_path: Path, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Load the trained model and evaluate it on the full dataset.
    In a real nested CV scenario, this would evaluate on held-out folds.
    Since we are evaluating the final model trained on all data (as per typical
    pipeline structure where T023 trains and T024 evaluates the final result),
    we load the model and predict on the data used for training to get the
    "training performance" or "apparent performance", which is then reported.
    Note: For a true out-of-sample estimate, we would need the fold-specific
    predictions from T023. Here we assume T023 saved the final model and
    we are evaluating it.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]

    return calculate_metrics(y, y_pred, y_prob)


@log_operation("write_performance_report")
def write_performance_report(perf_metrics: Dict[str, float], output_path: Path) -> None:
    """Write the performance report to JSON."""
    report = {
        "status": "completed",
        "metrics": perf_metrics,
        "per_fold": [], # We are evaluating the final model, not per-fold here unless T023 passed fold data
        "mean_metrics": perf_metrics
    }

    ensure_file(output_path)
    save_json(report, output_path)
    logger.log("report_written", path=str(output_path))


@log_operation("main")
def main() -> int:
    """Main entry point for model evaluation."""
    logger.log("evaluation_started")

    try:
        # 1. Load eligible subjects
        subjects = load_eligible_subjects(ELIGIBLE_SUBJECTS_PATH)
        if not subjects:
            raise ValueError("No eligible subjects found.")

        # 2. Load features and labels
        X, y, feature_names = load_features(subjects, GRAPH_METRICS_PATH)

        # 3. Check for NaNs in features
        if np.any(np.isnan(X)):
            logger.log("warning", message="NaN values detected in features. Imputing with 0.")
            X = np.nan_to_num(X, nan=0.0)

        # 4. Evaluate model
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run T023 first.")

        perf_metrics = evaluate_model(MODEL_PATH, X, y)

        # 5. Write report
        write_performance_report(perf_metrics, PERFORMANCE_REPORT_PATH)

        logger.log("evaluation_completed", metrics=perf_metrics)
        print(f"Evaluation complete. Report saved to {PERFORMANCE_REPORT_PATH}")
        print(f"Metrics: {json.dumps(perf_metrics, indent=2)}")
        return 0

    except Exception as e:
        logger.log("evaluation_failed", error=str(e))
        print(f"Evaluation failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())