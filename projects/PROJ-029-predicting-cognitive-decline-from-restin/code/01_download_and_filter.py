"""Download OpenNeuro ds000246, filter participants, and write outputs.

This script performs the following steps:
1. Download the participants.tsv file from OpenNeuro (if not already cached).
2. Parse the TSV and identify subjects that have non‑null MMSE and MOCA scores
   at *both* timepoints (i.e., at least two sessions with both scores present).
3. Limit the eligible set to N = min(100, number of eligible subjects).
4. Write `data/processed/eligible_subjects.csv` containing the selected subject IDs.
5. Write `data/processed/excluded_subjects.log` documenting why each
   non‑eligible subject was excluded.

Exit codes:
- 0 : success
- 2 : no eligible subjects found
- 3 : unrecoverable error during download / parsing
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests

from utils.logger import get_logger

# --------------------------------------------------------------------------- #
# Configuration constants
# --------------------------------------------------------------------------- #
DATASET_ID = "ds000246"
VERSION = "1.0.0"
PARTICIPANTS_URL = (
    f"https://openneuro.org/crn/datasets/{DATASET_ID}/versions/{VERSION}"
    "/files/participants.tsv?download"
)
CACHE_DIR = Path("data/raw") / DATASET_ID
PROCESSED_DIR = Path("data/processed")
ELIGIBLE_CSV = PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = PROCESSED_DIR / "excluded_subjects.log"
MAX_SUBJECTS = 100
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #


def download_file(url: str, dest: Path) -> None:
    """Download a file with simple retry logic.

    Parameters
    ----------
    url: str
        URL to download.
    dest: Path
        Destination path on local disk (parents are created automatically).
    """
    logger = get_logger("download_file")
    logger.info("Downloading %s to %s", url, dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info("Download succeeded on attempt %s", attempt)
            return
        except Exception as exc:  # pragma: no cover – network failures are rare in tests
            logger.warning("Attempt %s failed: %s", attempt, exc)
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
            else:
                logger.error("All download attempts failed.")
                raise


def read_participants_tsv(path: Path) -> List[Dict[str, str]]:
    """Read participants.tsv and return a list of dict rows."""
    logger = get_logger("read_participants_tsv")
    logger.info("Reading participants TSV from %s", path)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = [row for row in reader]
    logger.info("Read %d rows from participants.tsv", len(rows))
    return rows


def _has_valid_scores(row: Dict[str, str]) -> bool:
    """Return True if both MMSE and MOCA columns are non‑empty."""
    mmse = row.get("mmse", "").strip()
    moca = row.get("moca", "").strip()
    return bool(mmse) and bool(moca)


def filter_eligible_subjects(
    rows: List[Dict[str, str]]
) -> Tuple[List[str], Dict[str, str]]:
    """
    Identify subjects with non‑null MMSE and MOCA at *both* timepoints.

    Returns
    -------
    eligible: list of participant IDs
    excluded: dict mapping participant ID -> reason string
    """
    logger = get_logger("filter_eligible_subjects")
    logger.info("Filtering eligible subjects")
    # Group rows by participant_id
    groups: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        pid = row.get("participant_id") or row.get("subject_id") or row.get("participant")
        if not pid:
            continue
        groups.setdefault(pid, []).append(row)

    eligible: List[str] = []
    excluded: Dict[str, str] = {}

    for pid, sessions in groups.items():
        # Count sessions with both scores present
        valid_sessions = [s for s in sessions if _has_valid_scores(s)]
        if len(valid_sessions) >= 2:
            eligible.append(pid)
        else:
            reason = (
                f"Only {len(valid_sessions)} session(s) with complete MMSE/MOCA"
            )
            excluded[pid] = reason
    logger.info(
        "Found %d eligible subjects, %d excluded subjects",
        len(eligible),
        len(excluded),
    )
    return eligible, excluded


def limit_subjects(eligible: List[str], max_n: int = MAX_SUBJECTS) -> List[str]:
    """Return at most `max_n` subject IDs, preserving order."""
    logger = get_logger("limit_subjects")
    limited = eligible[:max_n]
    logger.info("Limiting subjects to %d (requested max %d)", len(limited), max_n)
    return limited


def write_outputs(
    eligible: List[str],
    excluded: Dict[str, str],
    eligible_path: Path = ELIGIBLE_CSV,
    excluded_path: Path = EXCLUDED_LOG,
) -> None:
    """Write CSV of eligible IDs and a log of excluded IDs."""
    logger = get_logger("write_outputs")
    logger.info("Writing eligible subjects to %s", eligible_path)
    eligible_path.parent.mkdir(parents=True, exist_ok=True)
    with open(eligible_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id"])
        for pid in eligible:
            writer.writerow([pid])

    logger.info("Writing excluded subjects log to %s", excluded_path)
    with open(excluded_path, "w", encoding="utf-8") as f:
        for pid, reason in excluded.items():
            f.write(f"{pid}: {reason}\\n")


def main() -> int:
    """Entry point for the script."""
    logger = get_logger("01_download_and_filter")
    try:
        # Step 1: download participants.tsv (cached)
        participants_path = CACHE_DIR / "participants.tsv"
        if not participants_path.is_file():
            download_file(PARTICIPANTS_URL, participants_path)
        else:
            logger.info("Using cached participants.tsv at %s", participants_path)

        # Step 2: read TSV
        rows = read_participants_tsv(participants_path)

        # Step 3: filter eligible subjects
        eligible, excluded = filter_eligible_subjects(rows)

        if not eligible:
            logger.error("No eligible subjects found – exiting with code 2")
            return 2  # EXIT_CODE_NO_LABELS as per spec

        # Step 4: limit to N
        limited = limit_subjects(eligible, MAX_SUBJECTS)

        # Step 5: write outputs
        write_outputs(limited, excluded)

        logger.info("Download and filter completed successfully.")
        return 0
    except Exception as exc:  # pragma: no cover – unexpected errors
        logger.error("Unexpected error in 01_download_and_filter: %s", exc)
        return 3  # generic failure


if __name__ == "__main__":
    sys.exit(main())