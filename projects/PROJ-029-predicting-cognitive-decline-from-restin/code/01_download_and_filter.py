"""Download OpenNeuro ds000246, filter participants, and write eligibility files.

This script performs the following steps:
1. Ensure the raw data directory exists.
2. Download the ds000246 dataset as a zip (if not already present).
3. Extract the zip to the raw data directory.
4. Read the BIDS participants.tsv file.
5. Determine eligibility: subjects must have non‑null MMSE or MOCA scores
   at **both** timepoints (baseline and follow‑up).
6. Limit the eligible set to at most 100 subjects (random seed = 42).
7. Write `eligible_subjects.csv` and `excluded_subjects.log` to
   `data/processed/`.

The script exits with status code 2 if no eligible subjects are found.
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

from utils.logger import get_logger

# Constants
DATASET_URL = "https://openneuro.org/crn/dataset/ds000246/download?format=zip"
RAW_DATA_DIR = Path("data/raw/ds000246")
ZIP_PATH = RAW_DATA_DIR.with_suffix(".zip")
PROCESSED_DIR = Path("data/processed")
ELIGIBLE_CSV = PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = PROCESSED_DIR / "excluded_subjects.log"
MAX_SUBJECTS = 100
EXIT_CODE_NO_LABELS = 2


def ensure_dir(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    get_logger("download_and_filter").log("dir_ensured", path=str(path))


def download_file(url: str, dest: Path) -> None:
    """Download a file with streaming and write to dest."""
    logger = get_logger("download_file")
    logger.log("start_download", url=url, dest=str(dest))
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.log("download_complete", dest=str(dest))


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract a zip archive to a target directory."""
    logger = get_logger("extract_zip")
    logger.log("start_extract", zip_path=str(zip_path), extract_to=str(extract_to))
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    logger.log("extract_complete", extract_to=str(extract_to))


def read_participants_tsv(tsv_path: Path) -> List[Dict[str, str]]:
    """Read participants.tsv and return a list of dict rows."""
    logger = get_logger("read_participants_tsv")
    logger.log("read_start", path=str(tsv_path))
    with tsv_path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = [row for row in reader]
    logger.log("read_complete", rows=len(rows))
    return rows


def _score_is_valid(value: str) -> bool:
    """Return True if a score string is non‑empty and not 'n/a'."""
    return value is not None and value.strip() != "" and value.strip().lower() not in {"n/a", "na", "nan"}


def is_eligible(subject_rows: List[Dict[str, str]]) -> bool:
    """Determine eligibility based on MMSE/MOCA scores at two timepoints.

    A subject is eligible if **both** sessions contain at least one
    non‑null score among the MMSE or MOCA columns.
    """
    # Identify score columns (case‑insensitive)
    score_cols = [col for col in subject_rows[0].keys() if "mmse" in col.lower() or "moca" in col.lower()]
    if not score_cols:
        return False  # No score columns present

    valid_counts = 0
    for row in subject_rows:
        if any(_score_is_valid(row.get(col, "")) for col in score_cols):
            valid_counts += 1
    return valid_counts >= 2  # need at least two timepoints with data


def filter_eligible_subjects(all_rows: List[Dict[str, str]]) -> (List[str], List[str]):
    """Return a tuple of (eligible_subject_ids, exclusion_reasons)."""
    logger = get_logger("filter_eligible_subjects")
    # Group rows by participant_id
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in all_rows:
        pid = row.get("participant_id") or row.get("sub") or row.get("subject_id")
        if not pid:
            continue
        grouped.setdefault(pid, []).append(row)

    eligible: List[str] = []
    excluded: List[str] = []
    for pid, rows in grouped.items():
        if is_eligible(rows):
            eligible.append(pid)
            logger.log("subject_eligible", participant_id=pid)
        else:
            reason = "Insufficient MMSE/MOCA data across sessions"
            excluded.append(f"{pid}: {reason}")
            logger.log("subject_excluded", participant_id=pid, reason=reason)
    return eligible, excluded


def limit_subjects(subject_ids: List[str], max_n: int = MAX_SUBJECTS) -> List[str]:
    """Randomly limit the list to at most max_n entries (seeded)."""
    logger = get_logger("limit_subjects")
    if len(subject_ids) <= max_n:
        logger.log("no_limit_needed", total=len(subject_ids))
        return subject_ids
    random.seed(42)
    limited = random.sample(subject_ids, max_n)
    logger.log("subjects_limited", original=len(subject_ids), limited=len(limited))
    return limited


def write_eligible_csv(subject_ids: List[str], out_path: Path) -> None:
    """Write eligible subject IDs to a CSV with a single column."""
    logger = get_logger("write_eligible_csv")
    logger.log("write_start", path=str(out_path), count=len(subject_ids))
    ensure_dir(out_path.parent)
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id"])
        for pid in subject_ids:
            writer.writerow([pid])
    logger.log("write_complete", path=str(out_path))


def write_excluded_log(exclusions: List[str], out_path: Path) -> None:
    """Write exclusion reasons to a plain‑text log file."""
    logger = get_logger("write_excluded_log")
    logger.log("log_start", path=str(out_path), entries=len(exclusions))
    ensure_dir(out_path.parent)
    with out_path.open("w") as f:
        for line in exclusions:
            f.write(line + "\n")
    logger.log("log_complete", path=str(out_path))


def main() -> None:
    """Orchestrate the download, extraction, and filtering pipeline."""
    logger = get_logger("01_download_and_filter")
    logger.log("pipeline_start")

    # 1. Ensure directories exist
    ensure_dir(RAW_DATA_DIR)
    ensure_dir(PROCESSED_DIR)

    # 2. Download dataset if not already present
    if not ZIP_PATH.is_file():
        try:
            download_file(DATASET_URL, ZIP_PATH)
        except Exception as exc:
            logger.log("download_failed", error=str(exc))
            sys.exit(1)
    else:
        logger.log("zip_already_present", path=str(ZIP_PATH))

    # 3. Extract if not already extracted (check a known sub‑folder)
    expected_subdir = RAW_DATA_DIR / "sub-01"
    if not expected_subdir.is_dir():
        try:
            extract_zip(ZIP_PATH, RAW_DATA_DIR)
        except Exception as exc:
            logger.log("extract_failed", error=str(exc))
            sys.exit(1)
    else:
        logger.log("already_extracted", path=str(RAW_DATA_DIR))

    # 4. Load participants.tsv
    participants_path = RAW_DATA_DIR / "participants.tsv"
    if not participants_path.is_file():
        logger.log("participants_missing", path=str(participants_path))
        sys.exit(1)

    all_rows = read_participants_tsv(participants_path)

    # 5. Filter eligibility
    eligible_ids, exclusions = filter_eligible_subjects(all_rows)

    if not eligible_ids:
        logger.log("no_eligible_subjects")
        sys.exit(EXIT_CODE_NO_LABELS)

    # 6. Limit to MAX_SUBJECTS
    limited_ids = limit_subjects(eligible_ids, MAX_SUBJECTS)

    # 7. Write outputs
    write_eligible_csv(limited_ids, ELIGIBLE_CSV)
    write_excluded_log(exclusions, EXCLUDED_LOG)

    logger.log("pipeline_complete", eligible=len(limited_ids), excluded=len(exclusions))


if __name__ == "__main__":
    main()
