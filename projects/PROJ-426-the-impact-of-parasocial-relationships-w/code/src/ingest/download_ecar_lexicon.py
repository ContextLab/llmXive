"""
Download the ECAR Lexicon dataset, validate its schema, and store it as a CSV.

The ECAR Lexicon is hosted on HuggingFace at:
https://huggingface.co/datasets/12ml/e-CARE/resolve/main/train.csv

The script performs the following steps:
1. Download the CSV file via a direct HTTP request (no external
   dataset library required).
2. Load the CSV into a pandas DataFrame.
3. Validate that the required columns ``keyword``, ``anxiety_weight``,
   and ``avoidance_weight`` exist.
4. Validate that the file contains at least 500 rows.
5. Write the cleaned DataFrame to ``data/lexicons/ecar_lexicon.csv``.
6. Abort with a clear ``RuntimeError`` (message ``Lexicon Missing``) if
   any validation step fails.

The module provides a ``main()`` function that can be imported by the
test suite (``tests/unit/test_download_ecar_lexicon.py``) and also run
as a script: ``python -m src.ingest.download_ecar_lexicon``.
"""

import logging
import io
from pathlib import Path

import pandas as pd
import requests

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ECAR_URL = (
    "https://huggingface.co/datasets/12ml/e-CARE/resolve/main/train.csv"
)
REQUIRED_COLUMNS = {"keyword", "anxiety_weight", "avoidance_weight"}
MIN_ROWS = 500

log = get_logger(__name__)

def download_ecar_lexicon(url: str = ECAR_URL) -> pd.DataFrame:
    """
    Download the ECAR Lexicon CSV from the given URL and return it as a
    pandas DataFrame.

    Parameters
    ----------
    url : str
        Direct URL to the raw CSV file.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the lexicon.

    Raises
    ------
    RuntimeError
        If the HTTP request fails or the content cannot be parsed.
    """
    log.info(f"Downloading ECAR Lexicon from {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        log.error(f"Failed to download ECAR Lexicon: {exc}")
        raise RuntimeError("Lexicon Missing") from exc

    # The response content is a CSV text; use StringIO for pandas
    try:
        csv_bytes = response.content
        csv_str = csv_bytes.decode("utf-8")
        df = pd.read_csv(io.StringIO(csv_str))
    except Exception as exc:
        log.error(f"Failed to parse ECAR CSV: {exc}")
        raise RuntimeError("Lexicon Missing") from exc

    return df

def validate_lexicon(df: pd.DataFrame) -> None:
    """
    Validate the lexicon DataFrame against the expected schema.

    Checks that:
    * All required columns are present.
    * The DataFrame contains at least ``MIN_ROWS`` rows.

    Raises
    ------
    RuntimeError
        If any validation fails.
    """
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        log.error(f"Lexicon missing required columns: {missing}")
        raise RuntimeError("Lexicon Missing")

    row_count = len(df)
    if row_count < MIN_ROWS:
        log.error(
            f"Lexicon contains insufficient rows: {row_count} (< {MIN_ROWS})"
        )
        raise RuntimeError("Lexicon Missing")

    log.info(
        f"ECAR Lexicon validation passed (columns ok, rows={row_count})"
    )

def write_lexicon(df: pd.DataFrame) -> Path:
    """
    Write the validated lexicon DataFrame to the canonical location.

    Returns
    -------
    pathlib.Path
        Path to the written CSV file.
    """
    output_path = paths.data("lexicons", "ecar_lexicon.csv")
    # Ensure parent directory exists (paths.data creates it)
    df.to_csv(output_path, index=False)
    log.info(f"ECAR Lexicon written to {output_path}")
    return output_path

def main() -> None:
    """
    Orchestrates the download, validation, and persistence of the ECAR
    Lexicon.  Any failure results in a ``RuntimeError`` with the message
    ``Lexicon Missing`` so that calling code (including the unit test)
    can detect the abort condition.
    """
    try:
        df = download_ecar_lexicon()
        validate_lexicon(df)
        write_lexicon(df)
    except RuntimeError as exc:
        # Re‑raise to ensure the script exits with a non‑zero status.
        log.error(f"ECAR Lexicon processing failed: {exc}")
        raise

if __name__ == "__main__":
    # When executed as a script we propagate any exception to the
    # interpreter so that the process exits with a non‑zero code.
    main()
