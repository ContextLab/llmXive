"""Download OpenNeuro ds000246, filter participants, and write outputs.

This script performs the following steps:
1. Download the ``participants.tsv`` file from the OpenNeuro dataset
   ``ds000246`` (Constitution VI, FR‑001).  Only the TSV is required for the
   eligibility check, so we avoid pulling the entire multi‑GB dataset.
2. Parse the TSV and keep subjects that have **non‑null** MMSE **and**
   MoCA scores at **both time points** (the TSV is expected to contain
   columns such as ``mmse_1``, ``mmse_2``, ``moca_1`` and ``moca_2`` – the
   exact column names are inferred case‑insensitively).
3. Limit the eligible set to ``N = min(100, available_eligible)``.
4. Write ``data/processed/eligible_subjects.csv`` (one column:
   ``participant_id``) and ``data/processed/excluded_subjects.log``
   (human‑readable reasons for exclusion).

The script is deliberately tolerant:
* If the dataset cannot be reached, it aborts with a clear error.
* If **no** eligible subjects are found, it exits with the constant
  ``EXIT_CODE_NO_LABELS = 2`` as required by the specification.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path
from typing import Iterable, List, Tuple

import requests

from utils.logger import get_logger, log_operation

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
DATASET_VERSION = "1.0.0"
DATASET_ID = "ds000246"
# Direct download link for the participants.tsv file (OpenNeuro provides a
# raw‑file endpoint that returns the file contents without needing the full
# dataset archive).
PARTICIPANTS_URL = (
    f"https://openneuro.org/crn/datasets/{DATASET_ID}/versions/"
    f"{DATASET_VERSION}/files/participants.tsv?download=1"
)

RAW_DIR = Path("data/raw") / DATASET_ID
PROCESSED_DIR = Path("data/processed")
ELIGIBLE_CSV = PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = PROCESSED_DIR / "excluded_subjects.log"

# Exit code when no labels (MMSE/MoCA) are present for any subject.
EXIT_CODE_NO_LABELS = 2

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_dir(p: Path) -> None:
    """Create a directory (including parents) if it does not exist."""
    p.mkdir(parents=True, exist_ok=True)

def download_file(url: str, dest: Path, retries: int = 3, backoff: float = 2.0) -> None:
    """Download a file via HTTP with simple retry logic."""
    logger = get_logger("download_file")
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Attempt {attempt} – downloading {url}")
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info(f"Successfully downloaded to {dest}")
            return
        except Exception as exc:  # pragma: no cover – network failures are rare in CI
            logger.warning(f"Download attempt {attempt} failed: {exc}")
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                raise

def read_participants_tsv(tsv_path: Path) -> List[dict]:
    """Read participants.tsv and return a list of dictionaries (one per row)."""
    logger = get_logger("read_participants_tsv")
    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = [row for row in reader]
    logger.info(f"Read {len(rows)} rows from {tsv_path.name}")
    return rows

def _find_score_columns(rows: List[dict]) -> Tuple[List[str], List[str]]:
    """
    Identify MMSE and MoCA column names (case‑insensitive) that contain a
    session identifier (e.g. ``mmse_1`` and ``mmse_2``). Returns two lists:
    ``mmse_cols`` and ``moca_cols``. If the required pairs are not present,
    the lists will be empty.
    """
    if not rows:
        return [], []
    sample = rows[0]
    mmse_cols = [c for c in sample if c.lower().startswith("mmse")]
    moca_cols = [c for c in sample if c.lower().startswith("moca")]
    # Keep only columns that appear to have two time points.
    mmse_cols = sorted([c for c in mmse_cols if any(t in c for t in ("1", "2"))])
    moca_cols = sorted([c for c in moca_cols if any(t in c for t in ("1", "2"))])
    return mmse_cols, moca_cols

def is_eligible(row: dict, mmse_cols: List[str], moca_cols: List[str]) -> Tuple[bool, str]:
    """
    Determine eligibility for a single participant row.

    Returns (eligible, reason).  ``reason`` is empty when eligible.
    """
    # Participant must have a non‑empty ID.
    pid = row.get("participant_id") or row.get("participant_id".lower()) or row.get("subject_id")
    if not pid:
        return False, "missing participant_id"

    # Check that every required score column is present and non‑empty.
    missing = []
    for col in mmse_cols + moca_cols:
        val = row.get(col, "").strip()
        if val == "" or val.lower() == "nan":
            missing.append(col)
    if missing:
        return False, f"missing scores: {', '.join(missing)}"
    return True, ""

def filter_eligible_subjects(
    rows: List[dict],
) -> Tuple[List[dict], List[Tuple[dict, str]]]:
    """Separate eligible and excluded participants."""
    logger = get_logger("filter_eligible")
    mmse_cols, moca_cols = _find_score_columns(rows)
    if len(mmse_cols) < 2 or len(moca_cols) < 2:
        logger.error(
            "Required MMSE/MoCA columns for two time points not found in TSV."
        )
        # No subject can be eligible if the columns are missing.
        return [], [(row, "insufficient score columns") for row in rows]

    eligible: List[dict] = []
    excluded: List[Tuple[dict, str]] = []
    for row in rows:
        ok, reason = is_eligible(row, mmse_cols, moca_cols)
        if ok:
            eligible.append(row)
        else:
            excluded.append((row, reason))
    logger.info(f"Eligible: {len(eligible)} – Excluded: {len(excluded)}")
    return eligible, excluded

def limit_subjects(eligible: List[dict], max_n: int = 100) -> List[dict]:
    """Truncate the eligible list to at most ``max_n`` entries."""
    return eligible[:max_n]

def write_eligible_csv(eligible: List[dict], path: Path) -> None:
    """Write ``participant_id`` column of eligible subjects to CSV."""
    logger = get_logger("write_eligible_csv")
    ensure_dir(path.parent)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id"])
        for row in eligible:
            pid = row.get("participant_id") or row.get("participant_id".lower())
            writer.writerow([pid])
    logger.info(f"Wrote {len(eligible)} eligible IDs to {path}")

def write_excluded_log(excluded: List[Tuple[dict, str]], path: Path) -> None:
    """Write a human‑readable log of excluded participants."""
    logger = get_logger("write_excluded_log")
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        for row, reason in excluded:
            pid = row.get("participant_id") or row.get("participant_id".lower()) or "UNKNOWN"
            f.write(f"{pid}: {reason}\n")
    logger.info(f"Wrote exclusion log with {len(excluded)} entries to {path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
@log_operation("01_download_and_filter")
def main() -> None:
    """Entry point for the download‑and‑filter step."""
    logger = get_logger("01_download_and_filter")

    # 1️⃣ Ensure directories exist.
    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)

    # 2️⃣ Download participants.tsv (if not already present).
    participants_path = RAW_DIR / "participants.tsv"
    if not participants_path.is_file():
        logger.info(f"Downloading participants.tsv from OpenNeuro ({PARTICIPANTS_URL})")
        try:
            download_file(PARTICIPANTS_URL, participants_path)
        except Exception as exc:
            logger.error(f"Failed to download participants.tsv: {exc}")
            sys.exit(1)
    else:
        logger.info(f"Using cached participants.tsv at {participants_path}")

    # 3️⃣ Parse TSV.
    rows = read_participants_tsv(participants_path)

    # 4️⃣ Filter eligibility.
    eligible, excluded = filter_eligible_subjects(rows)

    # 5️⃣ Abort if no eligible subjects (spec requirement).
    if not eligible:
        logger.error("No eligible subjects found – exiting with EXIT_CODE_NO_LABELS")
        sys.exit(EXIT_CODE_NO_LABELS)

    # 6️⃣ Limit to at most 100 subjects.
    limited = limit_subjects(eligible, max_n=100)

    # 7️⃣ Write outputs.
    write_eligible_csv(limited, ELIGIBLE_CSV)
    write_excluded_log(excluded, EXCLUDED_LOG)

    logger.info("Download and filtering completed successfully.")

if __name__ == "__main__":
    sys.exit(main())