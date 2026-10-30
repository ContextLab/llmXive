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
Afterwards the result is validated against the contract schema
``contracts/unified_dataset.schema.yaml`` using the shared validation utility
``src.utils.data_validation``.  A concise log file
``logs/unified_dataset_validation.log`` is created; it contains the single line
``validation passed`` when the schema check succeeds.

The script is deliberately lightweight – it performs only the joins required
by the contract and adds a ``missing_attachment_flag`` column (boolean) that
indicates whether attachment scores were unavailable for a given user.
"""

import sys
import logging
from pathlib import Path

import pandas as pd

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

    1. ``matched_df`` is the primary table – it already contains a
       ``user_id`` column (hashed Reddit username) and all survey‑related
       fields (loneliness_score, age, etc.).
    2. ``usage_df`` adds weekly usage metrics.  The contract expects a
       *single* record per user‑week, so we retain the join on ``user_id``.
    3. ``attachment_df`` provides the two attachment proxy scores.
       Not every user necessarily has a baseline post; in that case the
       scores are ``NaN`` and we set ``missing_attachment_flag`` to ``True``.

    The function returns a DataFrame that satisfies the
    ``contracts/unified_dataset.schema.yaml`` contract.
    """
    # Merge usage metrics (inner – a user must have at least one week of usage)
    merged = pd.merge(
        matched_df,
        usage_df,
        on="user_id",
        how="inner",
        suffixes=("", "_usage"),
    )

    # Merge attachment scores (left – keep all rows from the usage‑merged set)
    merged = pd.merge(
        merged,
        attachment_df,
        on="user_id",
        how="left",
        suffixes=("", "_attach"),
    )

    # Create the missing‑attachment flag
    merged["missing_attachment_flag"] = merged["attachment_anxiety_score"].isna()

    # For users lacking attachment scores we optionally fill with 0.0 to stay
    # within the 0‑1 range required by the schema.
    merged["attachment_anxiety_score"] = merged["attachment_anxiety_score"].fillna(0.0)
    merged["attachment_avoidance_score"] = merged["attachment_avoidance_score"].fillna(0.0)

    return merged


def _write_validation_log(log_path: Path, message: str) -> None:
    """Write a tiny validation log file.  The directory is created if needed."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(message + "\n", encoding="utf-8")


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------


def main() -> int:
    """
    Entry point used by the quick‑start and the unit test.

    Returns
    -------
    int
        0 on success, non‑zero on failure.
    """
    # Initialise a module‑level logger (console only – the explicit log file
    # is written later via ``_write_validation_log``).
    logger = get_logger(__name__)

    try:
        # Resolve canonical input / output locations
        base_dir = Path(__file__).resolve().parents[2]  # code/src/features → project root
        matched_path = base_dir / "data" / "processed" / "matched_users.parquet"
        usage_path = base_dir / "data" / "processed" / "usage_metrics.parquet"
        attachment_path = base_dir / "data" / "processed" / "attachment_scores.parquet"
        unified_path = base_dir / "data" / "processed" / "unified_dataset.parquet"
        schema_path = base_dir / "contracts" / "unified_dataset.schema.yaml"
        log_path = base_dir / "logs" / "unified_dataset_validation.log"

        logger.info("Loading feature artefacts")
        matched_df = _load_parquet(matched_path)
        usage_df = _load_parquet(usage_path)
        attachment_df = _load_parquet(attachment_path)

        logger.info("Merging feature tables")
        unified_df = _merge_features(matched_df, usage_df, attachment_df)

        logger.info(f"Writing unified dataset to {unified_path}")
        unified_path.parent.mkdir(parents=True, exist_ok=True)
        unified_df.to_parquet(unified_path, index=False)

        # ------------------------------------------------------------------
        # Validation step – abort if the contract is violated
        # ------------------------------------------------------------------
        logger.info("Running contract validation")
        try:
            # ``validate_and_checksum`` returns a dict; we only need to know that it
            # succeeded (it raises ValidationError on failure).
            validate_and_checksum(
                file_path=unified_path,
                schema_path=schema_path,
                checksum_path=None,
                file_type="parquet",
            )
        except ValidationError as ve:
            # Write a failure log and re‑raise so the exit code is non‑zero.
            _write_validation_log(log_path, f"validation failed: {ve}")
            logger.error(f"Schema validation failed: {ve}")
            raise

        # If we reach this point validation succeeded.
        _write_validation_log(log_path, "validation passed")
        logger.info("Feature integration completed successfully")
        return 0

    except Exception as exc:
        logger.exception("Integrate features failed")
        # Ensure a failure log is always present
        failure_log = Path(__file__).resolve().parents[2] / "logs" / "unified_dataset_validation.log"
        _write_validation_log(failure_log, f"validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
