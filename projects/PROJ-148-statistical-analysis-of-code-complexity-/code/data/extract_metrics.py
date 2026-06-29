"""
extract_metrics.py

Compute code complexity metrics for a collection of source files using the
``lizard`` library.

Expected input CSV
-------------------
The input CSV should contain at least one column that points to a source
file on disk.  By convention the column is named ``file_path`` but the
implementation also falls back to ``path`` if the former is missing.

Output CSV
----------
The output CSV contains the original columns plus the following metric
columns:

- ``cyclomatic_complexity`` – average cyclomatic complexity of all functions
  in the file (as reported by ``lizard``).
- ``loc`` – lines of code (non‑comment, non‑blank) – ``result.nloc``.
- ``token_count`` – total token count in the file.
- ``nesting_depth`` – maximum nesting depth across functions.
- ``halstead_volume`` – Halstead volume for the file.

Files that cannot be parsed by ``lizard`` are skipped and a warning is
emitted; this mirrors the fallback handling described in task T050.

Usage
-----
```bash
python -m data.extract_metrics <input_csv> <output_csv>
```

The module also provides a reusable ``extract_metrics`` function that can be
imported by other pipeline stages.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import List, Optional

import lizard
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)

METRIC_COLUMNS = [
    "cyclomatic_complexity",
    "loc",
    "token_count",
    "nesting_depth",
    "halstead_volume",
]


def _detect_path_column(df: pd.DataFrame) -> str:
    """Return the column name that holds the file path.

    The function prefers ``file_path`` and falls back to ``path``.  If
    neither column is present a ``ValueError`` is raised.
    """
    for col in ("file_path", "path"):
        if col in df.columns:
            return col
    raise ValueError(
        "Input DataFrame must contain a 'file_path' or 'path' column."
    )


def _compute_metrics_for_file(file_path: Path) -> Optional[dict]:
    """Run lizard on *file_path* and return a dict of metrics.

    If lizard raises an exception (e.g. unsupported language or malformed
    source) the function returns ``None`` and logs a warning.
    """
    try:
        result = lizard.analyze_file(str(file_path))
    except Exception as exc:  # pragma: no cover – defensive
        logger.warning(
            "Lizard failed to parse %s: %s – skipping this file.", file_path, exc
        )
        return None

    # ``result`` provides the needed attributes; we guard against missing
    # attributes to keep the function robust across lizard versions.
    metrics = {
        "cyclomatic_complexity": getattr(
            result, "average_cyclomatic_complexity", None
        ),
        "loc": getattr(result, "nloc", None),
        "token_count": getattr(result, "token_count", None),
        "nesting_depth": getattr(result, "max_nesting_depth", None),
        "halstead_volume": getattr(result, "halstead_volume", None),
    }
    return metrics


def extract_metrics(
    input_csv: str,
    output_csv: str,
    *,
    chunk_size: int = 10_000,
    skip_errors: bool = True,
) -> pd.DataFrame:
    """
    Compute complexity metrics for each source file listed in *input_csv*.

    Parameters
    ----------
    input_csv: str
        Path to the CSV that contains at least a ``file_path`` column.
    output_csv: str
        Destination CSV that will contain the original data plus the metric
        columns.
    chunk_size: int, optional
        Number of rows to process at once – useful for large datasets.
    skip_errors: bool, optional
        If ``True`` (default) rows whose files cannot be parsed are omitted
        from the final output; otherwise the function raises.

    Returns
    -------
    pandas.DataFrame
        The enriched DataFrame that was written to *output_csv*.
    """
    logger.info("Reading input CSV %s", input_csv)
    # Using pandas' iterator to stay memory‑friendly for huge inputs.
    iterator = pd.read_csv(input_csv, chunksize=chunk_size)

    enriched_chunks: List[pd.DataFrame] = []

    for chunk_idx, chunk in enumerate(iterator):
        logger.info("Processing chunk %d (%d rows)", chunk_idx + 1, len(chunk))
        path_col = _detect_path_column(chunk)

        # Prepare containers for metric values
        for metric in METRIC_COLUMNS:
            chunk[metric] = pd.NA

        for row_idx, row in chunk.iterrows():
            file_path = Path(row[path_col])
            if not file_path.is_file():
                msg = f"Source file not found: {file_path}"
                if skip_errors:
                    logger.warning(msg + " – skipping.")
                    continue
                else:
                    raise FileNotFoundError(msg)

            metrics = _compute_metrics_for_file(file_path)
            if metrics is None:
                if skip_errors:
                    continue
                else:
                    raise RuntimeError(f"Failed to compute metrics for {file_path}")

            for metric_name, value in metrics.items():
                chunk.at[row_idx, metric_name] = value

        enriched_chunks.append(chunk)

    if enriched_chunks:
        result_df = pd.concat(enriched_chunks, ignore_index=True)
    else:
        result_df = pd.DataFrame()  # empty

    logger.info("Writing enriched data to %s", output_csv)
    # Ensure the parent directory exists.
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_csv, index=False)

    logger.info("Metric extraction completed successfully.")
    return result_df


def main() -> None:
    """Entry‑point for ``python -m data.extract_metrics``."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Compute code complexity metrics using lizard."
    )
    parser.add_argument(
        "input_csv",
        type=str,
        help="CSV file containing at least a 'file_path' column.",
    )
    parser.add_argument(
        "output_csv",
        type=str,
        help="Path where the enriched CSV with metrics will be written.",
    )
    args = parser.parse_args()

    try:
        extract_metrics(args.input_csv, args.output_csv)
    except Exception as exc:  # pragma: no cover
        logger.error("Metric extraction failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()