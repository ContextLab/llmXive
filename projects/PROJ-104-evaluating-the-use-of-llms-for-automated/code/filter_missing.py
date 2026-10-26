"""Filter commit pairs to exclude rows with missing documentation diffs.

This script implements Task T016: it loads the raw commit‑pair CSV,
removes any rows where the ``doc_diff`` field is empty, null, or consists
only of whitespace, and writes the filtered result to
``data/processed/filtered_commit_pairs.csv``.

The module provides a ``filter_missing`` function that can be called
programmatically and a ``main`` entry point for CLI usage.

The script uses the project's path helpers (``llmxive_toolkit.paths``)
to locate input and output files and logs progress via the shared logger.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _load_raw_csv() -> pd.DataFrame:
    """Load the raw ``commit_pairs.csv`` as a DataFrame with all columns as strings."""
    raw_path = paths.data("raw", "commit_pairs.csv")
    if not raw_path.is_file():
        log.error("Raw commit pairs file not found at %s", raw_path)
        raise FileNotFoundError(raw_path)
    # Load everything as string to avoid type coercion issues.
    df = pd.read_csv(raw_path, dtype=str)
    log.debug("Loaded %d rows from %s", len(df), raw_path)
    return df

def _filter_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with rows where ``doc_diff`` is empty or null removed."""
    if "doc_diff" not in df.columns:
        log.error("Column 'doc_diff' missing from input CSV")
        raise KeyError("doc_diff column not found")
    # Treat NaN, empty strings, or strings that are only whitespace as missing.
    mask_not_null = df["doc_diff"].notna()
    mask_not_blank = df["doc_diff"].astype(str).str.strip().astype(bool)
    filtered = df[mask_not_null & mask_not_blank].copy()
    log.info(
        "Filtered commit pairs: %d rows kept, %d rows removed",
        len(filtered),
        len(df) - len(filtered),
    )
    return filtered

def _write_filtered_csv(df: pd.DataFrame) -> Path:
    """Write the filtered DataFrame to the processed folder and return the path."""
    out_path = paths.data("processed", "filtered_commit_pairs.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    log.info("Wrote filtered commit pairs to %s", out_path)
    return out_path

def filter_missing() -> Path:
    """Execute the full filtering pipeline and return the output path."""
    raw_df = _load_raw_csv()
    filtered_df = _filter_df(raw_df)
    return _write_filtered_csv(filtered_df)

def main(argv: list[str] | None = None) -> int:
    """CLI entry point – runs the filter and exits with status 0 on success."""
    # ``argv`` is accepted for compatibility with the project's convention,
    # but the function does not use any command‑line arguments.
    try:
        filter_missing()
        return 0
    except Exception as e:  # pragma: no cover – unexpected errors are logged.
        log.exception("Filtering failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
