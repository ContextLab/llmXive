"""Download OpenNeuro ds000246 participants.tsv and filter eligible subjects.

This script performs the following steps:
1. Ensure the raw data directory exists.
2. Download the participants.tsv file from the OpenNeuro GitHub mirror.
3. Parse the TSV into a list of dictionaries.
4. Keep subjects that have non‑null MMSE or MOCA scores at both baseline and follow‑up.
5. Limit the number of eligible subjects to N = min(100, available).
6. Write the list of eligible subject IDs to `data/processed/eligible_subjects.csv`.
7. Write a log of excluded subject IDs (and reasons) to `data/processed/excluded_subjects.log`.
8. Exit with code 2 if no eligible subjects are found.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import requests

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def ensure_directory(path: Path) -> None:
    """Create ``path`` (and parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest_path: Path) -> None:
    """Download ``url`` to ``dest_path`` using a streaming request."""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except Exception as exc:
        print(f"Failed to download {url!r}: {exc}", file=sys.stderr)
        raise


def read_participants_tsv(tsv_path: Path) -> List[Dict[str, str]]:
    """Read a TSV file and return a list of rows as dictionaries."""
    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [row for row in reader]


# ----------------------------------------------------------------------
# Eligibility logic
# ----------------------------------------------------------------------


def _extract_score(row: Dict[str, str], prefix: str) -> str | None:
    """Return the first non‑empty score for a given ``prefix`` (e.g. 'mmse')."""
    for suffix in ("_baseline", "_followup"):
        key = f"{prefix}{suffix}"
        if key in row and row[key].strip():
            return row[key].strip()
    return None


def has_valid_score(row: Dict[str, str]) -> bool:
    """Return ``True`` if the subject has a non‑null MMSE **or** MOCA at *both* timepoints.

    The function looks for columns named ``mmse_baseline``, ``mmse_followup``,
    ``moca_baseline`` and ``moca_followup``.  If either the MMSE pair or the
    MOCA pair is complete (both baseline and follow‑up present), the subject is
    considered eligible.
    """
    # Try MMSE first
    mmse_baseline = row.get("mmse_baseline", "").strip()
    mmse_followup = row.get("mmse_followup", "").strip()
    if mmse_baseline and mmse_followup:
        return True

    # Then MOCA
    moca_baseline = row.get("moca_baseline", "").strip()
    moca_followup = row.get("moca_followup", "").strip()
    if moca_baseline and moca_followup:
        return True

    return False


def is_eligible(row: Dict[str, str]) -> bool:
    """Wrapper that can be extended later; currently delegates to ``has_valid_score``."""
    return has_valid_score(row)


def filter_eligible_subjects(
    rows: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], List[Tuple[Dict[str, str], str]]]:
    """Separate ``rows`` into eligible and excluded subjects.

    Returns:
        (eligible_rows, excluded_rows_with_reason)
    """
    eligible: List[Dict[str, str]] = []
    excluded: List[Tuple[Dict[str, str], str]] = []

    for row in rows:
        if is_eligible(row):
            eligible.append(row)
        else:
            reason = "missing required MMSE/MOCA scores at both timepoints"
            excluded.append((row, reason))
    return eligible, excluded


def limit_subjects(eligible: List[Dict[str, str]], max_n: int = 100) -> List[Dict[str, str]]:
    """Return at most ``max_n`` subjects, preserving the original order."""
    return eligible[:max_n]


# ----------------------------------------------------------------------
# Output helpers
# ----------------------------------------------------------------------


def write_eligible_csv(eligible: List[Dict[str, str]], out_path: Path) -> None:
    """Write ``eligible`` subject IDs to a CSV file.

    The CSV contains a single column ``participant_id``.
    """
    ensure_directory(out_path.parent)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id"])
        for row in eligible:
            # OpenNeuro uses the ``participant_id`` column (e.g. ``sub-01``)
            pid = row.get("participant_id") or row.get("sub")
            writer.writerow([pid])


def write_excluded_log(
    excluded: List[Tuple[Dict[str, str], str]], out_path: Path
) -> None:
    """Write a plain‑text log of excluded subjects and the reason for exclusion."""
    ensure_directory(out_path.parent)
    with open(out_path, "w", encoding="utf-8") as f:
        for row, reason in excluded:
            pid = row.get("participant_id") or row.get("sub")
            f.write(f"{pid}: {reason}\n")


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------


EXIT_CODE_NO_LABELS = 2
PARTICIPANTS_URL = (
    "https://raw.githubusercontent.com/OpenNeuroDatasets/ds000246/master/participants.tsv"
)
RAW_DATA_DIR = Path("data/raw/ds000246")
PROCESSED_DIR = Path("data/processed")


def main() -> None:
    """Entry point for the script."""
    # 1. Ensure directories exist
    ensure_directory(RAW_DATA_DIR)
    ensure_directory(PROCESSED_DIR)

    participants_tsv_path = RAW_DATA_DIR / "participants.tsv"

    # 2. Download participants.tsv if it does not already exist
    if not participants_tsv_path.is_file():
        print(f"Downloading participants.tsv from {PARTICIPANTS_URL} ...")
        try:
            download_file(PARTICIPANTS_URL, participants_tsv_path)
        except Exception:
            sys.exit(1)
    else:
        print(f"Found existing participants.tsv at {participants_tsv_path}")

    # 3. Parse TSV
    rows = read_participants_tsv(participants_tsv_path)

    # 4. Filter eligible / excluded
    eligible, excluded = filter_eligible_subjects(rows)

    # 5. Apply the subject limit (N = min(100, available_eligible))
    limited_eligible = limit_subjects(eligible, max_n=100)

    # 6. Write outputs
    eligible_csv_path = PROCESSED_DIR / "eligible_subjects.csv"
    excluded_log_path = PROCESSED_DIR / "excluded_subjects.log"

    write_eligible_csv(limited_eligible, eligible_csv_path)
    write_excluded_log(excluded, excluded_log_path)

    # 7. Exit with proper code if no eligible subjects
    if not limited_eligible:
        print("No eligible subjects found – exiting with code 2.", file=sys.stderr)
        sys.exit(EXIT_CODE_NO_LABELS)

    print(f"Wrote {len(limited_eligible)} eligible subjects to {eligible_csv_path}")
    print(f"Wrote {len(excluded)} excluded subjects to {excluded_log_path}")


if __name__ == "__main__":
    main()
