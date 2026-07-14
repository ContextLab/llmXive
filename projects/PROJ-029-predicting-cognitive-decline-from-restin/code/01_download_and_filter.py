"""Download OpenNeuro ds000246, filter participants, and write eligibility files."""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from tqdm import tqdm

from utils.logger import get_logger, log_operation

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def ensure_dir(path: Path) -> None:
    """Create ``path`` and any missing parents (idempotent)."""
    path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path, max_retries: int = 3) -> None:
    """
    Stream‑download ``url`` to ``dest`` with a progress bar.

    Retries up to ``max_retries`` times on network failures.
    """
    logger = get_logger("download_file")
    logger.info(f"Downloading {url} → {dest}")

    for attempt in range(1, max_retries + 1):
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                ensure_dir(dest.parent)
                with open(dest, "wb") as f, tqdm(
                    total=total,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=dest.name,
                    leave=False,
                ) as bar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))
            logger.info("Download succeeded")
            return
        except Exception as exc:  # pragma: no cover – network errors are rare in CI
            logger.warning(f"Attempt {attempt}/{max_retries} failed: {exc}")
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)  # exponential back‑off


def read_participants_tsv(tsv_path: Path) -> List[Dict[str, str]]:
    """
    Read a BIDS ``participants.tsv`` file and return a list of rows as dicts.
    Empty strings are normalised to ``None`` for easier eligibility checks.
    """
    logger = get_logger("read_participants_tsv")
    logger.info(f"Reading participants file {tsv_path}")
    rows: List[Dict[str, str]] = []
    with tsv_path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for raw in reader:
            cleaned = {k: (v.strip() if v.strip() != "" else None) for k, v in raw.items()}
            rows.append(cleaned)
    logger.info(f"Found {len(rows)} participants")
    return rows


def is_eligible(row: Dict[str, str]) -> bool:
    """
    Eligibility rule:
    - The row must contain *both* MMSE and MoCA scores (any column containing those substrings)
    - At least one non‑null value must be present for each test at *both* timepoints.

    The BIDS participants file often stores longitudinal scores as ``MMSE_1``,
    ``MMSE_2`` (similarly for MoCA).  We accept any column that starts with the
    test name followed by an underscore and a digit.
    """
    mmse_keys = [k for k in row if k.lower().startswith("mmse")]
    moca_keys = [k for k in row if k.lower().startswith("moca")]

    # Need at least two distinct timepoints for each test
    if len(mmse_keys) < 2 or len(moca_keys) < 2:
        return False

    # Verify that each required column has a non‑null value
    for key in mmse_keys + moca_keys:
        if row.get(key) in (None, "", "n/a"):
            return False
    return True


def filter_eligible_subjects(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Separate eligible and excluded rows."""
    eligible: List[Dict[str, str]] = []
    excluded: List[Dict[str, str]] = []
    for row in rows:
        if is_eligible(row):
            eligible.append(row)
        else:
            excluded.append(row)
    return eligible, excluded


def limit_subjects(subjects: List[Dict[str, str]], max_n: int = 100) -> List[Dict[str, str]]:
    """Return at most ``max_n`` subjects, preserving order."""
    return subjects[:max_n]


def write_eligible_csv(subjects: List[Dict[str, str]], out_path: Path) -> None:
    """Write ``eligible_subjects.csv`` with a minimal set of columns."""
    logger = get_logger("write_eligible_csv")
    logger.info(f"Writing {len(subjects)} eligible subjects to {out_path}")
    ensure_dir(out_path.parent)
    fieldnames = ["participant_id"] + sorted(
        {k for row in subjects for k in row if k != "participant_id"}
    )
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in subjects:
            writer.writerow(row)


def write_excluded_log(excluded: List[Dict[str, str]], out_path: Path) -> None:
    """Write a simple log file listing excluded participant IDs and reasons."""
    logger = get_logger("write_excluded_log")
    logger.info(f"Writing exclusion log for {len(excluded)} participants to {out_path}")
    ensure_dir(out_path.parent)
    with out_path.open("w") as f:
        for row in excluded:
            pid = row.get("participant_id", "UNKNOWN")
            f.write(f"{pid}\\tIneligible (missing MMSE/MoCA at one or more timepoints)\\n")


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------


@log_operation("01_download_and_filter")
def main() -> None:
    """
    End‑to‑end driver:
    1. Ensure raw data directory exists.
    2. Download ``participants.tsv`` from OpenNeuro.
    3. Parse, filter, limit, and write eligibility artefacts.
    """
    logger = get_logger("01_download_and_filter")

    # 1. Directory layout
    raw_dir = Path("data/raw/ds000246")
    ensure_dir(raw_dir)

    # 2. Download participants.tsv
    participants_url = (
        "https://openneuro.org/crn/datasets/ds000246/versions/1.0.0/files/participants.tsv?download=1"
    )
    participants_path = raw_dir / "participants.tsv"
    if not participants_path.is_file():
        try:
            download_file(participants_url, participants_path)
        except Exception as exc:
            logger.error(f"Failed to download participants.tsv: {exc}")
            sys.exit(1)
    else:
        logger.info("participants.tsv already present – skipping download")

    # 3. Load and filter
    rows = read_participants_tsv(participants_path)
    eligible, excluded = filter_eligible_subjects(rows)

    if not eligible:
        logger.error("No eligible participants found – exiting with code 2")
        # EXIT_CODE_NO_LABELS = 2 as defined in 00_data_gate.py
        sys.exit(2)

    # 4. Apply N limit
    limited = limit_subjects(eligible, max_n=100)

    # 5. Write artefacts
    processed_dir = Path("data/processed")
    write_eligible_csv(limited, processed_dir / "eligible_subjects.csv")
    write_excluded_log(excluded, processed_dir / "excluded_subjects.log")

    logger.info("Download and filtering completed successfully")


if __name__ == "__main__":
    main()
