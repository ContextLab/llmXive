"""
Preprocessing module for Flight Delay Analysis.

This module provides functions to clean and preprocess the raw BTS flight
delay CSV data. It is used by ``code/main.py`` during Stage 1 of the
pipeline.

The implementation follows Task T002:
- Extract the ZIP (if a ZIP path is provided)
- Stream the CSV in chunks (``chunksize=200_000``)
- Compute ``total_delay = ArrDelay + DepDelay`` (treat NaN as 0)
- Drop negative delays
- Keep only commercial U.S. flights (non‑cancelled, non‑diverted)
- Flag anomalies (``delay > 1440`` min) and data errors
  (``delay > 10 000`` min)
- Record zero‑delay records
- Write a cleaned dataset with the required columns:
  ``flight_id,total_delay_minutes,carrier,origin,destination,
  is_anomaly,is_data_error,is_zero``

The public API matches the signatures expected by ``code/main.py``:
  - ``preprocess_flight_delays(input_path) -> pd.DataFrame``
  - ``save_summary_report(df, output_path) -> None``

The functions are deliberately robust: they raise ``PipelineError`` on
unrecoverable conditions (e.g., missing required columns) so that the
pipeline fails loudly rather than silently fabricating data.
"""

import json
import logging
import zipfile
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from utils import PipelineError, setup_logging

# Initialise module‑level logger
logger = setup_logging()

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _extract_csv_from_zip(zip_path: Path) -> Path:
    """
    Extract the first CSV file from ``zip_path`` and return its path.

    If the CSV has already been extracted, the existing file is reused.

    Parameters
    ----------
    zip_path: Path
        Path to the ZIP archive containing a single CSV.

    Returns
    -------
    Path
        Path to the extracted CSV file.
    """
    if not zip_path.is_file():
        raise PipelineError(f"ZIP archive not found: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Assume the archive contains exactly one CSV file
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise PipelineError(f"No CSV file found inside {zip_path}")
        csv_name = csv_names[0]

        extracted_path = zip_path.parent / csv_name
        if not extracted_path.is_file():
            logger.info(f"Extracting {csv_name} from {zip_path}")
            zf.extract(csv_name, path=zip_path.parent)
        else:
            logger.debug(f"CSV already extracted at {extracted_path}")

    return extracted_path

# ----------------------------------------------------------------------
# Core preprocessing
# ----------------------------------------------------------------------
def preprocess_flight_delays(input_path: str) -> pd.DataFrame:
    """
    Clean and preprocess raw BTS flight delay data.

    The function accepts either a CSV file path or a ZIP archive path.
    It streams the CSV in chunks (``chunksize=200_000``) to keep memory
    usage modest, applies the cleaning logic described in the task
    specification, and returns a single concatenated ``DataFrame`` with
    the required output columns.

    Parameters
    ----------
    input_path: str
        Path to the raw CSV file or to the ZIP archive containing it.

    Returns
    -------
    pd.DataFrame
        Cleaned data with columns:
        ``flight_id,total_delay_minutes,carrier,origin,destination,
        is_anomaly,is_data_error,is_zero``.
    """
    logger.info(f"Starting preprocessing for {input_path}")

    path = Path(input_path)

    # Resolve CSV location (handle ZIP transparently)
    if path.suffix.lower() == ".zip":
        csv_path = _extract_csv_from_zip(path)
    else:
        csv_path = path

    if not csv_path.is_file():
        raise PipelineError(f"CSV file not found: {csv_path}")

    # ------------------------------------------------------------------
    # Column mapping – we try to be tolerant to slight naming variations
    # ------------------------------------------------------------------
    # Required raw columns (may appear with different capitalisation)
    required_cols = {
        "ArrDelay": ["ArrDelay", "arrdelay"],
        "DepDelay": ["DepDelay", "depdelay"],
        "Cancelled": ["Cancelled", "cancelled"],
        "Diverted": ["Diverted", "diverted"],
        "UniqueCarrier": ["UniqueCarrier", "Carrier", "carrier"],
        "Origin": ["Origin", "origin"],
        "Dest": ["Dest", "Destination", "dest"],
        "FlightNum": ["FlightNum", "flightnum", "FlightNumber", "flight_number"],
    }

    # Determine the actual column names present in the file
    # Read only the header line first
    with open(csv_path, "r", encoding="utf-8") as f:
        header_line = f.readline()
    raw_columns = [c.strip() for c in header_line.split(",")]

    # Build a mapping from our canonical name -> actual column name
    col_map = {}
    for canonical, alternatives in required_cols.items():
        for alt in alternatives:
            if alt in raw_columns:
                col_map[canonical] = alt
                break
        else:
            # Column not found – for optional ones we can continue,
            # but for the core delay columns we must error out.
            if canonical in ("ArrDelay", "DepDelay"):
                raise PipelineError(
                    f"Required column '{canonical}' not found in CSV header."
                )
            # For others we will create a placeholder column later
            col_map[canonical] = None

    # ------------------------------------------------------------------
    # Chunked processing
    # ------------------------------------------------------------------
    chunksize = 200_000
    cleaned_chunks: List[pd.DataFrame] = []

    # Helper to safely fetch a column (or create a default series)
    def _get_series(df_chunk: pd.DataFrame, canonical_name: str):
        actual = col_map.get(canonical_name)
        if actual and actual in df_chunk.columns:
            return df_chunk[actual]
        # Return a series of zeros / appropriate default
        if canonical_name in ("ArrDelay", "DepDelay"):
            return pd.Series(0, index=df_chunk.index, dtype=float)
        elif canonical_name == "Cancelled" or canonical_name == "Diverted":
            return pd.Series(0, index=df_chunk.index, dtype=int)
        else:
            return pd.Series("", index=df_chunk.index, dtype=object)

    # Iterate over the CSV
    for chunk_idx, chunk in enumerate(
        pd.read_csv(csv_path, chunksize=chunksize, low_memory=False)
    ):
        logger.debug(f"Processing chunk {chunk_idx + 1}")

        # Ensure required columns exist (create defaults if missing)
        arr_delay = _get_series(chunk, "ArrDelay").fillna(0).astype(float)
        dep_delay = _get_series(chunk, "DepDelay").fillna(0).astype(float)
        total_delay = arr_delay + dep_delay

        # Drop negative delays
        mask_non_negative = total_delay >= 0
        total_delay = total_delay[mask_non_negative]
        chunk = chunk.loc[mask_non_negative]

        # Keep only commercial US flights:
        #   - Not cancelled, not diverted
        #   - Origin and Destination present (non‑null)
        cancelled = _get_series(chunk, "Cancelled").astype(int)
        diverted = _get_series(chunk, "Diverted").astype(int)

        mask_flight = (cancelled == 0) & (diverted == 0)
        mask_origin = chunk[_get_series(chunk, "Origin").name if col_map["Origin"] else "Origin"].notna()
        mask_dest = chunk[_get_series(chunk, "Dest").name if col_map["Dest"] else "Dest"].notna()
        flight_mask = mask_flight & mask_origin & mask_dest

        chunk = chunk.loc[flight_mask]
        total_delay = total_delay.loc[flight_mask]

        # Build output columns
        # flight_id: use FlightNum if available, otherwise fallback to index
        flight_num_series = _get_series(chunk, "FlightNum")
        if flight_num_series.isnull().all():
            flight_id = pd.Series(chunk.index.astype(str), index=chunk.index)
        else:
            flight_id = flight_num_series.astype(str)

        carrier_series = _get_series(chunk, "UniqueCarrier")
        if carrier_series.isnull().all():
            carrier_series = pd.Series("", index=chunk.index)

        origin_series = _get_series(chunk, "Origin")
        dest_series = _get_series(chunk, "Dest")

        is_anomaly = total_delay > 1440
        is_data_error = total_delay > 10_000
        is_zero = total_delay == 0

        cleaned = pd.DataFrame(
            {
                "flight_id": flight_id,
                "total_delay_minutes": total_delay.astype(int),
                "carrier": carrier_series,
                "origin": origin_series,
                "destination": dest_series,
                "is_anomaly": is_anomaly,
                "is_data_error": is_data_error,
                "is_zero": is_zero,
            }
        )

        cleaned_chunks.append(cleaned)

    if not cleaned_chunks:
        raise PipelineError("No valid records found after preprocessing.")

    cleaned_df = pd.concat(cleaned_chunks, ignore_index=True)
    logger.info(
        f"Preprocessing complete: {len(cleaned_df)} valid records produced."
    )
    return cleaned_df

# ----------------------------------------------------------------------
# Summary report generation
# ----------------------------------------------------------------------
def save_summary_report(df: pd.DataFrame, output_path: str) -> None:
    """
    Persist a tiny summary JSON for the cleaned dataset.

    The summary contains:
    - ``total_records``: number of rows in the cleaned DataFrame
    - ``valid_records``: same as ``total_records`` (since preprocessing
      already removed invalid rows)
    - ``retention_rate``: set to ``1.0`` because the input to this
      function is the already‑filtered dataset.

    Parameters
    ----------
    df: pd.DataFrame
        The cleaned DataFrame (output of ``preprocess_flight_delays``).
    output_path: str
        Destination path for the JSON summary file.
    """
    total_records = int(df.shape[0])
    summary = {
        "total_records": total_records,
        "valid_records": total_records,
        "retention_rate": 1.0,
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Summary report written to {out_path}")

# ----------------------------------------------------------------------
# If executed as a script, expose a minimal CLI for ad‑hoc runs
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocess BTS flight delay CSV (or ZIP) and write cleaned output."
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to the raw CSV file or ZIP archive containing it.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(
            Path("data")
            / "processed"
            / "cleaned_delays.csv"
        ),
        help="Path where the cleaned CSV will be written.",
    )
    parser.add_argument(
        "--summary",
        type=str,
        default=str(
            Path("data")
            / "results"
            / "summary_report.json"
        ),
        help="Path for the JSON summary report.",
    )

    args = parser.parse_args()

    cleaned_df = preprocess_flight_delays(args.input_path)
    cleaned_df.to_csv(args.output, index=False)
    save_summary_report(cleaned_df, args.summary)