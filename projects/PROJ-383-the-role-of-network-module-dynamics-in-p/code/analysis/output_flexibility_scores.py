"""
Module: output_flexibility_scores.py

Purpose:
  Aggregate per-subject flexibility results computed by the dynamic connectivity
  pipeline and write a consolidated Parquet file containing one row per subject
  with their flexibility score.

Output:
  data/processed/flexibility_scores.parquet
    Columns:
      - subject_id: str
      - flexibility_score: float
      - n_windows: int
      - n_nodes: int
      - processing_status: str (ok | skipped | error)
      - error_message: str (optional, only if status != 'ok')
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Project-relative imports
from utils.logging_config import setup_logging, log_subject_exclusion
from utils.config import set_all_seeds

# Path constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "data" / "processed"
INPUT_DIR = PROJECT_ROOT / "data" / "processed"  # Where per-subject JSONs live
OUTPUT_FILE = RESULTS_DIR / "flexibility_scores.parquet"

# Ensure output directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def _get_input_json_path(subject_id: str) -> Path:
    """
    Construct the expected path for a per-subject flexibility JSON file.
    The dynamic_connectivity pipeline writes:
      data/processed/dynamic_results/<subject_id>.json
    """
    return INPUT_DIR / "dynamic_results" / f"{subject_id}.json"


def load_subject_flexibility_results(subject_id: str) -> Optional[Dict[str, Any]]:
    """
    Load the flexibility result dictionary for a single subject from its JSON file.

    Returns:
      Dict containing at least:
        - 'flexibility_score': float
        - 'n_windows': int
        - 'n_nodes': int
        - 'status': str
        - 'error_message': str (optional)
      or None if the file is missing or unreadable.
    """
    json_path = _get_input_json_path(subject_id)
    if not json_path.exists():
        return None

    try:
        import json
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logging.error(f"Failed to load flexibility results for subject {subject_id}: {e}")
        return None


def get_available_subjects() -> List[str]:
    """
    Scan the dynamic_results directory and return a list of subject IDs
    for which a JSON result file exists.
    """
    results_dir = INPUT_DIR / "dynamic_results"
    if not results_dir.exists():
        logging.warning(f"Dynamic results directory not found: {results_dir}")
        return []

    subjects = []
    for p in sorted(results_dir.glob("*.json")):
        # Strip extension and assume filename == subject_id
        subjects.append(p.stem)
    return subjects


def aggregate_flexibility_scores(subject_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Aggregate flexibility results for a list of subjects into a single DataFrame.

    If subject_ids is None, all available subjects in the dynamic_results directory
    are processed.

    Returns a DataFrame with columns:
      - subject_id
      - flexibility_score
      - n_windows
      - n_nodes
      - processing_status
      - error_message
    """
    if subject_ids is None:
        subject_ids = get_available_subjects()

    records = []
    for sid in subject_ids:
        data = load_subject_flexibility_results(sid)
        if data is None:
            # File missing or unreadable
            records.append({
                "subject_id": sid,
                "flexibility_score": np.nan,
                "n_windows": np.nan,
                "n_nodes": np.nan,
                "processing_status": "skipped",
                "error_message": "Result file missing or unreadable"
            })
            log_subject_exclusion(
                sid,
                reason="flexibility_result_missing",
                message="Result file missing or unreadable"
            )
            continue

        status = data.get("status", "unknown")
        if status != "ok":
            # Processing failed for this subject
            records.append({
                "subject_id": sid,
                "flexibility_score": np.nan,
                "n_windows": float(data.get("n_windows", np.nan)),
                "n_nodes": float(data.get("n_nodes", np.nan)),
                "processing_status": "error",
                "error_message": data.get("error_message", "Unknown error")
            })
            log_subject_exclusion(
                sid,
                reason="flexibility_computation_error",
                message=data.get("error_message", "Unknown error")
            )
            continue

        # Successful computation
        records.append({
            "subject_id": sid,
            "flexibility_score": float(data.get("flexibility_score", np.nan)),
            "n_windows": int(data.get("n_windows", np.nan)),
            "n_nodes": int(data.get("n_nodes", np.nan)),
            "processing_status": "ok",
            "error_message": ""
        })

    df = pd.DataFrame(records)
    if len(df) == 0:
        logging.warning("No flexibility results found to aggregate.")
        # Return empty DataFrame with expected schema
        df = pd.DataFrame(columns=[
            "subject_id",
            "flexibility_score",
            "n_windows",
            "n_nodes",
            "processing_status",
            "error_message"
        ])

    return df


def save_flexibility_scores(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the aggregated flexibility scores DataFrame to a Parquet file.

    Parameters:
      df: DataFrame with aggregated scores
      output_path: Optional custom output path; defaults to OUTPUT_FILE

    Returns:
      Path to the saved file
    """
    if output_path is None:
        output_path = OUTPUT_FILE

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure column order is consistent
    column_order = [
        "subject_id",
        "flexibility_score",
        "n_windows",
        "n_nodes",
        "processing_status",
        "error_message"
    ]
    existing_cols = [c for c in column_order if c in df.columns]
    extra_cols = [c for c in df.columns if c not in column_order]
    ordered_cols = existing_cols + extra_cols

    df_out = df[ordered_cols].copy()

    df_out.to_parquet(output_path, index=False)
    logging.info(f"Flexibility scores saved to {output_path}")
    return output_path


def main() -> None:
    """
    Entry point for the flexibility scores aggregation script.

    This function:
      1. Initializes logging and random seeds.
      2. Collects all available subject IDs.
      3. Aggregates their flexibility results into a DataFrame.
      4. Writes the DataFrame to data/processed/flexibility_scores.parquet.
    """
    # Setup logging
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "output_flexibility_scores.log"
    setup_logging(log_file=log_file, level=logging.INFO)

    # Set random seeds for reproducibility
    set_all_seeds()

    logging.info("Starting flexibility scores aggregation.")

    # Aggregate results
    df = aggregate_flexibility_scores()

    if df.empty:
        logging.warning("No subjects with flexibility results found. Exiting.")
        sys.exit(0)

    # Save to Parquet
    output_path = save_flexibility_scores(df)

    # Summary
    ok_count = int((df["processing_status"] == "ok").sum())
    total_count = len(df)
    logging.info(f"Aggregated {ok_count}/{total_count} subjects successfully.")
    logging.info(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()