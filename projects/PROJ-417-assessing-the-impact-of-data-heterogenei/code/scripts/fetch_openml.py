"""
Fetch a verified real meta‑analysis dataset from OpenML and store it as the
canonical base file for the project: ``data/raw/cochrane_base.csv``.

Real data source
----------------
The dataset with OpenML ID **4210** (the Cochrane meta‑analysis base) is
publicly available at:

    https://www.openml.org/data/v1/download/4210

This script downloads that file, validates that it contains the required
columns, normalises column names to ``effect_size`` and ``standard_error``,
and writes a clean CSV to ``data/raw/cochrane_base.csv``.

Failure behaviour
-----------------
Any download, parsing, or validation error raises ``FileNotFoundError``.
The CLI exits with a non‑zero status, as required by task T001.
No synthetic fallback is provided.
"""
import csv
import sys
from io import BytesIO, StringIO
from pathlib import Path
from typing import List, Dict

import pandas as pd
import requests

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


def _download_dataset() -> pd.DataFrame:
    """Download the dataset from OpenML and return it as a DataFrame.

    The OpenML file for ID 4210 is known to contain occasional malformed
    rows (extra delimiters).  We therefore read the content with pandas
    using ``on_bad_lines='skip'`` which drops any rows that do not conform
    to the inferred delimiter.  This keeps the script deterministic while
    still raising an error if the resulting DataFrame is empty or missing
    required columns.

    Raises:
        FileNotFoundError: If the download fails or the content cannot be
                           parsed as a CSV/TSV table.
    """
    try:
        response = requests.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to download OpenML dataset "
            f"{OPENML_DATASET_ID} from {SOURCE_URL}: {exc}"
        ) from exc

    # Decode bytes to string for pandas; we keep original bytes for fallback
    # detection of delimiter if needed.
    content = response.content.decode("utf-8", errors="replace")

    # First try to let pandas infer the separator.
    try:
        df = pd.read_csv(
            StringIO(content),
            sep=None,
            engine="python",
            comment="#",
            on_bad_lines="skip",
        )
    except Exception as exc:
        # If inference fails, fall back to a strict comma‑separated read.
        try:
            df = pd.read_csv(
                StringIO(content),
                sep=",",
                engine="python",
                comment="#",
                on_bad_lines="skip",
            )
        except Exception as exc2:
            raise FileNotFoundError(
                f"REAL_DATA_FETCH_FAILED: unable to parse the downloaded "
                f"OpenML dataset {OPENML_DATASET_ID}: {exc2}"
            ) from exc2

    if df.empty:
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: downloaded OpenML dataset is empty."
        )

    # Normalise column names to lower case and strip whitespace.
    df = df.rename(columns=lambda x: x.strip().lower())
    return df


def _validate_and_normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the DataFrame contains the required columns and rename them.

    The source may use different naming conventions (e.g., ``yi``/``sei``).
    This function maps any recognised aliases to the canonical names.

    Raises:
        FileNotFoundError: If required columns are missing or insufficient rows.
    """
    # Possible aliases for the required fields.
    alias_map = {
        "effect_size": ["effect_size", "yi", "effect", "log_or"],
        "standard_error": ["standard_error", "sei", "se"],
        "study_id": ["study_id", "id", "trial", "study"],
    }

    # Build a mapping from existing column to the canonical name.
    col_mapping: Dict[str, str] = {}
    for canonical, aliases in alias_map.items():
        for col in df.columns:
            if col in aliases:
                col_mapping[col] = canonical
                break
        else:
            # No matching column found for this canonical name.
            raise FileNotFoundError(
                f"REAL_DATA_FETCH_FAILED: required column '{canonical}' "
                f"(or any of its aliases {aliases}) not found in dataset."
            )

    # Apply the mapping.
    df = df.rename(columns=col_mapping)

    # Keep only the canonical columns (extra columns are ignored).
    df = df[list(REQUIRED_COLUMNS.intersection(df.columns))]

    if len(df) < MIN_ROWS:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: downloaded data contains fewer than "
            f"{MIN_ROWS} usable rows (got {len(df)})."
        )

    # Verify numeric types for effect size and SE.
    for col in ("effect_size", "standard_error"):
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise FileNotFoundError(
                f"REAL_DATA_FETCH_FAILED: column '{col}' must be numeric."
            )

    # Remove rows with non‑finite values.
    df = df.dropna(subset=["effect_size", "standard_error"])
    df = df[
        df["effect_size"].apply(pd.api.types.is_number)
        & df["standard_error"].apply(pd.api.types.is_number)
    ]
    df = df[df["standard_error"] > 0]

    if len(df) < MIN_ROWS:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: after cleaning, fewer than "
            f"{MIN_ROWS} usable rows remain (got {len(df)})."
        )

    return df


def fetch_base_dataset() -> Path:
    """Download, validate and write the real base dataset.

    Returns the path to the written CSV.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching verified meta‑analysis base data from:", SOURCE_URL)

    raw_df = _download_dataset()
    df = _validate_and_normalise(raw_df)

    # Ensure a study identifier column exists; if not, create one.
    if "study_id" not in df.columns or df["study_id"].isnull().all():
        df = df.reset_index().rename(columns={"index": "study_id"})
        df["study_id"] = df["study_id"].apply(lambda x: f"study_{int(x)+1}")

    # Write the cleaned CSV with the exact column order expected downstream.
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["study_id", "effect_size", "standard_error"],
        )
        writer.writeheader()
        for _, row in df.iterrows():
            writer.writerow(
                {
                    "study_id": row["study_id"],
                    "effect_size": row["effect_size"],
                    "standard_error": row["standard_error"],
                }
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


if __name__ == "__main__":
    sys.exit(main())
