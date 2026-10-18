"""
Fetch a verified real meta‑analysis dataset and store it as the
canonical base file for the project: ``data/raw/cochrane_base.csv``.

Real data source
----------------
The classic BCG vaccine meta‑analysis (Colditz et al., 1994) is
distributed with the R ``metafor`` package.  Historically the raw
file lived at::

    https://raw.githubusercontent.com/wviechtb/metafor/master/data/dat.bcg.dat

The file has been moved in recent versions of the repository.
This script now uses the OpenML mirror (dataset ID 4210) via the
``openml`` Python package to reliably obtain the data.  No synthetic
fallback is provided – any download or validation failure raises
``FileNotFoundError`` and the CLI exits with a non‑zero status,
as required by task T001.

The script:
1. Downloads the dataset using ``openml.datasets.get_dataset``.
2. Extracts the required 2 × 2 table columns.
3. Converts each table to a log‑odds ratio and its standard error
   (with a 0.5 continuity correction when needed).
4. Validates that at least ``MIN_ROWS`` trials were successfully
   parsed and that all effects/SEs are finite and positive.
5. Writes the validated CSV to ``data/raw/cochrane_base.csv`` with
   columns: ``study_id``, ``effect_size``, ``standard_error``,
   ``year`` and ``source``.

Failure behaviour: any download or validation failure raises
``FileNotFoundError`` (and the CLI exits non‑zero) – there is NO
synthetic fallback.
"""
import csv
import math
import sys
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
OPENML_DATASET_ID = 4210
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


def _download_via_openml() -> List[Dict]:
    """Download the dataset using the ``openml`` package.

    Returns a list of dictionaries, each representing a trial with the
    keys ``tpos``, ``tneg``, ``cpos``, ``cneg``, and ``year``.
    """
    try:
        import openml
    except ImportError as exc:
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: the 'openml' package is not installed."
        ) from exc

    try:
        dataset = openml.datasets.get_dataset(OPENML_DATASET_ID, download_all_files=True)
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to fetch OpenML dataset {OPENML_DATASET_ID}: {exc}"
        ) from exc

    # ``get_data`` returns (dataframe, _, _, _)
    df, _, _, _ = dataset.get_data()
    if df is None or df.empty:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: OpenML dataset {OPENML_DATASET_ID} returned no data."
        )

    # Expected column names (based on the original metafor data)
    required_cols = {"tpos", "tneg", "cpos", "cneg", "year"}
    missing = required_cols - set(df.columns.str.lower())
    if missing:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: OpenML data missing required columns: {missing}"
        )

    # Normalise column names to lower case for safety
    df = df.rename(columns=lambda x: x.lower())

    trials = []
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
        trials.append(
            {
                "trial": idx + 1,
                "tpos": tpos,
                "tneg": tneg,
                "cpos": cpos,
                "cneg": cneg,
                "year": year,
            }
        )
    return trials


def fetch_base_dataset() -> Path:
    """Download, convert, validate and write the real base dataset.

    Returns the path to the written CSV.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching verified meta‑analysis base data from OpenML dataset ID:",
          OPENML_DATASET_ID)

    trials = _download_via_openml()
    if len(trials) < MIN_ROWS:
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: downloaded data yielded fewer than "
            f"{MIN_ROWS} usable trials (got {len(trials)})."
        )

    out_rows = []
    for t in trials:
        effect, se = _log_or_and_se(t["tpos"], t["tneg"], t["cpos"], t["cneg"])
        if not (math.isfinite(effect) and math.isfinite(se)) or se <= 0:
            raise FileNotFoundError(
                "REAL_DATA_FETCH_FAILED: non‑finite effect or non‑positive "
                f"standard error in trial {t['trial']}."
            )
        out_rows.append(
            {
                "study_id": f"trial_{t['trial']:02d}",
                "effect_size": effect,
                "standard_error": se,
                "year": t["year"],
                "source": "dat.bcg (metafor, OpenML mirror)",
            }
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