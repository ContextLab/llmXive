"""Download OpenNeuro ds000246 dataset (participants.tsv) and filter eligible subjects.

This script performs the following steps:
1. Ensure the raw data directory exists.
2. Download the ``participants.tsv`` file from the public GitHub mirror of the
   OpenNeuro dataset if it is not already present.
3. Parse the TSV and keep only subjects that have non‑empty MMSE and MOCA scores
   at **both** time points (if the columns exist).
4. Limit the number of eligible subjects to ``N = min(100, available)``.
5. Write two artefacts:
   - ``data/processed/eligible_subjects.csv`` – the retained subjects and their
     scores.
   - ``data/processed/excluded_subjects.log`` – a plain‑text log of subjects that
     were excluded and the reason for exclusion.

The script is deliberately lightweight: it only downloads the small
``participants.tsv`` file (≈ few KB) rather than the full BIDS dataset, which
would be far too large for CI execution. All other downstream steps (e.g.
downloading the full imaging data) are handled by later scripts.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List, Dict

import requests

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RAW_DATA_DIR = Path("data/raw/ds000246")
PROCESSED_DATA_DIR = Path("data/processed")
PARTICIPANTS_URL = (
    "https://raw.githubusercontent.com/OpenNeuroDatasets/ds000246/master/participants.tsv"
)
PARTICIPANTS_FILENAME = "participants.tsv"
ELIGIBLE_OUTPUT = PROCESSED_DATA_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = PROCESSED_DATA_DIR / "excluded_subjects.log"
MAX_SUBJECTS = 100

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def ensure_dir(p: Path) -> None:
    """Create directory ``p`` (including parents) if it does not exist."""
    p.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path) -> None:
    """Download ``url`` to ``dest`` using a streaming request."""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
    except Exception as exc:
        raise RuntimeError(f"Failed to download {url!r}: {exc}") from exc


def read_participants_tsv(path: Path) -> List[Dict[str, str]]:
    """Read a BIDS ``participants.tsv`` file and return a list of rows as dicts."""
    if not path.is_file():
        raise FileNotFoundError(f"participants.tsv not found at {path}")

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = [row for row in reader]
    return rows


def is_eligible(row: Dict[str, str]) -> bool:
    """
    Determine eligibility of a subject row.

    Eligibility criteria (as described in the task):
    * Non‑null MMSE at both time points.
    * Non‑null MOCA at both time points.

    The exact column names can vary across releases.  We therefore look for
    any column that contains ``mmse`` or ``moca`` (case‑insensitive) and
    require that **all** such columns have a non‑empty value for the row.
    """
    # Normalise keys to lower case for easier matching
    lower_keys = {k.lower(): v for k, v in row.items()}

    # Identify MMSE and MOCA related columns
    mmse_keys = [k for k in lower_keys if "mmse" in k]
    moca_keys = [k for k in lower_keys if "moca" in k]

    # If the dataset does not contain the expected columns, we consider the
    # subject ineligible – this makes the failure explicit.
    if not mmse_keys or not moca_keys:
        return False

    # All identified columns must be non‑empty after stripping whitespace
    for key in mmse_keys + moca_keys:
        if lower_keys[key].strip() == "":
            return False
    return True


def filter_eligible_subjects(
    rows: List[Dict[str, str]]
) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Split ``rows`` into eligible and excluded based on ``is_eligible``.
    Returns a tuple ``(eligible, excluded)``.
    """
    eligible = []
    excluded = []
    for row in rows:
        if is_eligible(row):
            eligible.append(row)
        else:
            excluded.append(row)
    return eligible, excluded


def limit_subjects(
    eligible: List[Dict[str, str]], max_n: int = MAX_SUBJECTS
) -> List[Dict[str, str]]:
    """Return at most ``max_n`` subjects, preserving the original order."""
    return eligible[:max_n]


def write_eligible_csv(rows: List[Dict[str, str]], dest: Path) -> None:
    """Write eligible rows to ``dest`` as a CSV (comma‑separated)."""
    if not rows:
        raise ValueError("No eligible rows to write.")
    fieldnames = rows[0].keys()
    with dest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_excluded_log(rows: List[Dict[str, str]], dest: Path) -> None:
    """Write a simple log listing excluded subject IDs and why they were excluded."""
    with dest.open("w", encoding="utf-8") as f:
        for row in rows:
            subj = row.get("participant_id") or row.get("subject_id") or "UNKNOWN"
            f.write(f"{subj}\\texcluded (missing MMSE/MOCA)\\n")


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    # 1. Ensure directories exist
    ensure_dir(RAW_DATA_DIR)
    ensure_dir(PROCESSED_DATA_DIR)

    participants_path = RAW_DATA_DIR / PARTICIPANTS_FILENAME

    # 2. Download participants.tsv if missing
    if not participants_path.is_file():
        print(f"Downloading participants.tsv from {PARTICIPANTS_URL} ...")
        download_file(PARTICIPANTS_URL, participants_path)
        print(f"Saved to {participants_path}")

    # 3. Load participants.tsv
    try:
        rows = read_participants_tsv(participants_path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    # 4. Filter eligible / excluded
    eligible, excluded = filter_eligible_subjects(rows)

    # 5. Fail fast if no eligible subjects
    if not eligible:
        print("No eligible subjects found after filtering.", file=sys.stderr)
        sys.exit(1)

    # 6. Apply subject limit (N = min(100, available))
    limited = limit_subjects(eligible, MAX_SUBJECTS)

    # 7. Write outputs
    write_eligible_csv(limited, ELIGIBLE_OUTPUT)
    write_excluded_log(excluded, EXCLUDED_LOG)

    print(f"Wrote {len(limited)} eligible subjects to {ELIGIBLE_OUTPUT}")
    print(f"Wrote {len(excluded)} excluded subjects to {EXCLUDED_LOG}")


if __name__ == "__main__":
    main()