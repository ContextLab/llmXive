"""
Fetch a verified real meta‑analysis dataset and store it as the
canonical base file for the project: ``data/raw/cochrane_base.csv``.

Real data source
----------------
The classic BCG vaccine meta‑analysis (Colditz et al., 1994) is
distributed with the R ``metafor`` package.  The original data file
is available in the metafor source repository:

    https://raw.githubusercontent.com/wviechtb/metafor/master/data/dat.bcg.dat

This script downloads that file directly (using ``requests``), parses the
2 × 2 tables, converts them to log‑odds ratios and standard errors, and
writes a validated CSV to ``data/raw/cochrane_base.csv``.

Failure behaviour
-----------------
Any download, parsing, or validation error raises ``FileNotFoundError``.
The CLI exits with a non‑zero status, as required by task T001.
No synthetic fallback is provided.
"""
import csv
import math
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd
import requests

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
SOURCE_URL = (
    "https://raw.githubusercontent.com/wviechtb/metafor/master/data/dat.bcg.dat"
)
SOURCE_CITATION = (
    "Colditz et al. (1994), BCG vaccine meta‑analysis; "
    "distributed as dataset 'dat.bcg' in the R package metafor "
    "(Viechtbauer, 2010)."
)
OUTPUT_PATH = paths.data("raw", "cochrane_base.csv")
MIN_ROWS = 5
# ----------------------------------------------------------------------


def _log_or_and_se(tpos: int, tneg: int, cpos: int, cneg: int) -> (float, float):
    """Log odds ratio and its SE from a 2 × 2 table.

    A 0.5 continuity correction is applied to all four cells when any
    cell is zero (standard practice for log‑OR meta‑analysis).
    """
    if min(tpos, tneg, cpos, cneg) == 0:
        tpos, tneg, cpos, cneg = (x + 0.5 for x in (tpos, tneg, cpos, cneg))
    log_or = math.log((tpos / tneg) / (cpos / cneg))
    se = math.sqrt(1.0 / tpos + 1.0 / tneg + 1.0 / cpos + 1.0 / cneg)
    return log_or, se


def _download_dataset() -> pd.DataFrame:
    """Download the raw BCG dataset from the GitHub mirror.

    Returns a pandas DataFrame with the expected columns.
    Raises FileNotFoundError on any failure.
    """
    try:
        response = requests.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to download BCG dataset from {SOURCE_URL}: {exc}"
        ) from exc

    # The original file is whitespace‑delimited with a header.
    # ``read_csv`` with ``delim_whitespace=True`` handles it.
    try:
        from io import StringIO

        df = pd.read_csv(StringIO(response.text), delim_whitespace=True)
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to parse the downloaded dataset: {exc}"
        ) from exc

    if df.empty:
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: downloaded dataset is empty."
        )

    # Normalise column names to lower case for safety.
    df = df.rename(columns=lambda x: x.lower())
    return df


def fetch_base_dataset() -> Path:
    """Download, convert, validate and write the real base dataset.

    Returns the path to the written CSV.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching verified meta‑analysis base data from:", SOURCE_URL)

    df = _download_dataset()

    required_cols = {"tpos", "tneg", "cpos", "cneg", "year"}
    missing = required_cols - set(df.columns)
    if missing:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: dataset missing required columns: {missing}"
        )

    out_rows: List[Dict] = []
    for idx, row in df.iterrows():
        try:
            tpos = int(row["tpos"])
            tneg = int(row["tneg"])
            cpos = int(row["cpos"])
            cneg = int(row["cneg"])
            year = int(row["year"])
        except (ValueError, TypeError) as exc:
            # Skip rows that cannot be interpreted as integers
            continue

        effect, se = _log_or_and_se(tpos, tneg, cpos, cneg)
        if not (math.isfinite(effect) and math.isfinite(se)) or se <= 0:
            raise FileNotFoundError(
                "REAL_DATA_FETCH_FAILED: non‑finite effect or non‑positive "
                f"standard error in trial {idx + 1}."
            )
        out_rows.append(
            {
                "study_id": f"trial_{idx + 1:02d}",
                "effect_size": effect,
                "standard_error": se,
                "year": year,
                "source": "dat.bcg (metafor, GitHub mirror)",
            }
        )

    if len(out_rows) < MIN_ROWS:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: downloaded data yielded fewer than "
            f"{MIN_ROWS} usable trials (got {len(out_rows)})."
        )

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "study_id",
                "effect_size",
                "standard_error",
                "year",
                "source",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} studies (log odds ratios + SEs) -> {OUTPUT_PATH}")
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