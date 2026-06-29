"""Label bug‑fix vs. non‑bug‑fix units.

This module provides a small utility that reads a CSV file containing
commit information (at least a ``message`` column), applies a heuristic
to decide whether the commit corresponds to a bug‑fix, and writes the
enriched data back to disk with a new ``bug_label`` column (``1`` for
bug‑fix, ``0`` otherwise).

The heuristic is deliberately simple – it looks for common bug‑fix
keywords in the commit message (case‑insensitive).  The function is
pure and can be unit‑tested without touching the file system; the
``main`` entry‑point provides a CLI for the data‑pipeline.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

from utils.logging import get_logger

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
# CLI entry point
# ----------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Label bug‑fix commits in a CSV file."
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to the input CSV file containing at least a 'message' column.",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Path where the CSV with the added 'bug_label' column will be written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point.

    Reads *input_path*, labels bug‑fix commits, and writes the result to
    *output_path*.
    """
    args = _parse_args(argv)

    logger.info("Reading input CSV from %s", args.input_path)
    try:
        df = pd.read_csv(args.input_path)
    except Exception as exc:
        logger.error("Failed to read input CSV: %s", exc)
        sys.exit(1)

    try:
        labeled_df = label_bug_fixes(df)
    except Exception as exc:
        logger.error("Failed to label bug fixes: %s", exc)
        sys.exit(1)

    logger.info("Writing labeled CSV to %s", args.output_path)
    try:
        # Ensure the parent directory exists
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        labeled_df.to_csv(args.output_path, index=False, quoting=csv.QUOTE_ALL)
    except Exception as exc:
        logger.error("Failed to write output CSV: %s", exc)
        sys.exit(1)

    logger.info("Labeling complete. %d rows processed.", len(labeled_df))


if __name__ == "__main__":
    main()
