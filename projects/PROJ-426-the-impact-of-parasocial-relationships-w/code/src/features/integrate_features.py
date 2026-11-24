"""
Integrate Features Script
-------------------------

This script merges the three feature artefacts produced by earlier pipeline
stages:

* ``matched_users.parquet`` – anonymised user records with loneliness scores
  and demographic covariates.
* ``usage_metrics.parquet`` – weekly usage frequency and session duration.
* ``attachment_scores.parquet`` – attachment‑anxiety and attachment‑avoidance
  proxy scores derived from the ECAR lexicon.

The merged result is written to ``data/processed/unified_dataset.parquet``.
The script aligns weekly usage metrics to the survey timestamps by aggregating
all usage occurring in the 28 days preceding each survey record (lagged structure).

Afterwards the result is validated against the contract schema
``contracts/unified_dataset.schema.yaml`` using the shared validation utility
``src.utils.data_validation``. A concise log file
``logs/unified_dataset_validation.log`` is created; it contains the single line
``validation passed`` when the schema check succeeds.
"""

import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np

from llmxive_toolkit import paths, get_logger
from src.utils.data_validation import validate_and_checksum, ValidationError

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------

def _load_parquet(file_path: Path) -> pd.DataFrame:
    """Load a Parquet file, raising a clear error if the file is missing."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required parquet file not found: {file_path}")
    return pd.read_parquet(file_path)

def _merge_features(
    matched_df: pd.DataFrame,
    usage_df: pd.DataFrame,
    attachment_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Perform the three‑way merge required for the unified dataset.

    To support the lagged structure (Usage at T predicts Loneliness at T+1),
    we align weekly usage to survey timestamps. For each survey record, we
    sum the usage metrics from the 4 weeks (28 days) immediately preceding
    the survey timestamp.

    1. ``matched_df`` is the primary longitudinal table.
    2. ``usage_df`` provides weekly aggregates.
    3. ``attachment_df`` provides user-level proxy scores.
    """
    # Ensure timestamps are datetime objects
    matched_df["timestamp"] = pd.to_datetime(matched_df["timestamp"], utc=True)
    usage_df["week_start"] = pd.to_datetime(usage_df["week_start"], utc=True)

    # 1. Align Usage to Survey (Lagged Window)
    # Join on user_id to create candidates for the window
    merged = pd.merge(
        matched_df,
        usage_df,
        on="user_id",
        how="inner",
        suffixes=("", "_usage"),
    )

    # Filter for usage that occurred in the 28 days PRIOR to the survey
    # Usage must be before the survey, but not more than 28 days before.
    # (merged["timestamp"] - merged["week_start"]) gives a Timedelta
    days_diff = (merged["timestamp"] - merged["week_start"]).dt.days
    merged = merged[(days_diff >= 0) & (days_diff < 28)].copy()

    # Aggregate usage metrics per survey record
    # We group by all survey-specific columns to keep them in the result
    group_cols = [
        "user_id", 
        "timestamp", 
        "survey_period", 
        "loneliness_score", 
        "age"
    ]
    # Ensure only existing columns from matched_df are used in grouping
    actual_group_cols = [c for c in group_cols if c in merged.columns]
    
    unified = (
        merged.groupby(actual_group_cols, as_index=False)
        .agg({
            "usage_frequency": "sum",
            "session_duration": "sum",
        })
    )

    # The contract for unified_dataset.schema.yaml specifies session_duration 
    # maximum: 24.0. Since usage_metrics.py produces duration in minutes,
    # we convert the summed total to hours to satisfy the contract.
    unified["session_duration"] = unified["session_duration"] / 60.0

    # 2. Merge Attachment Scores (Left join - user level)
    unified = pd.merge(
        unified,
        attachment_df,
        on="user_id",
        how="left",
    )

    # Create the missing‑attachment flag
    unified["missing_attachment_flag"] = unified["attachment_anxiety_score"].isna()

    # Fill NaNs with 0.0 to satisfy schema constraints [0.0, 1.0]
    unified["attachment_anxiety_score"] = unified["attachment_anxiety_score"].fillna(0.0)
    unified["attachment_avoidance_score"] = unified["attachment_avoidance_score"].fillna(0.0)

    # Final Column Selection to strictly match contracts/unified_dataset.schema.yaml
    # (additionalProperties: false)
    final_cols = [
        "user_id",
        "loneliness_score",
        "usage_frequency",
        "session_duration",
        "attachment_anxiety_score",
        "attachment_avoidance_score",
        "age",
        "timestamp",
        "survey_period",
        "missing_attachment_flag",
    ]
    
    # Only keep columns that actually exist in the result
    existing_final_cols = [c for c in final_cols if c in unified.columns]
    return unified[existing_final_cols]

def _write_validation_log(log_path: Path, message: str) -> None:
    """Write a tiny validation log file. The directory is created if needed."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(message + "\n", encoding="utf-8")

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------

def main() -> int:
    """
    Entry point used by the quick‑start and the unit test.
    Returns 0 on success, non-zero on failure.
    """
    logger = get_logger(__name__)

    try:
        # Resolve canonical input / output locations using llmxive_toolkit
        matched_path = paths.processed("matched_users.parquet")
        usage_path = paths.processed("usage_metrics.parquet")
        attachment_path = paths.processed("attachment_scores.parquet")
        unified_path = paths.processed("unified_dataset.parquet")
        schema_path = paths.contracts("unified_dataset.schema.yaml")
        log_path = paths.logs("unified_dataset_validation.log")

        logger.info("Loading feature artefacts")
        matched_df = _load_parquet(matched_path)
        usage_df = _load_parquet(usage_path)
        attachment_df = _load_parquet(attachment_path)

        logger.info("Merging feature tables with lagged time alignment")
        unified_df = _merge_features(matched_df, usage_df, attachment_df)

        logger.info(f"Writing unified dataset to {unified_path}")
        unified_path.parent.mkdir(parents=True, exist_ok=True)
        unified_df.to_parquet(unified_path, index=False)

        # Validation step – abort if the contract is violated
        logger.info("Running contract validation")
        try:
            validate_and_checksum(
                file_path=unified_path,
                schema_path=schema_path,
                checksum_path=None,
                file_type="parquet",
            )
        except ValidationError as ve:
            _write_validation_log(log_path, f"validation failed: {ve}")
            logger.error(f"Schema validation failed: {ve}")
            raise

        _write_validation_log(log_path, "validation passed")
        logger.info("Feature integration completed successfully")
        return 0

    except Exception as exc:
        logger.exception("Integrate features failed")
        # Ensure a failure log is always present
        try:
            failure_log = paths.logs("unified_dataset_validation.log")
            _write_validation_log(failure_log, f"validation failed: {exc}")
        except:
            pass
        return 1

if __name__ == "__main__":
    sys.exit(main())