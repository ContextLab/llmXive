"""
Fetch a verified real meta-analysis dataset and store it as the
canonical base file for the project: ``data/raw/cochrane_base.csv``.

Real data source
----------------
The classic BCG vaccine meta-analysis (Colditz et al., 1994; Tuberculosis
Prevention Trial, as distributed with the R ``metafor`` package as
``dat.bcg``).  This is a real, peer-reviewed collection of 13 clinical
trials with 2x2 count data -- exactly the study-level structure a
meta-analysis simulation needs.  It is fetched programmatically from the
official metafor GitHub repository.

The script:
1. Downloads the raw ``dat.bcg.dat`` file over HTTPS.
2. Converts each trial's 2x2 table to a log odds ratio (effect size)
   and its standard error via the standard formulas.
3. Validates the result (>= 5 studies, finite effects, positive SEs).
4. Writes the validated CSV to ``data/raw/cochrane_base.csv``.

Failure behaviour: any download or validation failure raises
``FileNotFoundError`` (and the CLI exits non-zero) -- there is NO
synthetic fallback.

This fulfills T001: exit status 0, real file on disk, loud failure.
"""
import csv
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Tuple

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Official metafor package data repository (Viechtbauer, W.).
# dat.bcg: BCG vaccine efficacy against tuberculosis, 13 trials.
DATA_URL = (
    "https://raw.githubusercontent.com/wviechtb/metafor/master/data/dat.bcg.dat"
)
SOURCE_CITATION = (
    "Colditz et al. (1994), BCG vaccine meta-analysis; "
    "distributed as dataset 'dat.bcg' in the R package metafor "
    "(Viechtbauer, 2010), https://github.com/wviechtb/metafor"
)
OUTPUT_PATH = paths.data("raw", "cochrane_base.csv")
MIN_ROWS = 5
TIMEOUT_S = 60

# ----------------------------------------------------------------------
# Parsing / conversion helpers
# ----------------------------------------------------------------------
def _parse_dat(text: str) -> List[dict]:
    """Parse the whitespace-delimited ``dat.bcg.dat`` layout.

    Each data row has: trial  author...  year  tpos  tneg  cpos  cneg
    The author field may contain spaces, so the row is anchored on the
    numeric head (trial) and the five numeric tail fields.
    """
    rows: List[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 7:
            continue
        # Skip the header line if present.
        try:
            trial = int(parts[0])
        except ValueError:
            continue
        try:
            year, tpos, tneg, cpos, cneg = (int(x) for x in parts[-5:])
        except ValueError:
            continue
        author = " ".join(parts[1:-5])
        rows.append(
            {
                "trial": trial,
                "author": author,
                "year": year,
                "tpos": tpos,
                "tneg": tneg,
                "cpos": cpos,
                "cneg": cneg,
            }
        )
    return rows

def _log_or_and_se(
    tpos: int, tneg: int, cpos: int, cneg: int
) -> Tuple[float, float]:
    """Log odds ratio and its SE from a 2x2 table.

    A 0.5 continuity correction is applied to all four cells when any
    cell is zero (standard practice for log-OR meta-analysis).
    """
    if min(tpos, tneg, cpos, cneg) == 0:
        tpos, tneg, cpos, cneg = (x + 0.5 for x in (tpos, tneg, cpos, cneg))
    log_or = math.log((tpos / tneg) / (cpos / cneg))
    se = math.sqrt(1.0 / tpos + 1.0 / tneg + 1.0 / cpos + 1.0 / cneg)
    return log_or, se

# ----------------------------------------------------------------------
# Fetch + validate + write
# ----------------------------------------------------------------------
def fetch_base_dataset() -> Path:
    """Download, convert, validate and write the real base dataset.

    Raises:
        FileNotFoundError: if the download or validation fails.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fetching verified meta-analysis base data from:")
    print(f"  {DATA_URL}")
    try:
        req = urllib.request.Request(
            DATA_URL, headers={"User-Agent": "llmXive-PROJ-417/1.0"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            raw = resp.read()
    except (urllib.error.URLError, OSError) as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to download the base "
            f"meta-analysis dataset from {DATA_URL}: {exc}"
        ) from exc

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: downloaded content is not valid UTF-8."
        ) from exc

    trials = _parse_dat(text)
    if len(trials) < MIN_ROWS:
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: downloaded data yielded fewer than "
            f"{MIN_ROWS} usable trials (got {len(trials)})."
        )

    out_rows = []
    for t in trials:
        effect, se = _log_or_and_se(
            t["tpos"], t["tneg"], t["cpos"], t["cneg"]
        )
        if not (math.isfinite(effect) and math.isfinite(se)) or se <= 0:
            raise FileNotFoundError(
                "REAL_DATA_FETCH_FAILED: non-finite effect or "
                "non-positive standard error in trial "
                f"{t['trial']} ({t['author']})."
            )
        out_rows.append(
            {
                "study_id": f"trial_{t['trial']:02d}_{t['author'].replace(' ', '_')}",
                "effect_size": effect,
                "standard_error": se,
                "year": t["year"],
                "source": "dat.bcg (metafor)",
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

    print(
        f"Wrote {len(out_rows)} studies (log odds ratios + SEs) "
        f"-> {OUTPUT_PATH}"
    )
    print(f"Source: {SOURCE_CITATION}")
    return OUTPUT_PATH

def main() -> int:
    print("=" * 60)
    print("FETCHING VERIFIED BASE META-ANALYSIS DATASET")
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
