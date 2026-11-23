"""
src.features.usage_metrics
--------------------------

This module aggregates weekly AI‑companion usage metrics for each matched user.
It computes:

* ``usage_frequency`` – the number of interaction records (comments) a user made
  within a given calendar week.
* ``session_duration`` – the total minutes spent in sessions during that week.
  A *session* is defined as a series of consecutive interactions where the gap
  between successive timestamps does not exceed 24 hours.  The duration of each
  session is capped at 24 hours (1440 minutes) before being summed for the week.

The script reads the matched user identifiers from
``data/processed/matched_users.parquet`` and the raw Pushshift logs from
``data/raw/pushshift_logs.parquet``.  It writes the aggregated weekly metrics
to ``data/processed/usage_metrics.parquet``.

The implementation is deliberately defensive – it logs useful information,
validates required columns, and raises clear errors if expected inputs are
missing.  This behaviour is exercised by the unit test
``tests/unit/test_usage_metrics.py`` which checks that the resulting records
contain non‑negative integer counts and that no single session exceeds the
24‑hour cap.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _hash_username(username: str) -> str:
    """
    Deterministic SHA‑256 hash of a raw Reddit username (UTF‑8, no salt).

    Parameters
    ----------
    username: str
        The raw Reddit username.

    Returns
    -------
    str
        64‑character hexadecimal hash.
    """
    if not isinstance(username, str):
        raise TypeError("username must be a string")
    return hashlib.sha256(username.encode("utf-8")).hexdigest()


def _load_matched_user_ids(matched_path: Path) -> pd.Index:
    """
    Load the matched user identifiers.

    Parameters
    ----------
    matched_path: Path
        Path to ``matched_users.parquet``.

    Returns
    -------
    pd.Index
        Index of ``user_id`` values.
    """
    if not matched_path.exists():
        raise FileNotFoundError(f"Matched users file not found: {matched_path}")

    df = pd.read_parquet(matched_path, columns=["user_id"])
    return df["user_id"]


def _load_pushshift_logs(pushshift_path: Path) -> pd.DataFrame:
    """
    Load the raw Pushshift comment logs.

    The function expects at least the following columns:
    ``author`` (raw Reddit username) and ``created_utc`` (epoch seconds).

    Parameters
    ----------
    pushshift_path: Path
        Path to ``pushshift_logs.parquet``.

    Returns
    -------
    pd.DataFrame
        DataFrame with the raw logs.
    """
    if not pushshift_path.exists():
        raise FileNotFoundError(f"Pushshift logs file not found: {pushshift_path}")

    df = pd.read_parquet(pushshift_path, columns=["author", "created_utc"])
    if "author" not in df.columns or "created_utc" not in df.columns:
        raise ValueError(
            "Pushshift logs must contain 'author' and 'created_utc' columns"
        )
    # Convert epoch seconds to timezone‑aware UTC datetime
    df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s", utc=True)
    return df


def _assign_user_hashes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a deterministic ``author_hash`` column to the Pushshift logs.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing an ``author`` column.

    Returns
    -------
    pd.DataFrame
        Same DataFrame with an additional ``author_hash`` column.
    """
    df = df.copy()
    df["author_hash"] = df["author"].apply(_hash_username)
    return df


def _filter_to_matched_users(df: pd.DataFrame, matched_ids: pd.Index) -> pd.DataFrame:
    """
    Keep only rows whose ``author_hash`` appears in the matched user set.

    Parameters
    ----------
    df: pd.DataFrame
        Pushshift logs with an ``author_hash`` column.
    matched_ids: pd.Index
        Set of hashed user identifiers.

    Returns
    -------
    pd.DataFrame
        Filtered logs.
    """
    return df[df["author_hash"].isin(matched_ids)].copy()


def _week_start(dt: pd.Timestamp) -> pd.Timestamp:
    """
    Return the Monday (start of ISO week) for a given timestamp.

    Parameters
    ----------
    dt: pd.Timestamp

    Returns
    -------
    pd.Timestamp
    """
    # ISO week starts on Monday
    return (dt - pd.Timedelta(days=dt.weekday())).normalize()


def _compute_sessions(timestamps: pd.Series) -> int:
    """
    Compute the total session duration (in minutes) for a sorted series
    of timestamps belonging to a single user within a single week.

    Sessions are groups of consecutive timestamps where the gap between
    successive timestamps does not exceed 24 hours.  The duration of each
    session (last – first) is capped at 1440 minutes before summation.

    Parameters
    ----------
    timestamps: pd.Series
        Sorted UTC timestamps for one user‑week.

    Returns
    -------
    int
        Total session duration in minutes (capped per session).
    """
    if timestamps.empty:
        return 0

    # Ensure timestamps are sorted
    timestamps = timestamps.sort_values()

    total_minutes = 0
    session_start = timestamps.iloc[0]
    session_end = timestamps.iloc[0]

    max_gap = timedelta(hours=24)

    for ts in timestamps.iloc[1:]:
        if ts - session_end <= max_gap:
            # Same session – extend the end
            session_end = ts
        else:
            # Close current session
            duration = (session_end - session_start).total_seconds() / 60
            total_minutes += min(duration, 1440)  # cap at 24 h
            # Start a new session
            session_start = ts
            session_end = ts

    # Add the final session
    duration = (session_end - session_start).total_seconds() / 60
    total_minutes += min(duration, 1440)

    # Return integer minutes (round down)
    return int(total_minutes)


def _aggregate_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce weekly usage metrics per user.

    The resulting DataFrame has columns:
    ``user_id``, ``week_start`` (date), ``usage_frequency`` (int),
    ``session_duration`` (int minutes).

    Parameters
    ----------
    df: pd.DataFrame
        Pushshift logs filtered to matched users, with columns:
        ``author_hash`` and ``created_utc`` (datetime).

    Returns
    -------
    pd.DataFrame
        Aggregated weekly usage metrics.
    """
    # Derive week start (Monday) for each record
    df = df.copy()
    df["week_start"] = df["created_utc"].apply(_week_start)

    # Group by user and week
    grouped = df.groupby(["author_hash", "week_start"])

    records = []
    for (user_hash, week_start_dt), group in grouped:
        usage_frequency = int(group.shape[0])
        session_duration = _compute_sessions(group["created_utc"])
        records.append(
            {
                "user_id": user_hash,
                "week_start": week_start_dt.date(),
                "usage_frequency": usage_frequency,
                "session_duration": session_duration,
            }
        )

    result = pd.DataFrame(records)
    # Ensure integer dtypes
    result["usage_frequency"] = result["usage_frequency"].astype("int64")
    result["session_duration"] = result["session_duration"].astype("int64")
    return result


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def compute_usage_metrics(
    matched_path: Path,
    pushshift_path: Path,
    output_path: Path,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    """
    Compute and persist weekly usage metrics.

    Parameters
    ----------
    matched_path: Path
        Path to ``matched_users.parquet``.
    pushshift_path: Path
        Path to ``pushshift_logs.parquet``.
    output_path: Path
        Destination for the aggregated parquet file.
    logger: logging.Logger, optional
        Logger instance; if omitted a module‑level logger is created.

    Returns
    -------
    pd.DataFrame
        The aggregated metrics DataFrame (also written to disk).
    """
    if logger is None:
        logger = get_logger(__name__)

    logger.info("Loading matched user identifiers")
    matched_ids = _load_matched_user_ids(matched_path)

    logger.info("Loading raw Pushshift logs")
    raw_logs = _load_pushshift_logs(pushshift_path)

    logger.info("Hashing usernames in Pushshift logs")
    hashed_logs = _assign_user_hashes(raw_logs)

    logger.info("Filtering logs to matched users")
    filtered = _filter_to_matched_users(hashed_logs, matched_ids)

    if filtered.empty:
        logger.warning("No Pushshift records found for matched users")
        # Still write an empty file with the expected schema
        empty_df = pd.DataFrame(
            columns=[
                "user_id",
                "week_start",
                "usage_frequency",
                "session_duration",
            ]
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        empty_df.to_parquet(output_path, index=False)
        return empty_df

    logger.info("Aggregating weekly usage metrics")
    weekly_metrics = _aggregate_weekly(filtered)

    logger.info(
        f"Writing {len(weekly_metrics)} weekly usage records to {output_path}"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    weekly_metrics.to_parquet(output_path, index=False)

    return weekly_metrics


def main() -> None:
    """
    Entry‑point used by developers and the test suite.

    The function resolves canonical project paths via ``llmxive_toolkit.paths``,
    invokes :func:`compute_usage_metrics`, and logs progress.
    """
    logger = get_logger(__name__)

    # Resolve canonical locations
    matched_path = paths.data("processed", "matched_users.parquet")
    pushshift_path = paths.data("raw", "pushshift_logs.parquet")
    output_path = paths.data("processed", "usage_metrics.parquet")

    compute_usage_metrics(
        matched_path=matched_path,
        pushshift_path=pushshift_path,
        output_path=output_path,
        logger=logger,
    )
    logger.info("Usage‑metrics aggregation completed successfully.")


if __name__ == "__main__":
    main()