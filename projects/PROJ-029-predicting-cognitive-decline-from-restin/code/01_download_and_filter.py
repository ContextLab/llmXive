"""01_download_and_filter.py
Download OpenNeuro dataset ds000246, parse participants.tsv, filter subjects with
non‑null MMSE or MOCA scores at both timepoints, limit to at most 100 subjects,
and write eligibility reports.
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests

# Use the unified logger implementation (tolerant logger) from utils.logger
from utils.logger import get_logger, log_operation

# Constants
DATASET_URL = "https://openneuro.org/crn/datasets/ds000246/files/participants.tsv?download=1"
RAW_DATA_DIR = Path("data/raw/ds000246")
PROCESSED_DIR = Path("data/processed")
ELIGIBLE_CSV = PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = PROCESSED_DIR / "excluded_subjects.log"
EXIT_CODE_NO_ELIGIBLE = 2
MAX_SUBJECTS = 100


def ensure_dir(p: Path) -> None:
    """Create directory ``p`` if it does not exist."""
    p.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path, retries: int = 3, backoff: int = 5) -> None:
    """Download a file with simple retry logic."""
    logger = get_logger("download")
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Downloading {url} (attempt {attempt})")
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info(f"Saved to {dest}")
            return
        except Exception as exc:
            logger.warning(f"Download attempt {attempt} failed: {exc}")
            if attempt < retries:
                time.sleep(backoff * attempt)
    logger.error(f"Failed to download {url} after {retries} attempts")
    raise RuntimeError(f"Could not download {url}")


def read_participants_tsv(path: Path) -> List[Dict[str, str]]:
    """Read participants.tsv into a list of dictionaries."""
    logger = get_logger("participants_read")
    logger.info(f"Reading participants file: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = [row for row in reader]
    logger.info(f"Found {len(rows)} participants")
    return rows


def _has_nonnull_score(row: Dict[str, str], prefix: str) -> bool:
    """Return True if both time‑point columns for a given prefix are non‑empty."""
    # Accept common column names; be tolerant to missing columns.
    tp1 = row.get(f"{prefix}_T1") or row.get(f"{prefix}_1") or row.get(f"{prefix}1")
    tp2 = row.get(f"{prefix}_T2") or row.get(f"{prefix}_2") or row.get(f"{prefix}2")
    return bool(tp1 and tp1.strip()) and bool(tp2 and tp2.strip())


def is_eligible(row: Dict[str, str]) -> bool:
    """Determine eligibility based on MMSE or MOCA scores at both timepoints."""
    # Check MMSE first, then MOCA. If either pair is present and non‑null, accept.
    if _has_nonnull_score(row, "MMSE"):
        return True
    if _has_nonnull_score(row, "MOCA"):
        return True
    return False


def filter_eligible_subjects(
    rows: List[Dict[str, str]]
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Split rows into eligible and excluded lists."""
    eligible = []
    excluded = []
    for row in rows:
        if is_eligible(row):
            eligible.append(row)
        else:
            excluded.append(row)
    return eligible, excluded


def limit_subjects(
    eligible: List[Dict[str, str]], limit: int = MAX_SUBJECTS
) -> List[Dict[str, str]]:
    """Return at most ``limit`` eligible subjects (preserving order)."""
    return eligible[: min(limit, len(eligible))]


def write_eligible_csv(eligible: List[Dict[str, str]], out_path: Path) -> None:
    """Write eligible subjects to CSV (tab‑separated for consistency)."""
    logger = get_logger("eligible_write")
    if not eligible:
        logger.warning("No eligible subjects to write.")
        return
    fieldnames = list(eligible[0].keys())
    logger.info(f"Writing {len(eligible)} eligible subjects to {out_path}")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=",")
        writer.writeheader()
        for row in eligible:
            writer.writerow(row)


def write_excluded_log(excluded: List[Dict[str, str]], out_path: Path) -> None:
    """Write a simple log listing excluded participant IDs and reasons."""
    logger = get_logger("excluded_write")
    logger.info(f"Writing excluded log with {len(excluded)} entries to {out_path}")
    with open(out_path, "w", encoding="utf-8") as f:
        for row in excluded:
            pid = row.get("participant_id") or row.get("sub") or "UNKNOWN"
            f.write(f"{pid}\\n")


@log_operation("run_download_and_filter")
def main() -> None:
    """Orchestrate download, filtering, and output generation."""
    logger = get_logger("01_download_and_filter")

    # Ensure directories exist
    ensure_dir(RAW_DATA_DIR)
    ensure_dir(PROCESSED_DIR)

    participants_path = RAW_DATA_DIR / "participants.tsv"

    # Download participants.tsv if missing
    if not participants_path.is_file():
        try:
            download_file(DATASET_URL, participants_path)
        except Exception as exc:
            logger.error(f"Failed to obtain participants.tsv: {exc}")
            sys.exit(1)

    # Load participants
    rows = read_participants_tsv(participants_path)

    # Filter
    eligible, excluded = filter_eligible_subjects(rows)

    # Apply limit
    limited_eligible = limit_subjects(eligible, MAX_SUBJECTS)

    # Write outputs
    write_eligible_csv(limited_eligible, ELIGIBLE_CSV)
    write_excluded_log(excluded, EXCLUDED_LOG)

    # Exit with specific code if no eligible subjects
    if not limited_eligible:
        logger.error("No eligible subjects found after filtering.")
        sys.exit(EXIT_CODE_NO_ELIGIBLE)

    logger.info(
        f"Processing complete: {len(limited_eligible)} eligible, {len(excluded)} excluded."
    )


if __name__ == "__main__":
    main()
