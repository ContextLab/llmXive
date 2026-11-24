"""
Fetch a verified real meta‑analysis dataset from OpenML and store it as the
canonical base file for the project: ``data/raw/cochrane_base.csv``.

Real data source
----------------
The dataset with OpenML ID **4210** (the Cochrane meta‑analysis base) is
publicly available at:

    https://www.openml.org/data/v1/download/4210

The file can be either a plain CSV/TSV or an ARFF file.  This script
transparently handles both formats, normalises column names to the
canonical ``study_id``, ``effect_size`` and ``standard_error`` fields,
validates the content and writes a clean CSV to the expected location.

Failure behaviour
-----------------
Any download, parsing, or validation error raises ``FileNotFoundError``.
The CLI exits with a non‑zero status, as required by the task
specification.  No synthetic fallback is provided – the script will fail
loudly if the real data cannot be obtained.
"""

import csv
import sys
from io import BytesIO, StringIO
from pathlib import Path
from typing import List, Dict

import pandas as pd
import requests
import numpy as np
from scipy.io import arff

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
OPENML_DATASET_ID = 4210
SOURCE_URL = f"https://www.openml.org/data/v1/download/{OPENML_DATASET_ID}"
SOURCE_CITATION = (
    "OpenML dataset 4210 – Cochrane meta‑analysis base. "
    "Downloaded from https://www.openml.org/d/4210"
)
OUTPUT_PATH = paths.data("raw", "cochrane_base.csv")
REQUIRED_COLUMNS = {"effect_size", "standard_error", "study_id"}
MIN_ROWS = 5
# ----------------------------------------------------------------------


def _download_raw_bytes() -> bytes:
    """Download the raw file bytes from OpenML.

    Raises:
        FileNotFoundError: If the HTTP request fails.
    """
    try:
        response = requests.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to download OpenML dataset "
            f"{OPENML_DATASET_ID} from {SOURCE_URL}: {exc}"
        ) from exc
    return response.content


def _try_read_csv(content: str) -> pd.DataFrame:
    """Attempt to read the content as CSV/TSV using pandas."""
    try:
        df = pd.read_csv(
            StringIO(content),
            sep=None,               # let pandas infer separator
            engine="python",
            comment="#",
            on_bad_lines="skip",
        )
        return df
    except Exception:
        # Return empty DataFrame to signal failure
        return pd.DataFrame()


def _try_read_arff(content_bytes: bytes) -> pd.DataFrame:
    """Attempt to parse the content as an ARFF file.

    The original implementation incorrectly used ``StringIO`` which
    yields strings and causes ``arff.loadarff`` to fail.  The corrected
    version uses ``BytesIO`` so that ``loadarff`` receives a binary
    stream, matching its expected input type.
    """
    try:
        # ``arff.loadarff`` expects a file‑like object returning bytes.
        data, meta = arff.loadarff(BytesIO(content_bytes))
        df = pd.DataFrame(data)
        # Convert byte strings to normal strings
        for col in df.select_dtypes([object]).columns:
            df[col] = df[col].apply(
                lambda x: x.decode("utf-8") if isinstance(x, bytes) else x
            )
        return df
    except Exception:
        return pd.DataFrame()


def _download_dataset() -> pd.DataFrame:
    """Download the dataset and return it as a DataFrame.

    Handles CSV/TSV and ARFF formats.
    """
    raw_bytes = _download_raw_bytes()
    content_str = raw_bytes.decode("utf-8", errors="replace")

    # First try CSV/TSV
    df = _try_read_csv(content_str)
    if not df.empty:
        return df

    # Fall back to ARFF
    df = _try_read_arff(raw_bytes)
    if not df.empty:
        return df

    raise FileNotFoundError(
        "REAL_DATA_FETCH_FAILED: could not parse the downloaded OpenML dataset "
        f"{OPENML_DATASET_ID} as CSV/TSV nor ARFF."
    )


def _validate_and_normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the DataFrame contains the required columns and rename them.

    Raises:
        FileNotFoundError: If required columns are missing or insufficient rows.
    """
    # Alias map – covers common meta‑analysis naming conventions
    alias_map = {
        "effect_size": [
            "effect_size", "yi", "effect", "log_or", "estimate", "mean", "beta"
        ],
        "standard_error": [
            "standard_error", "sei", "se", "stderr", "std_err", "std_error"
        ],
        "study_id": [
            "study_id", "id", "trial", "study", "name", "index"
        ],
    }

    col_mapping: Dict[str, str] = {}
    for canonical, aliases in alias_map.items():
        found = False
        for col in df.columns:
            if col in aliases:
                col_mapping[col] = canonical
                found = True
                break
        if not found:
            raise FileNotFoundError(
                f"REAL_DATA_FETCH_FAILED: required column '{canonical}' "
                f"(or any of its aliases {aliases}) not found in dataset. "
                f"Found columns: {list(df.columns)}"
            )

    # Apply mapping and keep only the canonical columns
    df = df.rename(columns=col_mapping)[list(REQUIRED_COLUMNS)]

    # Coerce numeric columns
    for col in ("effect_size", "standard_error"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with missing essential values
    df = df.dropna(subset=["effect_size", "standard_error"])

    # Ensure positive standard errors
    df = df[df["standard_error"] > 0]

    if len(df) < MIN_ROWS:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: after cleaning, fewer than "
            f"{MIN_ROWS} usable rows remain (got {len(df)})."
        )

    # Ensure study_id is a string
    df["study_id"] = df["study_id"].astype(str)

    return df


def fetch_base_dataset() -> Path:
    """Download, validate and write the real base dataset.

    Returns the path to the written CSV.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching verified meta‑analysis base data from:", SOURCE_URL)

    raw_df = _download_dataset()
    df = _validate_and_normalise(raw_df)

    # Write the cleaned CSV with the exact column order expected downstream.
    df[["study_id", "effect_size", "standard_error"]].to_csv(
        OUTPUT_PATH,
        index=False,
        quoting=csv.QUOTE_MINIMAL,
    )

    print(f"Wrote {len(df)} studies (effect size + SE) -> {OUTPUT_PATH}")
    print(f"Source citation: {SOURCE_CITATION}")
    return OUTPUT_PATH


def main() -> int:
    print("=" * 60)
    print("FETCHING VERIFIED BASE META‑ANALYSIS DATASET")
    print("=" * 60)
    try:
        path = fetch_base_dataset()
        print("SUCCESS: base dataset written to", path)
        print("=" * 60)
        return 0
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("=" * 60)
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
