"""
01_download_and_filter.py

Download the OpenNeuro ds000246 dataset (or at least the participants.tsv file),
filter subjects that have at least one cognitive score (MMSE or MOCA) present at
both time‑points, limit to a maximum of 100 eligible subjects, and write the
results to the processed data directory.

The script is deliberately lightweight – it only downloads the small
``participants.tsv`` file (≈ few KB) rather than the full imaging data.  All
downstream steps (graph construction, modelling, …) rely on the subject list
produced here.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import requests

# Local utilities ---------------------------------------------------------

# ``utils.logger`` provides a tolerant logger that works with any call shape.
# Importing it here ensures consistent logging across the pipeline.
from utils.logger import get_logger

# -------------------------------------------------------------------------

# Constants ----------------------------------------------------------------
DATASET_ID = "ds000246"
PARTICIPANTS_URL = (
    "https://raw.githubusercontent.com/OpenNeuroDatasets/ds000246/master/participants.tsv"
)
# Directory layout ---------------------------------------------------------
RAW_DIR = Path("data") / "raw" / DATASET_ID
PROCESSED_DIR = Path("data") / "processed"
ELIGIBLE_CSV = PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = PROCESSED_DIR / "excluded_subjects.log"

# Logging ------------------------------------------------------------------
logger = get_logger("download_and_filter")

# Helper functions ---------------------------------------------------------

def ensure_dir(p: Path) -> None:
    """Create ``p`` and all parents if they do not exist."""
    p.mkdir(parents=True, exist_ok=True)

def download_file(url: str, dest: Path, retries: int = 3, backoff: float = 2.0) -> None:
    """
    Download ``url`` to ``dest`` with simple exponential back‑off.

    Parameters
    ----------
    url: str
        Remote file URL.
    dest: Path
        Destination path (including filename).
    retries: int
        Number of retry attempts.
    backoff: float
        Multiplier for sleep time between retries.
    """
    ensure_dir(dest.parent)
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Attempt {attempt}: downloading {url}")
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info(f"Successfully downloaded to {dest}")
            return
        except Exception as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt == retries:
                logger.error(f"All {retries} attempts failed – aborting.")
                raise
            sleep_time = backoff ** attempt
            logger.info(f"Sleeping {sleep_time:.1f}s before retry.")
            time.sleep(sleep_time)

def read_participants_tsv(path: Path) -> pd.DataFrame:
    """
    Load the participants.tsv file into a DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with at least a ``participant_id`` column and any
        cognitive score columns (e.g. ``mmse_baseline``).
    """
    logger.info(f"Reading participants file from {path}")
    try:
        df = pd.read_csv(path, sep="\t", dtype=str)  # keep everything as strings
    except Exception as e:
        logger.error(f"Failed to read participants.tsv: {e}")
        raise
    return df

def _score_present(row: pd.Series, prefix: str) -> bool:
    """
    Helper: does a row contain a non‑null MMSE or MOCA score for the given
    ``prefix`` (e.g. ``baseline`` or ``followup``)?

    The dataset uses a variety of column naming conventions; we check a
    handful of common patterns.
    """
    mmse_col = f"mmse_{prefix}"
    moca_col = f"moca_{prefix}"
    # Some datasets use ``mmse``/``moca`` without a suffix – fall back to that.
    mmse_alt = "mmse" if prefix == "baseline" else None
    moca_alt = "moca" if prefix == "baseline" else None

    def non_null(col: str | None) -> bool:
        if col is None or col not in row:
            return False
        val = row[col]
        return pd.notna(val) and str(val).strip() != ""

    return any(
        [
            non_null(mmse_col),
            non_null(moca_col),
            non_null(mmse_alt),
            non_null(moca_alt),
        ]
    )

def filter_eligible_subjects(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Tuple[str, str]]]:
    """
    Keep subjects that have at least one cognitive score (MMSE or MOCA)
    present at *both* time‑points.

    Returns
    -------
    eligible_df : pd.DataFrame
        Subset of ``df`` that passed the filter.
    excluded : list of (subject_id, reason)
        Records for subjects that were filtered out.
    """
    logger.info("Filtering eligible subjects")
    eligible_rows = []
    excluded = []

    # The participant identifier column in BIDS is usually ``participant_id``.
    id_col = "participant_id"
    if id_col not in df.columns:
        # Some datasets use ``sub`` or ``subject_id`` – try a fallback.
        for cand in ("sub", "subject_id"):
            if cand in df.columns:
                id_col = cand
                break
        else:
            logger.error("No participant identifier column found.")
            raise KeyError("participant identifier column missing")

    for _, row in df.iterrows():
        subj = row[id_col]
        has_baseline = _score_present(row, "baseline")
        has_followup = _score_present(row, "followup")
        if has_baseline and has_followup:
            eligible_rows.append(row)
        else:
            missing = []
            if not has_baseline:
                missing.append("baseline")
            if not has_followup:
                missing.append("followup")
            reason = f"missing scores at {' & '.join(missing)}"
            excluded.append((subj, reason))

    eligible_df = pd.DataFrame(eligible_rows)
    logger.info(f"Found {len(eligible_df)} eligible subjects, {len(excluded)} excluded")
    return eligible_df, excluded

def limit_subjects(df: pd.DataFrame, max_n: int = 100) -> pd.DataFrame:
    """
    Randomly select up to ``max_n`` rows from ``df`` while preserving the order
    for reproducibility (seed = 42).
    """
    if len(df) <= max_n:
        return df
    df_shuffled = df.sample(n=max_n, random_state=42).reset_index(drop=True)
    logger.info(f"Limiting subjects to {max_n} (random seed 42)")
    return df_shuffled

def write_outputs(
    eligible_df: pd.DataFrame,
    excluded: List[Tuple[str, str]],
    eligible_path: Path = ELIGIBLE_CSV,
    excluded_path: Path = EXCLUDED_LOG,
) -> None:
    """
    Persist the filtered subject list and the exclusion log.

    Parameters
    ----------
    eligible_df : pd.DataFrame
        DataFrame containing at least the participant identifier column.
    excluded : list of (subject_id, reason)
        Records of subjects that were filtered out.
    """
    logger.info(f"Writing eligible subjects to {eligible_path}")
    ensure_dir(eligible_path.parent)

    # Ensure the identifier column is present – rename to ``subject_id`` for downstream consistency.
    id_col = "participant_id"
    if id_col not in eligible_df.columns:
        # try to locate the identifier column used earlier
        for cand in ("sub", "subject_id"):
            if cand in eligible_df.columns:
                id_col = cand
                break
    eligible_df = eligible_df[[id_col]].rename(columns={id_col: "subject_id"})
    eligible_df.to_csv(eligible_path, index=False)

    logger.info(f"Writing exclusion log to {excluded_path}")
    ensure_dir(excluded_path.parent)
    with open(excluded_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["subject_id", "reason"])
        for subj, reason in excluded:
            writer.writerow([subj, reason])

# -------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    """
    Entry point for the script.

    Returns
    -------
    int
        Exit code – ``0`` on success, ``2`` if no eligible subjects were found.
    """
    if argv is None:
        argv = sys.argv[1:]

    # -----------------------------------------------------------------
    # 1. Download participants.tsv (or use a cached copy)
    # -----------------------------------------------------------------
    participants_path = RAW_DIR / "participants.tsv"
    if not participants_path.is_file():
        try:
            download_file(PARTICIPANTS_URL, participants_path)
        except Exception as e:
            logger.error(f"Failed to download participants.tsv: {e}")
            return 1

    # -----------------------------------------------------------------
    # 2. Load the TSV
    # -----------------------------------------------------------------
    try:
        df = read_participants_tsv(participants_path)
    except Exception:
        return 1

    # -----------------------------------------------------------------
    # 3. Filter eligible subjects
    # -----------------------------------------------------------------
    try:
        eligible_df, excluded = filter_eligible_subjects(df)
    except Exception:
        return 1

    if eligible_df.empty:
        logger.error("No eligible subjects found – exiting with code 2.")
        return 2  # EXIT_CODE_NO_LABELS per spec

    # -----------------------------------------------------------------
    # 4. Limit to N = min(100, available)
    # -----------------------------------------------------------------
    limited_df = limit_subjects(eligible_df, max_n=100)

    # -----------------------------------------------------------------
    # 5. Write outputs
    # -----------------------------------------------------------------
    try:
        write_outputs(limited_df, excluded)
    except Exception as e:
        logger.error(f"Failed to write output files: {e}")
        return 1

    logger.info("Download and filtering completed successfully.")
    return 0

# -------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())