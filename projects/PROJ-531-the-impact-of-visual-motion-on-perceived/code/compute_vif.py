"""
T015 – Compute Variance Inflation Factor (VIF) diagnostics.

This script reads the analysis‑ready dataset, computes VIF for each
predictor (motion features), excludes any predictor with VIF ≥ 5,
and writes a JSON report to ``data/processed/vif_report.json``.
The report contains the VIF value for every considered feature and a
top‑level boolean ``vif_pass`` indicating whether all retained features
satisfy the VIF threshold.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
INPUT_CSV = paths.data("processed", "analysis_ready.csv")
OUTPUT_JSON = paths.data("processed", "vif_report.json")
VIF_THRESHOLD = 5.0

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_data(csv_path: Path) -> pd.DataFrame:
    """Load the analysis‑ready CSV; raise if missing."""
    if not csv_path.exists():
        log.error(f"Input file not found: {csv_path}")
        raise FileNotFoundError(f"Missing input file: {csv_path}")
    df = pd.read_csv(csv_path)
    log.info(f"Loaded analysis data with shape {df.shape}")
    return df

def select_predictor_columns(df: pd.DataFrame) -> list:
    """
    Return a list of columns to be treated as predictors.

    Excludes identifier columns and the outcome variable.  Columns that are
    completely missing are dropped because they cannot contribute to a VIF
    calculation.
    """
    exclude = {"participant_id", "agency_score", "user_response_trigger"}
    predictors = [c for c in df.columns if c not in exclude]
    # Drop columns that are entirely NaN – they would cause singular matrices.
    predictors = [c for c in predictors if not df[c].isna().all()]
    log.debug(f"Selected predictor columns: {predictors}")
    return predictors

def compute_vif(df: pd.DataFrame, predictor_cols: list) -> dict:
    """
    Compute VIF for each predictor column.

    If only a single predictor is present, its VIF is defined as 1.0.
    Returns a dict mapping column name → VIF (float).
    """
    if not predictor_cols:
        log.warning("No predictor columns found for VIF calculation.")
        return {}

    # Prepare the matrix (add constant for statsmodels compatibility)
    X = df[predictor_cols].astype(float).fillna(0.0).values
    vif_dict = {}
    if X.shape[1] == 1:
        # Single predictor – VIF is 1 by definition
        vif_dict[predictor_cols[0]] = 1.0
        return vif_dict

    for i, col in enumerate(predictor_cols):
        # variance_inflation_factor expects the design matrix without a constant
        vif = variance_inflation_factor(X, i)
        vif_dict[col] = float(vif)
        log.debug(f"VIF for {col}: {vif:.3f}")
    return vif_dict

def write_report(vif_dict: dict, output_path: Path) -> None:
    """Write the VIF report JSON, adding the ``vif_pass`` flag."""
    excluded = [f for f, v in vif_dict.items() if v >= VIF_THRESHOLD]
    included = [f for f, v in vif_dict.items() if v < VIF_THRESHOLD]

    report = {
        "vif_per_feature": vif_dict,
        "included_features": included,
        "excluded_features": excluded,
        "vif_pass": len(excluded) == 0,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    log.info(f"VIF report written to {output_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Execute the VIF diagnostic pipeline.

    Returns:
        0 on success, non‑zero on failure (so the script can be used in
        ``bash run_pipeline.sh`` with proper exit‑code handling).
    """
    try:
        df = load_data(INPUT_CSV)
        predictor_cols = select_predictor_columns(df)
        vif_dict = compute_vif(df, predictor_cols)
        write_report(vif_dict, OUTPUT_JSON)
    except Exception as e:
        log.exception("VIF computation failed")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
