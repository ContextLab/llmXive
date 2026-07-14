"""01_download_and_filter.py
Download OpenNeuro dataset ds000246, parse participants.tsv, filter subjects
with non‑null MMSE and MoCA scores at both timepoints, limit to at most 100
eligible subjects, and write the results to disk.
"""

from __future__ import annotations

import csv
import io
import sys
import zipfile
import random
import json
from pathlib import Path
from typing import List, Dict

import requests

# Use the robust logger defined in utils.logger (tolerant to many call signatures)
from utils.logger import get_logger

logger = get_logger(__name__)


DATA_ROOT = Path("data")
RAW_ROOT = DATA_ROOT / "raw" / "ds000246"
PROCESSED_ROOT = DATA_ROOT / "processed"


def ensure_directory(path: Path) -> None:
    """Create a directory (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {path}")


def download_file(url: str, dest: Path, retries: int = 3, backoff: float = 2.0) -> None:
    """Download a file from *url* to *dest* with simple retry logic."""
    ensure_directory(dest.parent)
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Downloading {url} (attempt {attempt})")
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info(f"Successfully downloaded to {dest}")
            return
        except Exception as exc:
            logger.warning(f"Download attempt {attempt} failed: {exc}")
            if attempt == retries:
                raise
            time.sleep(backoff * attempt)


def read_participants_tsv(tsv_path: Path) -> List[Dict[str, str]]:
    """Read the participants.tsv file and return a list of dict rows."""
    logger.info(f"Reading participants file: {tsv_path}")
    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = [dict(row) for row in reader]
    logger.info(f"Found {len(rows)} participants")
    return rows


def _has_nonempty(value: str | None) -> bool:
    """Utility: True if *value* is not None/empty after stripping."""
    return bool(value and value.strip())


def is_eligible(row: Dict[str, str]) -> bool:
    """
    Determine eligibility:
    - Must contain a non‑empty MMSE column.
    - Must contain a non‑empty MoCA column.
    The exact column names can vary in case; we look for any column that
    contains the substrings ``mmse`` or ``moca`` (case‑insensitive).
    """
    mmse_keys = [k for k in row.keys() if "mmse" in k.lower()]
    moca_keys = [k for k in row.keys() if "moca" in k.lower()]

    if not mmse_keys or not moca_keys:
        return False

    # Require at least one non‑empty entry for each score type
    has_mmse = any(_has_nonempty(row.get(k)) for k in mmse_keys)
    has_moca = any(_has_nonempty(row.get(k)) for k in moca_keys)

    return has_mmse and has_moca


def filter_eligible_subjects(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Return only rows that satisfy :func:`is_eligible`."""
    eligible = [row for row in rows if is_eligible(row)]
    logger.info(f"{len(eligible)} subjects are eligible out of {len(rows)} total")
    return eligible


def limit_subjects(rows: List[Dict[str, str]], max_n: int = 100) -> List[Dict[str, str]]:
    """Limit the list to at most *max_n* entries (preserving order)."""
    limited = rows[:max_n]
    if len(rows) > max_n:
        logger.info(f"Limiting subjects from {len(rows)} to {max_n}")
    return limited


def write_eligible_csv(rows: List[Dict[str, str]], out_path: Path) -> None:
    """Write *rows* to a CSV containing only the participant identifier."""
    ensure_directory(out_path.parent)
    fieldnames = ["participant_id"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            pid = row.get("participant_id") or row.get("sub")
            if not pid:
                # Fallback: use the first column value
                pid = next(iter(row.values()))
            writer.writerow({"participant_id": pid})
    logger.info(f"Wrote eligible subjects CSV to {out_path}")


def write_excluded_log(excluded_rows: List[Dict[str, str]], out_path: Path) -> None:
    """Write a simple log listing excluded subject IDs."""
    ensure_directory(out_path.parent)
    with open(out_path, "w", encoding="utf-8") as f:
        for row in excluded_rows:
            pid = row.get("participant_id") or row.get("sub") or "UNKNOWN"
            f.write(f"Excluded subject {pid}: missing MMSE or MoCA score\\n")
    logger.info(f"Wrote excluded subjects log to {out_path}")


def main() -> None:
    """
    Orchestrate the download‑and‑filter pipeline.

    Exit codes:
        0 – success
        2 – no eligible subjects found
        1 – other errors
    """
    try:
        # 1️⃣ Ensure directories exist
        ensure_directory(RAW_ROOT)
        ensure_directory(PROCESSED_ROOT)

        # 2️⃣ Download participants.tsv if not already present
        participants_url = (
            "https://openneuro.org/crn/datasets/ds000246/versions/1.0.0/files/participants.tsv?download"
        )
        participants_path = RAW_ROOT / "participants.tsv"
        if not participants_path.is_file():
            download_file(participants_url, participants_path)
        else:
            logger.info(f"participants.tsv already present at {participants_path}")

        # 3️⃣ Parse TSV
        all_rows = read_participants_tsv(participants_path)

        # 4️⃣ Filter eligible subjects
        eligible_rows = filter_eligible_subjects(all_rows)
        excluded_rows = [r for r in all_rows if r not in eligible_rows]

        # 5️⃣ Abort if none eligible
        if not eligible_rows:
            logger.error("No eligible subjects found – exiting with code 2")
            sys.exit(2)

        # 6️⃣ Limit to at most 100 subjects
        eligible_limited = limit_subjects(eligible_rows, max_n=100)

        # 7️⃣ Write outputs
        eligible_csv_path = PROCESSED_ROOT / "eligible_subjects.csv"
        excluded_log_path = PROCESSED_ROOT / "excluded_subjects.log"

        write_eligible_csv(eligible_limited, eligible_csv_path)
        write_excluded_log(excluded_rows, excluded_log_path)

        logger.info("Download and filter step completed successfully.")
        sys.exit(0)

    except Exception as exc:
        logger.error(f"Unexpected error in download_and_filter: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
