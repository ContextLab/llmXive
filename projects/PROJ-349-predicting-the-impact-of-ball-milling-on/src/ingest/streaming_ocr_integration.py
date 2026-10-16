"""
Streaming OCR Integration Module
--------------------------------

This module provides utilities to integrate OCR fallback processing into the
streaming ingestion pipeline.  It operates on a pandas ``DataFrame`` (or an
iterator of chunked DataFrames) and attempts to extract particle‑size
distribution (PSD) metrics from image files flagged as containing unstructured
PSD data.

The implementation is deliberately defensive:
  * It only attempts OCR when a column named ``psd_image_path`` exists and
    contains a non‑null value.
  * OCR is performed via the internal helpers in ``src.ingest.ocr_extractor``.
  * If OCR fails (e.g., missing Tesseract, unreadable file), the error is
    logged and the row is left unchanged – the pipeline continues without
    fabricating data.
  * Extracted numeric values are mapped to the standard PSD columns
    ``d10``, ``d50``, ``d90``.  Missing values remain ``NaN`` and will be
    handled later by the imputation stage.

The module is exercised by the integration test
``tests/integration/test_streaming_ocr_integration.py``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

# Import the internal OCR helpers.  They are deliberately prefixed with an
# underscore but are part of the public contract of the ``ocr_extractor``
# module for this project.
from src.ingest.ocr_extractor import (
    _attempt_ocr_on_image,
    _extract_numbers_from_text,
)
from src.exceptions import DataIngestionError

# Project‑wide logger – respects the standard ``llmxive_toolkit`` configuration.
log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def _process_row(row: pd.Series) -> pd.Series:
    """
    Process a single row, attempting OCR extraction if an image path is
    present.

    Parameters
    ----------
    row : pd.Series
        A single record from the ingestion stream.

    Returns
    -------
    pd.Series
        The (potentially) enriched row.  New columns ``d10``, ``d50`` and
        ``d90`` are added when OCR succeeds; otherwise the original values
        are left untouched (they may be ``NaN``).
    """
    image_path = row.get("psd_image_path")
    if pd.isna(image_path):
        # No image to process – nothing to do.
        return row

    try:
        img_path = Path(image_path)
        if not img_path.is_file():
            raise DataIngestionError(f"PSD image not found: {img_path}")

        # ------------------------------------------------------------------
        # OCR extraction
        # ------------------------------------------------------------------
        # ``_attempt_ocr_on_image`` returns the raw textual content of the image.
        # It may raise ``DataIngestionError`` if OCR cannot be performed.
        raw_text = _attempt_ocr_on_image(str(img_path))

        # ``_extract_numbers_from_text`` parses the raw OCR string and returns
        # a mapping of metric names to numeric values (e.g. {"d10": 12.3,
        # "d50": 45.6, "d90": 78.9}).  If the parser cannot find a metric it
        # simply omits that key.
        numbers = _extract_numbers_from_text(raw_text)

        # Populate the standard PSD columns if they are present in the mapping.
        for metric in ("d10", "d50", "d90"):
            if metric in numbers:
                row[metric] = numbers[metric]

    except DataIngestionError as exc:
        # The pipeline must never fail because OCR failed on a single row.
        # We log the incident and continue – downstream imputation will handle
        # missing values.
        log.warning("OCR fallback failed for row %s: %s", row.get("experiment_id"), exc)
    except Exception as exc:  # pragma: no cover – unexpected errors
        # Unexpected exceptions are also logged but do not abort the stream.
        log.error(
            "Unexpected error during OCR processing for row %s: %s",
            row.get("experiment_id"),
            exc,
            exc_info=True,
        )
    return row

def stream_with_ocr(
    df_iter: Iterable[pd.DataFrame],
) -> pd.DataFrame:
    """
    Apply OCR fallback processing to an iterable of DataFrames (e.g. a
    streaming CSV reader).

    Parameters
    ----------
    df_iter : Iterable[pd.DataFrame]
        An iterator yielding chunked DataFrames.

    Returns
    -------
    pd.DataFrame
        A single concatenated DataFrame with OCR‑derived PSD columns added.
    """
    processed_chunks = []
    for chunk in df_iter:
        # Ensure we are working on a copy to avoid SettingWithCopy warnings.
        chunk = chunk.copy()
        # Apply row‑wise processing.
        chunk = chunk.apply(_process_row, axis=1)
        processed_chunks.append(chunk)

    if processed_chunks:
        return pd.concat(processed_chunks, ignore_index=True)
    else:
        # Return an empty DataFrame with the expected columns if the iterator
        # yields nothing.
        return pd.DataFrame(columns=["d10", "d50", "d90"])

# ----------------------------------------------------------------------
# CLI entry point (convenient for manual debugging)
# ----------------------------------------------------------------------
def main() -> int:
    """
    Simple command‑line interface that reads a CSV file (optionally streamed
    via ``chunksize``) and writes the OCR‑enriched result to ``stdout`` as CSV.

    Usage
    -----
    ``python -m src.ingest.streaming_ocr_integration <input.csv> [--chunksize N]``

    Returns
    -------
    int
        Exit code (0 on success).
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Stream a CSV and apply OCR fallback for flagged PSD images."
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to the input CSV file containing a 'psd_image_path' column.",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=1000,
        help="Number of rows per chunk when streaming the CSV (default: 1000).",
    )
    args = parser.parse_args()

    if not args.input_csv.is_file():
        log.error("Input CSV not found: %s", args.input_csv)
        return 1

    # Stream the CSV in chunks to keep memory usage low.
    df_iterator = pd.read_csv(args.input_csv, chunksize=args.chunksize)
    enriched_df = stream_with_ocr(df_iterator)

    # Write the result to stdout so the caller can redirect as needed.
    enriched_df.to_csv(sys.stdout, index=False)
    return 0

if __name__ == "__main__":
    sys.exit(main())
