"""adherence_extraction.extract_metrics
-------------------------------------------------
Implements extraction of adherence metrics from usage‑metadata files
(CSV or JSON) and adds detailed logging for each metric computation step
as required by task T024.
-------------------------------------------------
The script can be executed directly:
    python code/adherence_extraction/extract_metrics.py --input <path> --output <path>
It will write a CSV file with per‑user metrics to the output location and
emit JSON‑line log entries (and human‑readable messages) via the
``pipeline_logger`` utility.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Union

import pandas as pd

# Pipeline logger utilities
from logging.pipeline_logger import get_logger, log_dict


__all__ = ["extract_metrics", "main"]


def _read_input(input_path: Path) -> pd.DataFrame:
    """Read a CSV or JSON file containing usage‑metadata."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() == ".csv":
        df = pd.read_csv(input_path)
    elif input_path.suffix.lower() == ".json":
        # Assume a list‑of‑records JSON file
        df = pd.read_json(input_path, orient="records", lines=False)
    else:
        raise ValueError(
            f"Unsupported file type: {input_path.suffix}. Expected .csv or .json"
        )

    return df


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce columns to appropriate dtypes and drop malformed rows."""
    required_cols = [
        "user_id",
        "session_start",
        "session_end",
        "session_completed",
        "self_reported_engagement",
    ]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in input data: {missing}")

    # Convert timestamps
    df["session_start"] = pd.to_datetime(df["session_start"], errors="coerce")
    df["session_end"] = pd.to_datetime(df["session_end"], errors="coerce")

    # Ensure boolean for completion flag
    df["session_completed"] = df["session_completed"].astype(bool)

    # Ensure numeric for self‑reported engagement
    df["self_reported_engagement"] = pd.to_numeric(
        df["self_reported_engagement"], errors="coerce"
    )

    # Drop rows where timestamps could not be parsed
    df = df.dropna(subset=["session_start", "session_end"])

    return df


def _compute_user_metrics(df: pd.DataFrame, logger) -> pd.DataFrame:
    """Compute adherence metrics per user and log each step."""
    results = []

    for user_id, group in df.groupby("user_id"):
        # Basic counts
        total_sessions = len(group)

        # ------------------------------------------------------------------
        # Metric 1: sessions_per_week
        # ------------------------------------------------------------------
        min_start = group["session_start"].min()
        max_end = group["session_end"].max()
        # Number of weeks covered – add a small epsilon to avoid division by zero
        weeks_covered = max(
            (max_end - min_start).days / 7.0, 1e-6
        )  # at least a tiny fraction of a week
        sessions_per_week = total_sessions / weeks_covered
        logger.info(
            f"Computed sessions_per_week: {sessions_per_week:.3f} for user {user_id}"
        )
        log_dict(
            {
                "event": "metric_computed",
                "user_id": user_id,
                "metric": "sessions_per_week",
                "value": sessions_per_week,
            }
        )

        # ------------------------------------------------------------------
        # Metric 2: completion_rate
        # ------------------------------------------------------------------
        completed = group["session_completed"].sum()
        completion_rate = completed / total_sessions if total_sessions else 0.0
        logger.info(
            f"Computed completion_rate: {completion_rate:.3f} for user {user_id}"
        )
        log_dict(
            {
                "event": "metric_computed",
                "user_id": user_id,
                "metric": "completion_rate",
                "value": completion_rate,
            }
        )

        # ------------------------------------------------------------------
        # Metric 3: average_session_duration (minutes)
        # ------------------------------------------------------------------
        durations = (group["session_end"] - group["session_start"]).dt.total_seconds()
        avg_duration = durations.mean() / 60.0 if not durations.empty else 0.0
        logger.info(
            f"Computed avg_session_duration: {avg_duration:.2f} min for user {user_id}"
        )
        log_dict(
            {
                "event": "metric_computed",
                "user_id": user_id,
                "metric": "avg_session_duration",
                "value": avg_duration,
            }
        )

        # ------------------------------------------------------------------
        # Metric 4: average_self_reported_engagement
        # ------------------------------------------------------------------
        avg_engagement = (
            group["self_reported_engagement"].mean()
            if not group["self_reported_engagement"].isna().all()
            else 0.0
        )
        logger.info(
            f"Computed avg_self_reported_engagement: {avg_engagement:.3f} for user {user_id}"
        )
        log_dict(
            {
                "event": "metric_computed",
                "user_id": user_id,
                "metric": "avg_self_reported_engagement",
                "value": avg_engagement,
            }
        )

        results.append(
            {
                "user_id": user_id,
                "sessions_per_week": sessions_per_week,
                "completion_rate": completion_rate,
                "avg_session_duration": avg_duration,
                "avg_self_reported_engagement": avg_engagement,
            }
        )

    return pd.DataFrame(results)


def extract_metrics(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
) -> None:
    """
    Read usage‑metadata, compute per‑user adherence metrics, write them to CSV,
    and emit detailed log entries for each computation step.

    Parameters
    ----------
    input_path : Union[str, Path]
        Path to the source CSV or JSON file containing raw usage metadata.
    output_path : Union[str, Path]
        Destination CSV file for the processed adherence metrics.
    """
    logger = get_logger(__name__)

    input_path = Path(input_path)
    output_path = Path(output_path)

    logger.info(f"Starting metric extraction from {input_path}")
    df_raw = _read_input(input_path)
    df_prepared = _prepare_dataframe(df_raw)

    logger.info("Computing per‑user adherence metrics")
    df_metrics = _compute_user_metrics(df_prepared, logger)

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_metrics.to_csv(output_path, index=False)
    logger.info(f"Wrote adherence metrics to {output_path}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract adherence metrics from usage‑metadata files."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to input CSV or JSON file containing usage metadata.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/adherence_metrics.csv"),
        help="Path to write the computed adherence metrics CSV.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry‑point for the CLI."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        extract_metrics(args.input, args.output)
    except Exception as exc:
        # Use the pipeline logger's error handling utilities if needed
        logger = get_logger(__name__)
        logger.error(f"Metric extraction failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()