"""Sensitivity analysis (Part 2) for cognitive decline prediction.

This script varies the definition of cognitive decline by adjusting the
required drop in MMSE/MOCA scores by ±1 point. For each definition it
re‑trains a Random Forest model on the full dataset and computes the
false‑positive and false‑negative rates. Results are written to
``data/processed/sensitivity_analysis_threshold_variation.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix

# Local utility imports
from utils.io import load_csv, save_json, ensure_dir

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
DEFAULT_DECLINE_THRESHOLD = 3  # points drop required to label decline
FEATURES_CSV = Path("data/processed/graph_metrics.csv")
ELIGIBLE_SUBJECTS_CSV = Path("data/processed/eligible_subjects.csv")
OUTPUT_JSON = Path("data/processed/sensitivity_analysis_threshold_variation.json")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_features() -> pd.DataFrame:
    """Load the pre‑computed graph metrics as feature matrix."""
    if not FEATURES_CSV.is_file():
        raise FileNotFoundError(f"Feature file not found: {FEATURES_CSV}")
    return load_csv(FEATURES_CSV)

def load_raw_scores() -> pd.DataFrame:
    """
    Load the raw cognitive scores needed to define decline.

    Expected columns (at minimum):
        - subject_id
        - mmse_t1, mmse_t2
        - moca_t1, moca_t2
    """
    if not ELIGIBLE_SUBJECTS_CSV.is_file():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_CSV}")
    return load_csv(ELIGIBLE_SUBJECTS_CSV)

def define_decline_label(
    scores_df: pd.DataFrame, threshold: int = DEFAULT_DECLINE_THRESHOLD
) -> pd.Series:
    """
    Produce a binary label series (1 = decline, 0 = stable) based on the
    supplied threshold. The function prefers MMSE when both MMSE and MOCA
    are present; otherwise it falls back to whichever is available.

    Parameters
    ----------
    scores_df : pd.DataFrame
        DataFrame containing raw scores.
    threshold : int
        Minimum drop required to be considered a decline.

    Returns
    -------
    pd.Series
        Binary labels indexed by ``subject_id``.
    """
    # Compute drops; ignore missing values (treated as no decline)
    def compute_drop(row: pd.Series) -> int:
        # Prefer MMSE
        if pd.notna(row.get("mmse_t1")) and pd.notna(row.get("mmse_t2")):
            return int(row["mmse_t1"] - row["mmse_t2"])
        elif pd.notna(row.get("moca_t1")) and pd.notna(row.get("moca_t2")):
            return int(row["moca_t1"] - row["moca_t2"])
        else:
            return 0

    drops = scores_df.apply(compute_drop, axis=1)
    labels = (drops >= threshold).astype(int)
    labels.index = scores_df["subject_id"]
    return labels

def train_random_forest(
    X: pd.DataFrame, y: pd.Series
) -> Tuple[RandomForestClassifier, np.ndarray]:
    """
    Train a Random Forest on the provided data and return both the fitted
    model and its predictions on the training set.

    The model uses the default hyper‑parameters (as required for the
    sensitivity analysis – we are not performing hyper‑parameter search here).

    Returns
    -------
    model : RandomForestClassifier
        The fitted classifier.
    preds : np.ndarray
        Predicted labels for ``X``.
    """
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=2,
    )
    rf.fit(X, y)
    preds = rf.predict(X)
    return rf, preds

def compute_fp_fn_rates(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Compute false‑positive and false‑negative rates.

    Returns a dict with keys:
        - "false_positive_rate"
        - "false_negative_rate"
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return {"false_positive_rate": fpr, "false_negative_rate": fnr}

def run_threshold_variation_analysis() -> Dict[int, Dict[str, float]]:
    """
    Iterate over three decline thresholds: default‑1, default, default+1.
    For each, re‑train the model and compute FP/FN rates.

    Returns
    -------
    results : dict
        Mapping from threshold value to a dict of FP/FN rates.
    """
    # Load data once
    features_df = load_features()
    scores_df = load_raw_scores()

    # Align feature rows with score rows via subject_id
    if "subject_id" not in features_df.columns:
        raise KeyError("features CSV must contain a 'subject_id' column")
    merged = features_df.merge(scores_df[["subject_id"]], on="subject_id", how="inner")
    X = merged.drop(columns=["subject_id"])

    results: Dict[int, Dict[str, float]] = {}
    for delta in (-1, 0, 1):
        thresh = DEFAULT_DECLINE_THRESHOLD + delta
        y = define_decline_label(scores_df, threshold=thresh).reindex(merged["subject_id"]).fillna(0).astype(int)
        # Guard against empty label sets
        if y.nunique() < 2:
            # If only one class present, FP/FN rates are undefined; record zeros.
            results[thresh] = {"false_positive_rate": 0.0, "false_negative_rate": 0.0}
            continue
        _, preds = train_random_forest(X, y)
        rates = compute_fp_fn_rates(y.values, preds)
        results[thresh] = rates
    return results

def write_outputs(results: Dict[int, Dict[str, float]]) -> None:
    """
    Persist the sensitivity analysis results to JSON.
    """
    ensure_dir(OUTPUT_JSON.parent)
    save_json(OUTPUT_JSON, results)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """
    Execute the sensitivity analysis. ``argv`` is ignored; the function
    exists to make the script callable from the test harness.
    Returns 0 on success, non‑zero on failure.
    """
    try:
        results = run_threshold_variation_analysis()
        write_outputs(results)
        print(f"Sensitivity analysis (threshold variation) written to {OUTPUT_JSON}")
        return 0
    except Exception as exc:
        print(f"Error during sensitivity analysis: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())