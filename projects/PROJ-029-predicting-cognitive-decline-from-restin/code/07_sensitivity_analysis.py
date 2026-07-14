"""
Sensitivity analysis for cognitive‑decline prediction.

Part 1 – Decision‑threshold sweep (already present in the original script).
Part 2 – Decline‑definition threshold variation (±1 point) with model
          re‑training for each variation.

The script reads pre‑computed graph metrics (features) and raw MMSE/MOCA
scores, builds binary decline labels, trains a RandomForest classifier,
and reports false‑positive / false‑negative rates for:
  * decision thresholds {0.45, 0.50, 0.55}
  * decline‑definition thresholds {base‑1, base, base+1}

All results are written to ``data/processed/sensitivity_report.json``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, load_csv, save_json

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

BASE_DECLINE_THRESHOLD = 3  # points drop required to be labelled as decline
DECLINE_DELTA_OPTIONS = [-1, 0, 1]  # ±1 point variations (including base)
DECISION_THRESHOLDS = [0.45, 0.50, 0.55]  # probability cut‑offs for classification

DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
GRAPH_METRICS_PATH = PROCESSED_DIR / "graph_metrics.csv"
ELIGIBLE_SUBJECTS_PATH = PROCESSED_DIR / "eligible_subjects.csv"
MODEL_PATH = PROCESSED_DIR / "model.pkl"
SENSITIVITY_REPORT_PATH = PROCESSED_DIR / "sensitivity_report.json"

logger = get_logger("sensitivity_analysis")

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def load_features() -> pd.DataFrame:
    """Load graph‑metric features."""
    logger.info("Loading graph metrics from %s", GRAPH_METRICS_PATH)
    if not GRAPH_METRICS_PATH.is_file():
        raise FileNotFoundError(f"Feature file missing: {GRAPH_METRICS_PATH}")
    df = pd.read_csv(GRAPH_METRICS_PATH)
    return df

def load_raw_scores() -> pd.DataFrame:
    """Load the raw MMSE / MoCA scores for eligible subjects."""
    logger.info("Loading raw cognitive scores from %s", ELIGIBLE_SUBJECTS_PATH)
    if not ELIGIBLE_SUBJECTS_PATH.is_file():
        raise FileNotFoundError(f"Score file missing: {ELIGIBLE_SUBJECTS_PATH}")
    df = pd.read_csv(ELIGIBLE_SUBJECTS_PATH)
    return df

def define_decline_label(df: pd.DataFrame, threshold: int = BASE_DECLINE_THRESHOLD) -> pd.Series:
    """
    Derive a binary decline label.

    The label is ``1`` (decline) if **any** of the following holds:
      * MMSE drop ≥ ``threshold`` points (t2 - t1 ≤ -threshold)
      * MoCA drop ≥ ``threshold`` points (t2 - t1 ≤ -threshold)

    If the relevant columns are missing, the function falls back to using
    whichever score is available.
    """
    logger.debug("Defining decline label with threshold %d", threshold)

    # Prefer MMSE if present, otherwise MoCA.
    if {"mmse_t1", "mmse_t2"}.issubset(df.columns):
        delta = df["mmse_t2"] - df["mmse_t1"]
        label = (delta <= -threshold).astype(int)
    elif {"moca_t1", "moca_t2"}.issubset(df.columns):
        delta = df["moca_t2"] - df["moca_t1"]
        label = (delta <= -threshold).astype(int)
    else:
        raise ValueError("Neither MMSE nor MoCA longitudinal columns found.")
    return label

def load_trained_model() -> RandomForestClassifier:
    """Load a previously trained model (if it exists)."""
    if MODEL_PATH.is_file():
        logger.info("Loading existing model from %s", MODEL_PATH)
        model = joblib.load(MODEL_PATH)
    else:
        logger.warning("Model file %s not found – a new model will be trained.", MODEL_PATH)
        model = None
    return model  # type: ignore[return-value]

def train_model(X: pd.DataFrame, y: pd.Series) -> RandomForestClassifier:
    """Train a RandomForest with the same hyper‑parameters used elsewhere."""
    logger.info("Training RandomForest (n_estimators=100, max_depth=None).")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=2,
    )
    rf.fit(X.drop(columns=["subject_id"], errors="ignore"), y)
    # Persist the model for downstream steps.
    ensure_dir(MODEL_PATH.parent)
    joblib.dump(rf, MODEL_PATH)
    logger.info("Model saved to %s", MODEL_PATH)
    return rf

def compute_fp_fn_rates(y_true: List[int], y_pred: List[int]) -> Tuple[float, float]:
    """
    Return (false_positive_rate, false_negative_rate).

    * False‑positive rate = FP / (FP + TN)
    * False‑negative rate = FN / (FN + TP)
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fp_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fn_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return fp_rate, fn_rate

# --------------------------------------------------------------------------- #
# Part 1 – Decision‑threshold sweep
# --------------------------------------------------------------------------- #

def part1_decision_threshold_sweep(model: RandomForestClassifier, X: pd.DataFrame, y: pd.Series) -> Dict[str, Dict[str, float]]:
    """Evaluate FP/FN rates for a set of decision thresholds."""
    logger.info("Running Part 1: decision‑threshold sweep.")
    probs = model.predict_proba(X.drop(columns=["subject_id"], errors="ignore"))[:, 1]
    results: Dict[str, Dict[str, float]] = {}
    for thr in DECISION_THRESHOLDS:
        preds = (probs >= thr).astype(int).tolist()
        fp, fn = compute_fp_fn_rates(y.tolist(), preds)
        results[f"threshold_{thr:.2f}"] = {"false_positive_rate": fp, "false_negative_rate": fn}
        logger.debug(
            "Decision threshold %.2f – FP: %.3f, FN: %.3f", thr, fp, fn
        )
    return results

# --------------------------------------------------------------------------- #
# Part 2 – Decline‑definition threshold variation
# --------------------------------------------------------------------------- #

def part2_decline_threshold_variation(
    X: pd.DataFrame,
    raw_scores: pd.DataFrame,
) -> Dict[str, Dict[str, float]]:
    """
    For each decline‑definition delta (‑1, 0, +1) re‑label the data,
    re‑train a model, and compute FP/FN rates at the **default** decision
    threshold of 0.50.
    """
    logger.info("Running Part 2: decline‑definition threshold variation.")
    baseline_thr = 0.50
    results: Dict[str, Dict[str, float]] = {}

    for delta in DECLINE_DELTA_OPTIONS:
        new_thr = BASE_DECLINE_THRESHOLD + delta
        logger.info("Evaluating decline threshold %d (delta %d).", new_thr, delta)

        # 1️⃣ Define new labels
        y_new = define_decline_label(raw_scores, threshold=new_thr)

        # 2️⃣ Train a fresh model
        model = train_model(X, y_new)

        # 3️⃣ Predict probabilities and apply baseline decision threshold
        probs = model.predict_proba(X.drop(columns=["subject_id"], errors="ignore"))[:, 1]
        preds = (probs >= baseline_thr).astype(int).tolist()

        # 4️⃣ Compute rates
        fp, fn = compute_fp_fn_rates(y_new.tolist(), preds)
        key = f"decline_thr_{new_thr}"
        results[key] = {"false_positive_rate": fp, "false_negative_rate": fn}
        logger.debug(
            "Decline thr %d – FP: %.3f, FN: %.3f", new_thr, fp, fn
        )

    return results

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main() -> int:
    """
    Execute the full sensitivity analysis and write a JSON report.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = error).
    """
    try:
        # Load data
        features_df = load_features()
        raw_scores_df = load_raw_scores()

        # Ensure we have a model – train if missing
        model = load_trained_model()
        if model is None:
            # Use the baseline decline definition to produce initial labels
            y_baseline = define_decline_label(raw_scores_df, threshold=BASE_DECLINE_THRESHOLD)
            model = train_model(features_df, y_baseline)

        # Part 1 – decision‑threshold sweep
        y_baseline = define_decline_label(raw_scores_df, threshold=BASE_DECLINE_THRESHOLD)
        part1_results = part1_decision_threshold_sweep(model, features_df, y_baseline)

        # Part 2 – decline‑definition variation
        part2_results = part2_decline_threshold_variation(features_df, raw_scores_df)

        # Consolidate report
        report = {
            "decision_threshold_sweep": part1_results,
            "decline_threshold_variation": part2_results,
            "metadata": {
                "base_decline_threshold": BASE_DECLINE_THRESHOLD,
                "decline_delta_options": DECLINE_DELTA_OPTIONS,
                "decision_thresholds": DECISION_THRESHOLDS,
            },
        }

        # Write JSON report
        ensure_dir(SENSITIVITY_REPORT_PATH.parent)
        save_json(report, SENSITIVITY_REPORT_PATH)
        logger.info("Sensitivity report written to %s", SENSITIVITY_REPORT_PATH)

        return 0
    except Exception as exc:  # pragma: no cover – top‑level safety net
        logger.error("Sensitivity analysis failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())