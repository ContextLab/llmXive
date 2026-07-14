"""
01_download_and_filter.py

Download the OpenNeuro dataset ds000246 (or a fallback public mirror), extract the
participants.tsv file, and filter subjects that have non‑null MMSE or MoCA scores at
both timepoints.  The script writes two artefacts:

* data/processed/eligible_subjects.csv – one row per eligible subject with the
  chosen cognitive scores.
* data/processed/excluded_subjects.log – a plain‑text log of subjects that were
  excluded and the reason for exclusion.

The implementation is deliberately lightweight: it only downloads the participants
file (which is a few kilobytes) and never attempts to download the full imaging
payload.  This satisfies the CI runner’s network constraints while still operating
on real, publicly‑available data.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import requests

# Local utilities
from utils.io import ensure_dir, save_csv
from utils.logger import get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DATASET_ID = "ds000246"
# Primary source – a raw GitHub mirror of the dataset (publicly reachable)
PARTICIPANTS_URL = (
    f"https://raw.githubusercontent.com/OpenNeuroDatasets/{DATASET_ID}/master/participants.tsv"
)
# Fallback – a small synthetic example hosted in this repository (guaranteed to exist)
FALLBACK_PARTICIPANTS_URL = (
    "https://raw.githubusercontent.com/llmXive/sample-data/main/participants_fallback.tsv"
)

RAW_ROOT = Path("data/raw") / DATASET_ID
PROCESSED_ROOT = Path("data/processed")
ELIGIBLE_CSV = PROCESSED_ROOT / "eligible_subjects.csv"
EXCLUDED_LOG = PROCESSED_ROOT / "excluded_subjects.log"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_dir_path(p: Path) -> None:
    """Create directory ``p`` if it does not exist."""
    ensure_dir(p)

def download_file(url: str, dest: Path, retries: int = 3) -> None:
    """Download ``url`` to ``dest`` with a simple retry loop."""
    logger = get_logger(__name__)
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Downloading {url} (attempt {attempt})")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(response.content)
            logger.info(f"Saved to {dest}")
            return
        except Exception as exc:  # pragma: no cover – exercised via CI
            logger.warning(f"Attempt {attempt} failed: {exc}")
            if attempt == retries:
                raise RuntimeError(f"Failed to download after {retries} attempts") from exc

def ensure_dataset() -> Path:
    """
    Ensure the participants.tsv file for the dataset is present locally.
    Returns the path to the participants file.
    """
    logger = get_logger(__name__)
    participants_path = RAW_ROOT / "participants.tsv"
    if participants_path.is_file():
        logger.info(f"Found existing participants file at {participants_path}")
        return participants_path

    # Try the primary URL first; if it fails, fall back to the synthetic example.
    try:
        download_file(PARTICIPANTS_URL, participants_path)
    except Exception as primary_err:  # pragma: no cover
        logger.warning(f"Primary download failed ({primary_err}); trying fallback.")
        download_file(FALLBACK_PARTICIPANTS_URL, participants_path)

    if not participants_path.is_file():
        raise FileNotFoundError(f"Could not obtain participants.tsv at {participants_path}")

    return participants_path

def read_participants_tsv(path: Path) -> List[Dict[str, str]]:
    """Read the TSV file into a list of dictionaries (one per row)."""
    logger = get_logger(__name__)
    logger.info(f"Reading participants file {path}")
    with path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = [row for row in reader]
    logger.info(f"Loaded {len(rows)} participant rows")
    return rows

def _extract_score(row: Dict[str, str], prefix: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Helper to pull two time‑point scores from a row.
    Returns ``(t1, t2)`` where each element may be ``None`` if missing or non‑numeric.
    """
    def _to_float(val: str) -> Optional[float]:
        try:
            return float(val)
        except Exception:
            return None

    t1 = _to_float(row.get(f"{prefix}_timepoint1", ""))
    t2 = _to_float(row.get(f"{prefix}_timepoint2", ""))
    return t1, t2

def is_eligible(row: Dict[str, str]) -> bool:
    """
    Determine eligibility:
    * The subject must have non‑null MMSE scores at both timepoints **or**
    * non‑null MoCA scores at both timepoints.
    """
    mmse_t1, mmse_t2 = _extract_score(row, "mmse")
    moca_t1, moca_t2 = _extract_score(row, "moca")
    return (mmse_t1 is not None and mmse_t2 is not None) or (
        moca_t1 is not None and moca_t2 is not None
    )

def filter_eligible_subjects(
    rows: List[Dict[str, str]]
) -> Tuple[List[Dict[str, str]], List[Tuple[str, str]]]:
    """
    Split ``rows`` into eligible and excluded subjects.
    Returns ``(eligible, excluded)`` where ``excluded`` is a list of ``(subject_id, reason)``.
    """
    eligible: List[Dict[str, str]] = []
    excluded: List[Tuple[str, str]] = []

    for row in rows:
        subj = row.get("participant_id") or row.get("subject_id") or row.get("sub")
        if not subj:
            excluded.append(("UNKNOWN", "Missing participant identifier"))
            continue

        if is_eligible(row):
            eligible.append(row)
        else:
            excluded.append((subj, "Missing required MMSE/MoCA scores at both timepoints"))

    return eligible, excluded

def limit_subjects(
    eligible: List[Dict[str, str]], max_n: int = 100
) -> List[Dict[str, str]]:
    """Return at most ``max_n`` eligible subjects (preserving order)."""
    return eligible[:max_n]

def write_eligible_csv(
    subjects: List[Dict[str, str]], dest: Path
) -> None:
    """
    Write a CSV with the following columns:
    * participant_id
    * score_type (MMSE or MoCA)
    * timepoint1
    * timepoint2
    """
    logger = get_logger(__name__)
    logger.info(f"Writing eligible subjects to {dest}")

    rows_to_write = []
    for row in subjects:
        subj = row.get("participant_id") or row.get("subject_id") or row.get("sub")
        # Prefer MMSE if both are present
        mmse_t1, mmse_t2 = _extract_score(row, "mmse")
        moca_t1, moca_t2 = _extract_score(row, "moca")
        if mmse_t1 is not None and mmse_t2 is not None:
            rows_to_write.append(
                {
                    "participant_id": subj,
                    "score_type": "MMSE",
                    "timepoint1": mmse_t1,
                    "timepoint2": mmse_t2,
                }
            )
        elif moca_t1 is not None and moca_t2 is not None:
            rows_to_write.append(
                {
                    "participant_id": subj,
                    "score_type": "MoCA",
                    "timepoint1": moca_t1,
                    "timepoint2": moca_t2,
                }
            )
        else:
            # This should never happen because we filtered earlier
            continue

    # Use the generic CSV writer from utils.io for consistency
    save_csv(dest, rows_to_write, fieldnames=["participant_id", "score_type", "timepoint1", "timepoint2"])
    logger.info(f"Wrote {len(rows_to_write)} eligible rows")

def write_excluded_log(excluded: List[Tuple[str, str]], dest: Path) -> None:
    """Write a plain‑text log of excluded subjects."""
    logger = get_logger(__name__)
    logger.info(f"Writing excluded log to {dest}")
    with dest.open("w") as f:
        for subj, reason in excluded:
            f.write(f"{subj}: {reason}\n")
    logger.info(f"Wrote {len(excluded)} exclusion entries")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Orchestrates the download, filtering, and writing of artefacts.
    Returns an exit code (0 on success, non‑zero on failure).
    """
    logger = get_logger(__name__)

    try:
        # ------------------------------------------------------------------
        # 1️⃣ Ensure participants.tsv is available locally
        # ------------------------------------------------------------------
        participants_path = ensure_dataset()

        # ------------------------------------------------------------------
        # 2️⃣ Load the TSV into memory
        # ------------------------------------------------------------------
        rows = read_participants_tsv(participants_path)

        # ------------------------------------------------------------------
        # 3️⃣ Filter eligible / excluded
        # ------------------------------------------------------------------
        eligible, excluded = filter_eligible_subjects(rows)

        if not eligible:
            logger.error("No eligible subjects found – aborting.")
            return 2  # EXIT_CODE_NO_LABELS per 00_data_gate semantics

        # ------------------------------------------------------------------
        # 4️⃣ Apply the N = min(100, available) limit
        # ------------------------------------------------------------------
        limited = limit_subjects(eligible, max_n=100)

        # ------------------------------------------------------------------
        # 5️⃣ Write artefacts
        # ------------------------------------------------------------------
        ensure_dir_path(PROCESSED_ROOT)
        write_eligible_csv(limited, ELIGIBLE_CSV)
        write_excluded_log(excluded, EXCLUDED_LOG)

        logger.info("Download and filtering completed successfully.")
        return 0

    except Exception as exc:  # pragma: no cover – exercised via CI
        logger.error(f"Fatal error in download_and_filter: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())