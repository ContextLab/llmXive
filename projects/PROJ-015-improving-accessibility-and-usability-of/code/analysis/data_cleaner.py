"""
Data cleaning utilities for the accessibility and usability study.

This module provides the core functions required by task **T004**:
  * ``remove_incomplete(df)`` – drop sessions marked as incomplete or dropout.
  * ``impute_sus(df)`` – impute a single missing SUS item with the participant mean;
    rows with >1 missing item are marked as incomplete.
  * ``compute_sus_score(responses)`` – compute a SUS score (0‑100) using the
    standard SUS formula.
  * ``derive_metrics(df)`` – assemble the final ``metrics_summary.csv`` containing
    the cleaned and derived metrics required by downstream analysis.

The module also offers a small CLI (``python -m code.analysis.data_cleaner``) that
loads real session data from ``data/raw`` (using the strict loader), runs the
cleaning pipeline, and writes the metrics summary to
``data/processed/metrics_summary.csv``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Sequence

import pandas as pd

from llmxive_toolkit import paths, get_logger

# Import the real‑data loader that raises loudly if no real data is present.
from analysis.data_loader import load_real_data

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions required by the specification
# ----------------------------------------------------------------------


def remove_incomplete(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where the ``status`` column indicates an incomplete session.

    Parameters
    ----------
    df : pd.DataFrame
        The raw session dataframe.

    Returns
    -------
    pd.DataFrame
        Dataframe containing only rows with ``status`` equal to ``'complete'``
        (or where the column is missing – such rows are kept because they are
        not explicitly marked incomplete).
    """
    if "status" not in df.columns:
        log.warning("Column 'status' not found – assuming all rows are complete.")
        return df.copy()

    mask = ~df["status"].isin(["incomplete", "dropout"])
    filtered = df[mask].reset_index(drop=True)
    dropped = len(df) - len(filtered)
    if dropped:
        log.info(f"Removed {dropped} incomplete/dropout rows.")
    return filtered


def impute_sus(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing SUS item responses.

    The raw data may contain individual SUS question columns named
    ``sus_q1`` … ``sus_q10``.  If a row has **exactly one** missing value,
    that value is replaced with the participant’s mean across the other nine
    items.  Rows with **more than one** missing item are marked as incomplete
    (their ``status`` column is set to ``'incomplete'``) so they will be
    removed by :func:`remove_incomplete`.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe that contains the SUS question columns.

    Returns
    -------
    pd.DataFrame
        A copy of ``df`` with missing values imputed where possible and
        ``status`` updated for rows that could not be salvaged.
    """
    sus_cols = [c for c in df.columns if c.startswith("sus_q") and c != "sus_score"]
    if not sus_cols:
        log.info("No individual SUS question columns found – skipping imputation.")
        return df.copy()

    df = df.copy()

    def _impute_row(row):
        missing = row[sus_cols].isna()
        n_missing = missing.sum()
        if n_missing == 0:
            return row
        if n_missing == 1:
            # Impute with participant mean (excluding the missing item)
            mean_val = row[sus_cols].mean(skipna=True)
            row[sus_cols] = row[sus_cols].fillna(mean_val)
            # Optional flag for downstream use – not required by the spec
            row["sus_imputed"] = True
            return row
        # >1 missing → mark as incomplete
        row["status"] = "incomplete"
        return row

    df = df.apply(_impute_row, axis=1)
    return df


def compute_sus_score(responses: Sequence[int | float]) -> float:
    """
    Compute the System Usability Scale (SUS) score from ten questionnaire items.

    The standard SUS algorithm:
      * For odd‑numbered items (1,3,5,7,9) subtract 1.
      * For even‑numbered items (2,4,6,8,10) subtract the response from 5.
      * Sum the adjusted values and multiply by 2.5 to obtain a score in the
        range 0‑100.

    Parameters
    ----------
    responses : sequence of 10 numeric responses (1‑5)

    Returns
    -------
    float
        SUS score between 0 and 100.
    """
    if len(responses) != 10:
        raise ValueError("SUS requires exactly 10 item responses.")
    # Ensure we work with floats to avoid integer division surprises
    vals = [float(r) for r in responses]

    odd_sum = sum(vals[i] - 1 for i in range(0, 10, 2))          # indices 0,2,4,6,8 → items 1,3,5,7,9
    even_sum = sum(5 - vals[i] for i in range(1, 10, 2))         # indices 1,3,5,7,9 → items 2,4,6,8,10
    sus_score = (odd_sum + even_sum) * 2.5
    # Clamp to the 0‑100 range in case of out‑of‑bounds input
    return max(0.0, min(100.0, sus_score))


def derive_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce the final metrics summary required by downstream analysis.

    The function expects a dataframe that already has:
      * ``participant_id``
      * ``interface_variant`` (or ``interface_type`` – both are accepted)
      * ``completion_time_seconds`` (or ``completion_time``)
      * ``error_count``
      * ``explanation_engagement_time_seconds`` (or ``explanation_engagement_time``)
      * SUS question columns ``sus_q1`` … ``sus_q10``

    It:
      1. Computes the SUS score for each row via :func:`compute_sus_score`.
      2. Normalises column names to match the contract:
         ``completion_time_sec`` and ``explanation_engagement_time_sec``.
      3. Writes the resulting dataframe to ``data/processed/metrics_summary.csv``
         (creating the folder if necessary).

    Returns
    -------
    pd.DataFrame
        The metrics dataframe that was written to disk.
    """
    required_cols = {"participant_id", "interface_variant", "completion_time_seconds",
                     "error_count", "explanation_engagement_time_seconds"}
    # Accept alternative column names used elsewhere in the code base
    col_aliases = {
        "interface_type": "interface_variant",
        "completion_time": "completion_time_seconds",
        "explanation_engagement_time": "explanation_engagement_time_seconds",
    }

    df = df.copy()
    for old, new in col_aliases.items():
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)

    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for metrics derivation: {missing}")

    # Compute SUS score per participant
    sus_cols = [f"sus_q{i}" for i in range(1, 11)]
    if not all(col in df.columns for col in sus_cols):
        raise ValueError("All SUS question columns (sus_q1‑sus_q10) must be present.")

    df["sus_score"] = df.apply(lambda r: compute_sus_score([r[col] for col in sus_cols]), axis=1)

    # Build the final dataframe with the contract‑specified column names
    metrics_df = pd.DataFrame({
        "participant_id": df["participant_id"],
        "interface_variant": df["interface_variant"],
        "completion_time_sec": df["completion_time_seconds"],
        "error_count": df["error_count"],
        "explanation_engagement_time_sec": df["explanation_engagement_time_seconds"],
        "sus_score": df["sus_score"],
    })

    # Write CSV
    output_path = paths.data("processed", "metrics_summary.csv")
    metrics_df.to_csv(output_path, index=False)
    log.info(f"Metrics summary written to {output_path}")

    return metrics_df

# ----------------------------------------------------------------------
# CLI entry point – mirrors the behaviour described in the task spec
# ----------------------------------------------------------------------


def main() -> None:
    """
    CLI for the data‑cleaning pipeline.

    Example usage:
    ``python -m code.analysis.data_cleaner --input data/raw --dev-mode``
    """
    parser = argparse.ArgumentParser(description="Clean raw session data and produce metrics summary.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw",
        help="Directory containing raw JSON session files.",
    )
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        help="Allow the pipeline to run even if only simulated data is present. "
             "In production this flag must be omitted.",
    )
    args = parser.parse_args()

    # Load raw sessions – this will raise loudly if no real data is found.
    try:
        raw_df = load_real_data(args.input)
    except FileNotFoundError as exc:
        log.error(str(exc))
        sys.exit(1)

    # Apply the cleaning steps defined above.
    df_clean = remove_incomplete(raw_df)
    df_clean = impute_sus(df_clean)

    # Any rows that became incomplete during imputation are dropped now.
    df_clean = remove_incomplete(df_clean)

    # Derive the final metrics and write the CSV.
    try:
        derive_metrics(df_clean)
    except Exception as exc:
        log.error(f"Failed to derive metrics: {exc}")
        sys.exit(1)

    log.info("Data cleaning pipeline completed successfully.")


if __name__ == "__main__":
    main()