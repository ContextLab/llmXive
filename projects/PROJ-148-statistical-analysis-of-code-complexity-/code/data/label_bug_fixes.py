"""Label bug‑fix vs. non‑bug‑fix functions.

This module reads a CSV of commit metadata and a CSV of extracted code
metrics, determines which commits are bug‑fixes using a simple keyword
heuristic, and maps those commits to the functions they touched.  The
result is a CSV with one row per function and a binary ``bug_label`` column
(``1`` for bug‑fix, ``0`` otherwise).

The implementation is deliberately deterministic:
* function identifiers are derived from a SHA‑256 hash of the
  ``file_path`` and ``function_name``.
* random sampling of untouched functions uses a fixed seed from the
  project's configuration.
* the script aborts with a non‑zero exit code if no bug‑fix commits are
  found (fail loudly as required).

The CLI matches the arguments used in ``quickstart.md``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from utils.logging import get_logger
from utils.config import get_seed

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Heuristic utilities
# ----------------------------------------------------------------------


BUG_FIX_KEYWORDS: Iterable[str] = (
    "fix",
    "bug",
    "bugfix",
    "patch",
    "error",
    "issue",
    "resolve",
    "correct",
)


def is_bug_fix(message: str) -> bool:
    """Return ``True`` if *message* looks like a bug‑fix commit.

    The check is performed by searching for any of the keywords in
    :data:`BUG_FIX_KEYWORDS` (case‑insensitive).  A simple ``in`` test is
    sufficient for the MVP and satisfies the contract tests that only
    require a binary ``bug_label`` column.
    """
    if not isinstance(message, str):
        return False
    lowered = message.lower()
    return any(keyword in lowered for keyword in BUG_FIX_KEYWORDS)


# ----------------------------------------------------------------------
# Core labeling logic
# ----------------------------------------------------------------------


def label_bug_fixes(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``bug_label`` column to *df*.

    Parameters
    ----------
    df: pandas.DataFrame
        Must contain a ``message`` column with the commit message text.

    Returns
    -------
    pandas.DataFrame
        A copy of *df* with an additional integer column ``bug_label``.
    """
    if "message" not in df.columns:
        raise KeyError("Input DataFrame must contain a 'message' column.")

    logger.debug("Labeling %d rows for bug‑fix detection.", len(df))
    df = df.copy()
    df["bug_label"] = df["message"].apply(lambda m: 1 if is_bug_fix(m) else 0)
    return df


# ----------------------------------------------------------------------
# Helper utilities for the function‑level mapping
# ----------------------------------------------------------------------


def _extract_project_id(file_path: str) -> str:
    """Extract the project identifier from a repository‑relative path.

    The repository layout created by ``download_gh.py`` places each project
    under ``data/raw/<project_id>/...``.  This helper extracts the
    ``<project_id>`` component; if the pattern cannot be found ``unknown``
    is returned.
    """
    parts = Path(file_path).parts
    if "raw" in parts:
        idx = parts.index("raw")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return "unknown"


def _function_name_from_path(file_path: str) -> str:
    """Derive a sensible function name from a file path.

    In the absence of true per‑function information we fall back to the
    filename (without extension).  This provides a stable, reproducible
    identifier that downstream steps can use.
    """
    return Path(file_path).stem


def _make_function_id(file_path: str, function_name: str) -> str:
    """Create a deterministic ``function_id`` from file and function name."""
    raw = f"{file_path}::{function_name}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Map bug‑fix commits to functions and emit a labeled CSV."
    )
    parser.add_argument(
        "--input",
        dest="commits_path",
        type=Path,
        required=True,
        help="Path to the commits CSV (must contain at least a 'message' column).",
    )
    parser.add_argument(
        "--metrics",
        dest="metrics_path",
        type=Path,
        required=True,
        help="Path to the metrics CSV (must contain a 'file_path' column).",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        required=True,
        help="Path where the labeled CSV will be written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point.

    Reads commit metadata and metric information, produces a function‑level
    CSV with a ``bug_label`` column, and writes it to *output_path*.
    """
    args = _parse_args(argv)

    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    logger.info("Reading commits from %s", args.commits_path)
    try:
        commits_df = pd.read_csv(args.commits_path)
    except Exception as exc:
        logger.error("Failed to read commits CSV: %s", exc)
        sys.exit(1)

    logger.info("Reading metrics from %s", args.metrics_path)
    try:
        metrics_df = pd.read_csv(args.metrics_path)
    except Exception as exc:
        logger.error("Failed to read metrics CSV: %s", exc)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Validate required columns
    # ------------------------------------------------------------------
    required_commit_cols = {"message", "file_path"}
    missing_commits = required_commit_cols - set(commits_df.columns)
    if missing_commits:
        logger.error("Commits CSV missing required columns: %s", missing_commits)
        sys.exit(1)

    if "file_path" not in metrics_df.columns:
        logger.error("Metrics CSV must contain a 'file_path' column.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Determine which commits are bug‑fixes
    # ------------------------------------------------------------------
    commits_df = label_bug_fixes(commits_df)

    bug_fix_commits = commits_df[commits_df["bug_label"] == 1]
    if bug_fix_commits.empty:
        logger.error("No bug‑fix commits found – aborting as required.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Map bug‑fix commits to functions (approximation)
    # ------------------------------------------------------------------
    # For each bug‑fix commit we consider *all* functions reported in the
    # metrics CSV that belong to the same file.  This is a conservative
    # approach that guarantees at least one positive row per affected file.
    positive_rows = []
    for _, commit in bug_fix_commits.iterrows():
        file_path = commit["file_path"]
        matching_metrics = metrics_df[metrics_df["file_path"] == file_path]

        if matching_metrics.empty:
            # No metric entry for this file – skip but continue processing.
            logger.warning("No metric entry for file %s referenced by a bug‑fix commit.", file_path)
            continue

        for _, metric in matching_metrics.iterrows():
            func_name = _function_name_from_path(metric["file_path"])
            func_id = _make_function_id(metric["file_path"], func_name)
            pos_row = {
                "function_id": func_id,
                "project_id": _extract_project_id(metric["file_path"]),
                "file_path": metric["file_path"],
                "function_name": func_name,
                "start_line": 0,                     # placeholder – real start line not available yet
                "end_line": 0,                       # placeholder – real end line not available yet
                "bug_label": 1,
            }
            positive_rows.append(pos_row)

    if not positive_rows:
        logger.error("Bug‑fix commits existed but no matching metric rows were found.")
        sys.exit(1)

    positive_df = pd.DataFrame(positive_rows)

    # ------------------------------------------------------------------
    # Sample untouched functions for the negative class
    # ------------------------------------------------------------------
    # Functions that were *not* touched by any bug‑fix commit are taken from
    # the metrics CSV after removing the positive ones.
    touched_file_paths = set(positive_df["file_path"])
    untouched_metrics = metrics_df[~metrics_df["file_path"].isin(touched_file_paths)]

    # Determine sample size – we use the same number of negatives as positives
    # (or all available if fewer).
    seed = get_seed()
    rng = np.random.default_rng(seed)
    n_negative = min(len(positive_df), len(untouched_metrics))
    if n_negative == 0:
        logger.warning("No untouched functions available for negative sampling.")
        negative_df = pd.DataFrame(columns=positive_df.columns)
    else:
        sampled = untouched_metrics.sample(n=n_negative, random_state=seed)
        negative_rows = []
        for _, metric in sampled.iterrows():
            func_name = _function_name_from_path(metric["file_path"])
            func_id = _make_function_id(metric["file_path"], func_name)
            neg_row = {
                "function_id": func_id,
                "project_id": _extract_project_id(metric["file_path"]),
                "file_path": metric["file_path"],
                "function_name": func_name,
                "start_line": 0,
                "end_line": 0,
                "bug_label": 0,
            }
            negative_rows.append(neg_row)
        negative_df = pd.DataFrame(negative_rows)

    # ------------------------------------------------------------------
    # Concatenate and write output
    # ------------------------------------------------------------------
    final_df = pd.concat([positive_df, negative_df], ignore_index=True)

    logger.info("Writing %d labeled rows to %s", len(final_df), args.output_path)
    try:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(args.output_path, index=False, quoting=csv.QUOTE_ALL)
    except Exception as exc:
        logger.error("Failed to write output CSV: %s", exc)
        sys.exit(1)

    logger.info("Labeling complete. %d rows processed (positive: %d, negative: %d).",
                len(final_df), len(positive_df), len(negative_df))


if __name__ == "__main__":
    main()