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
This script now tries a small list of known locations, falling back
to the OpenML mirror (dataset ID 4210) if the original URL no longer
resolves.  No synthetic fallback is provided – any download or
validation failure raises ``FileNotFoundError`` and the CLI exits
with a non‑zero status, as required by task T001.

The script:
1. Attempts to download the raw ``dat.bcg`` file from a prioritized
   list of URLs.
2. Parses the whitespace‑delimited layout (or ARFF‑style layout from
   OpenML) into a list of trials.
3. Converts each 2 × 2 table to a log‑odds ratio and its standard
   error (with a 0.5 continuity correction when needed).
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
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Tuple

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Primary historic location (may be removed in the upstream repo)
PRIMARY_URL = (
    "https://raw.githubusercontent.com/wviechtb/metafor/master/data/dat.bcg.dat"
)
# Alternate location without the .dat suffix (present in newer releases)
ALT_URL = (
    "https://raw.githubusercontent.com/wviechtb/metafor/master/data/dat.bcg"
)
# OpenML mirror – dataset ID 4210 (publicly hosted)
OPENML_URL = "https://www.openml.org/data/v1/download/4210"

SOURCE_CITATION = (
    "Colditz et al. (1994), BCG vaccine meta‑analysis; "
    "distributed as dataset 'dat.bcg' in the R package metafor "
    "(Viechtbauer, 2010)."
)
OUTPUT_PATH = paths.data("raw", "cochrane_base.csv")
MIN_ROWS = 5
TIMEOUT_S = 60

# ----------------------------------------------------------------------
# Parsing / conversion helpers
# ----------------------------------------------------------------------
def _parse_dat_whitespace(text: str) -> List[dict]:
    """Parse the original whitespace‑delimited ``dat.bcg.dat`` layout.

    Each data row has: trial  author…  year  tpos  tneg  cpos  cneg
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
        # The first token should be the trial number.
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

def _parse_arff(text: str) -> List[dict]:
    """Parse a simple ARFF file that contains the same columns as the
    original ``dat.bcg`` dataset.  The parser is deliberately lightweight:
    it looks for the ``@DATA`` section and then expects whitespace‑delimited
    rows with the same six numeric fields plus an author string.
    """
    data_section = False
    rows: List[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            continue
        if line.upper().startswith("@DATA"):
            data_section = True
            continue
        if not data_section:
            continue
        # At this point we have a data line.
        parts = line.split(",") if "," in line else line.split()
        # Some ARFF exports separate the author with quotes – strip them.
        parts = [p.strip().strip('"') for p in parts]
        if len(parts) < 7:
            continue
        try:
            trial = int(parts[0])
            author = parts[1]
            year = int(parts[2])
            tpos = int(parts[3])
            tneg = int(parts[4])
            cpos = int(parts[5])
            cneg = int(parts[6])
        except ValueError:
            continue
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
    """Log odds ratio and its SE from a 2 × 2 table.

    A 0.5 continuity correction is applied to all four cells when any
    cell is zero (standard practice for log‑OR meta‑analysis).
    """
    if min(tpos, tneg, cpos, cneg) == 0:
        tpos, tneg, cpos, cneg = (x + 0.5 for x in (tpos, tneg, cpos, cneg))
    log_or = math.log((tpos / tneg) / (cpos / cneg))
    se = math.sqrt(1.0 / tpos + 1.0 / tneg + 1.0 / cpos + 1.0 / cneg)
    return log_or, se

# ----------------------------------------------------------------------
# Fetch + validate + write
# ----------------------------------------------------------------------
def _download(url: str) -> bytes:
    """Download ``url`` with a short timeout.  Propagates any
    ``URLError``/``OSError`` as ``FileNotFoundError`` with a helpful
    message.
    """
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "llmXive-PROJ-417/1.0"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return resp.read()
    except (urllib.error.URLError, OSError) as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to download from {url}: {exc}"
        ) from exc

def fetch_base_dataset() -> Path:
    """Download, convert, validate and write the real base dataset.

    The function tries a list of known URLs in order.  The first
    successful download is used.  If none succeed, a ``FileNotFoundError``
    is raised.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching verified meta‑analysis base data from:")
    candidate_urls = [PRIMARY_URL, ALT_URL, OPENML_URL]
    raw_bytes: bytes | None = None
    for url in candidate_urls:
        try:
            raw_bytes = _download(url)
            print(f"  SUCCESS: downloaded from {url}")
            break
        except FileNotFoundError as exc:
            print(f"  WARNING: {exc}", file=sys.stderr)
            continue

    if raw_bytes is None:
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: all candidate URLs failed."
        )

    # Decode – most sources are UTF‑8; if that fails we raise.
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: downloaded content is not valid UTF‑8."
        ) from exc

    # Determine which parser to use.
    if "@DATA" in text.upper():
        trials = _parse_arff(text)
    else:
        trials = _parse_dat_whitespace(text)

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
                "REAL_DATA_FETCH_FAILED: non‑finite effect or "
                "non‑positive standard error in trial "
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
