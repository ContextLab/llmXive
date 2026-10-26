"""
qc.py
-------
Data validation and motion quality control (QC) for the HCP dataset.

This script reads the behavioural parquet file produced by
``src.data.download_hcp`` (``data/raw/dsrt_scores.parquet``), verifies that
all required columns are present, excludes subjects that do not satisfy
the motion threshold (mean FD >= 0.2 mm) or that are missing a DSRT score,
and writes two artefacts:

* ``data/derived/clean_subjects.parquet`` – a parquet table containing only
  the valid subjects with additional columns ``status`` (set to ``valid``),
  ``selected`` (boolean ``True``) and a SHA‑256 ``checksum`` of the row.
* ``data/derived/subject_qc.csv`` – a full QC log (including both valid and
  excluded subjects) containing ``subject_id, age, sex, mean_fd,
  dsrt_score, status, reason, selected, checksum``.  The ``status`` field
  follows the schema defined in ``contracts/subject_qc.schema.yaml``:
  ``valid``, ``excluded_motion`` or ``excluded_missing_data``.
  The ``reason`` column is populated for excluded subjects and left empty
  for valid ones.

The module also provides a reusable ``validate_and_filter`` function that
can be imported by downstream code or tests.

Usage (as a CLI)::

    python -m src.data.qc \\
        --input data/raw/dsrt_scores.parquet \\
        --fd-threshold 0.2 \\
        --output-dir data
"""
import argparse
import hashlib
from pathlib import Path
from typing import List, Tuple

import pandas as pd

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {"subject_id", "age", "sex", "mean_fd", "dsrt_score"}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _check_required_columns(df: pd.DataFrame) -> None:
    """Raise a ``ValueError`` if any required column is missing."""
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns in behavioural data: {missing}"
        )

def _row_checksum(row: pd.Series) -> str:
    """
    Compute a SHA‑256 checksum of the concatenated string representation of a row.

    The order of columns follows the row's index order. ``NaN`` values are
    represented as the string ``'nan'`` to keep the checksum deterministic.
    """
    values = [
        str(row[col]) if pd.notna(row[col]) else "nan" for col in row.index
    ]
    concatenated = "|".join(values).encode("utf-8")
    return hashlib.sha256(concatenated).hexdigest()

def validate_and_filter(
    df: pd.DataFrame,
    fd_threshold: float = 0.2,
) -> Tuple[pd.DataFrame, List[Tuple[str, str]]]:
    """
    Validate the behavioural dataframe and filter out subjects that do not
    meet quality criteria.

    Parameters
    ----------
    df : pd.DataFrame
        Input behavioural data containing at least the columns listed in
        ``REQUIRED_COLUMNS``.
    fd_threshold : float, optional
        Maximum allowed mean framewise displacement (default 0.2 mm).

    Returns
    -------
    clean_df : pd.DataFrame
        Subset of ``df`` that passed QC, with added columns ``status``,
        ``selected`` and ``checksum``.
    exclusions : list[tuple[str, str]]
        List of ``(subject_id, reason)`` tuples for each excluded subject.
    """
    _check_required_columns(df)

    exclusions: List[Tuple[str, str]] = []

    # Subjects missing DSRT scores
    mask_missing_dsrt = df["dsrt_score"].isna()
    for sid in df.loc[mask_missing_dsrt, "subject_id"]:
        exclusions.append((sid, "Missing DSRT score"))

    # Subjects with excessive motion
    mask_high_fd = df["mean_fd"] >= fd_threshold
    for sid in df.loc[mask_high_fd, "subject_id"]:
        exclusions.append((sid, f"Mean FD >= {fd_threshold} mm"))

    # Combine exclusion masks (a subject may be excluded for both reasons)
    exclusion_mask = mask_missing_dsrt | mask_high_fd
    clean_df = df.loc[~exclusion_mask].copy()
    # Add required QC columns for the clean set
    clean_df["status"] = "valid"
    clean_df["selected"] = True
    clean_df["checksum"] = clean_df.apply(_row_checksum, axis=1)

    return clean_df, exclusions

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate behavioural data and apply motion QC (FR‑002)."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(paths.data("raw", "dsrt_scores.parquet")),
        help="Path to the behavioural parquet file produced by download_hcp.",
    )
    parser.add_argument(
        "--fd-threshold",
        type=float,
        default=0.2,
        help="Maximum allowed mean FD (default 0.2 mm).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory (default: 'data').",
    )
    args = parser.parse_args()

    logger = get_logger(__name__)

    input_path = Path(args.input)
    if not input_path.is_file():
        logger.error("Input behavioural file not found: %s", input_path)
        raise FileNotFoundError(f"Behavioural file not found: {input_path}")

    logger.info("Reading behavioural data from %s", input_path)
    # Use ``fastparquet`` engine to avoid importing ``pyarrow`` which is not
    # available in the execution environment.
    behavioural_df = pd.read_parquet(input_path, engine="fastparquet")

    try:
        clean_df, exclusions = validate_and_filter(
            behavioural_df, fd_threshold=args.fd_threshold
        )
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("QC validation failed: %s", exc)
        raise

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    derived_dir = Path(args.output_dir) / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)

    # Write clean subjects parquet (valid rows only)
    clean_path = derived_dir / "clean_subjects.parquet"
    logger.info(
        "Writing %d valid subjects to %s", clean_df.shape[0], clean_path
    )
    clean_df.to_parquet(clean_path, index=False, engine="fastparquet")

    # ------------------------------------------------------------------
    # Build the full QC log (all subjects)
    # ------------------------------------------------------------------
    full_qc_df = behavioural_df.copy()

    # Initialise columns
    full_qc_df["status"] = "valid"
    full_qc_df["reason"] = ""
    full_qc_df["selected"] = True

    # Apply exclusions
    for sid, reason in exclusions:
        # Determine which schema status to assign
        if "Missing DSRT" in reason:
            status_val = "excluded_missing_data"
        else:
            status_val = "excluded_motion"

        mask = full_qc_df["subject_id"] == sid
        full_qc_df.loc[mask, "status"] = status_val
        full_qc_df.loc[mask, "reason"] = reason
        full_qc_df.loc[mask, "selected"] = False

    # Compute checksum for every row using the helper
    full_qc_df["checksum"] = full_qc_df.apply(_row_checksum, axis=1)

    # Re‑order columns to match the schema
    column_order = [
        "subject_id",
        "age",
        "sex",
        "mean_fd",
        "dsrt_score",
        "status",
        "reason",
        "selected",
        "checksum",
    ]
    qc_log_path = derived_dir / "subject_qc.csv"
    logger.info(
        "Writing full QC log (%d rows) to %s", full_qc_df.shape[0], qc_log_path
    )
    full_qc_df = full_qc_df[column_order]
    qc_log_path.parent.mkdir(parents=True, exist_ok=True)
    full_qc_df.to_csv(qc_log_path, index=False)

    # Log each exclusion via the shared logger
    for sid, reason in exclusions:
        logger.info("Excluding subject %s: %s", sid, reason)

    logger.info("QC step completed successfully.")

if __name__ == "__main__":
    main()
