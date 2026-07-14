"""
Sensitivity Analysis – Decision Threshold Sweep (Part 1) and
Decline‑Definition Threshold Variation (Part 2)

Part 1 evaluates how changing the classifier decision threshold
(0.45, 0.50, 0.55) impacts false‑positive and false‑negative rates.

Part 2 assesses robustness of the label definition by varying the
decline‑definition threshold by ±1 point on the raw MMSE/MOCA scores.
For each variation the model is retrained from scratch and the same
error rates are computed (using the default decision threshold of 0.5).

Results from both parts are written to ``data/processed/sensitivity_report.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_predict

from utils.logger import get_logger, log_operation

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def ensure_output_dir() -> Path:
    """Create the ``data/processed`` directory if it does not exist."""
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def load_features() -> pd.DataFrame:
    """
    Load the graph‑metric feature matrix.

    Expected location: ``data/processed/graph_metrics.csv``.
    The CSV must contain a column named ``label`` (binary 0/1) that
    represents the decline outcome, plus any number of feature columns.
    """
    features_path = Path("data/processed/graph_metrics.csv")
    if not features_path.is_file():
        raise FileNotFoundError(
            f"Feature matrix not found at {features_path}. "
            "Run the graph‑metric computation step before sensitivity analysis."
        )
    df = pd.read_csv(features_path)
    if "label" not in df.columns:
        raise KeyError(
            "The feature matrix must contain a 'label' column for the true outcome."
        )
    return df


def load_trained_model() -> object:
    """
    Load the serialized RandomForest model.

    Expected location: ``data/processed/model.pkl``.
    """
    model_path = Path("data/processed/model.pkl")
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Trained model not found at {model_path}. "
            "Run the training script before sensitivity analysis."
        )
    return joblib.load(model_path)


def compute_fp_fn_rates(
    true_labels: List[int], pred_probs: List[float], threshold: float
) -> Dict[str, float]:
    """
    Compute false‑positive and false‑negative rates for a given decision threshold.

    Parameters
    ----------
    true_labels: List[int]
        Ground‑truth binary labels (0 = no decline, 1 = decline).
    pred_probs: List[float]
        Predicted probability of decline for each subject.
    threshold: float
        Decision threshold to classify a subject as declining.

    Returns
    -------
    dict
        ``{\"false_positive_rate\": ..., \"false_negative_rate\": ...}``
    """
    if len(true_labels) != len(pred_probs):
        raise ValueError("Length of true_labels and pred_probs must match.")

    tp = fp = tn = fn = 0
    for y, p in zip(true_labels, pred_probs):
        pred = 1 if p >= threshold else 0
        if y == 1 and pred == 1:
            tp += 1
        elif y == 0 and pred == 1:
            fp += 1
        elif y == 0 and pred == 0:
            tn += 1
        elif y == 1 and pred == 0:
            fn += 1
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return {"false_positive_rate": fpr, "false_negative_rate": fnr}


# ----------------------------------------------------------------------
# Part 1 – Decision‑threshold sweep
# ----------------------------------------------------------------------


@log_operation("decision_threshold_sweep")
def part1_decision_threshold_sweep() -> Dict[float, Dict[str, float]]:
    """
    Perform a sweep over the decision thresholds {0.45, 0.50, 0.55}.

    Returns a dictionary mapping each threshold to its FP/FN rates.
    """
    logger = get_logger("sensitivity_analysis")
    logger.info("Starting decision‑threshold sweep.")

    df = load_features()
    X = df.drop(columns=["label"])
    y = df["label"].tolist()

    model = load_trained_model()
    if not hasattr(model, "predict_proba"):
        raise AttributeError(
            "Loaded model does not implement ``predict_proba``; cannot compute thresholds."
        )
    pred_probs = model.predict_proba(X)[:, 1].tolist()

    thresholds = [0.45, 0.50, 0.55]
    results: Dict[float, Dict[str, float]] = {}

    for thr in thresholds:
        rates = compute_fp_fn_rates(y, pred_probs, thr)
        results[thr] = rates
        logger.info(
            f"Threshold {thr:.2f}: FPR={rates['false_positive_rate']:.3f}, "
            f"FNR={rates['false_negative_rate']:.3f}"
        )

    return results


# ----------------------------------------------------------------------
# Part 2 – Decline‑definition threshold variation
# ----------------------------------------------------------------------


@log_operation("label_threshold_variation")
def part2_label_threshold_variation() -> Dict[int, Dict[str, float]]:
    """
    Vary the decline‑definition threshold by ±1 point (i.e. -1, 0, +1)
    on the raw MMSE/MOCA scores, retrain the model for each variation,
    and compute FP/FN rates using the default decision threshold of 0.5.

    Returns a dictionary keyed by the threshold adjustment (e.g. -1, 0, +1)
    with the corresponding FP/FN rates.
    """
    logger = get_logger("sensitivity_analysis")
    logger.info("Starting label‑threshold variation analysis.")

    # Load the full feature matrix (including raw scores if present)
    df = load_features()

    # Identify raw score columns – they may be named with common prefixes.
    # We look for columns containing 'mmse' or 'moca' (case‑insensitive).
    raw_score_cols = [c for c in df.columns if any(tag in c.lower() for tag in ("mmse", "moca"))]
    if not raw_score_cols:
        logger.warning(
            "No raw MMSE/MOCA columns detected; falling back to existing labels."
        )

    # Original label column
    original_label = df["label"].copy()

    results: Dict[int, Dict[str, float]] = {}

    for delta in (-1, 0, 1):
        logger.info(f"Evaluating label adjustment delta={delta}.")

        # If raw scores are available we attempt a simple recomputation:
        # Assume a decline is defined as a drop of >= (3 + delta) points
        # between the first and last available timepoint.
        if raw_score_cols:
            # Simple heuristic: treat the first column as baseline and the last as follow‑up.
            baseline = df[raw_score_cols[0]]
            followup = df[raw_score_cols[-1]]
            drop = baseline - followup
            new_label = (drop >= (3 + delta)).astype(int)
        else:
            # No raw scores – keep the original label unchanged.
            new_label = original_label

        # Prepare training data
        X = df.drop(columns=["label"])
        y = new_label.tolist()

        # Train a fresh RandomForest (same hyper‑parameters as the original script)
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,
            random_state=random_state,
            n_jobs=2,
        )

        # Use cross‑validated predictions to obtain probabilities without a separate test split
        pred_probs = cross_val_predict(
            rf, X, y, cv=5, method="predict_proba", n_jobs=2
        )[:, 1].tolist()

        # Compute FP/FN rates at the default threshold 0.5
        rates = compute_fp_fn_rates(y, pred_probs, threshold=0.5)
        results[delta] = rates
        logger.info(
            f"Delta {delta:+d}: FPR={rates['false_positive_rate']:.3f}, "
            f"FNR={rates['false_negative_rate']:.3f}"
        )

    return results


# ----------------------------------------------------------------------
# Entry point – combine both analyses and write a unified report
# ----------------------------------------------------------------------


def main() -> None:
    """Run both parts of the sensitivity analysis and write the combined report."""
    # Part 1
    decision_results = part1_decision_threshold_sweep()

    # Part 2
    label_variation_results = part2_label_threshold_variation()

    # Combine into a single JSON structure
    combined_report = {
        "decision_threshold_sweep": decision_results,
        "label_threshold_variation": label_variation_results,
    }

    out_dir = ensure_output_dir()
    out_path = out_dir / "sensitivity_report.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(combined_report, f, indent=2)

    logger = get_logger("sensitivity_analysis")
    logger.info(f"Sensitivity report (both parts) written to {out_path}")


if __name__ == "__main__":
    main()
