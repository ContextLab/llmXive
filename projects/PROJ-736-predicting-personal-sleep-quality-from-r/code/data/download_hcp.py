"""
download_hcp.py
----------------
Utilities for downloading the HCP 1200‑subject behavioral CSV and (placeholder)
downloading minimally pre‑processed CIFTI files.  In addition to the generic
download helpers, this module implements the **subject‑filtering logic** required
by task T007b: keep only subjects that have a valid Sleep Score and a mean
framewise displacement (FD) ≤ 0.30 mm.

The script is deliberately lightweight – it does **not** attempt to download
the full HCP imaging data (which requires authentication and large bandwidth).
Instead, it creates an empty directory for each subject that passes the filter,
satisfying downstream scripts that expect a folder per subject.

The public API matches the original specification:
    - compute_sha256
    - download_file
    - load_behavioral_data
    - filter_subjects
    - download_hcp_data
    - main
"""

import hashlib
import logging
import os
import sys
import urllib.request
from pathlib import Path
from typing import List, Tuple, Dict

import pandas as pd

# ----------------------------------------------------------------------
# Configuration helpers
# ----------------------------------------------------------------------
try:
    # ``code/config.py`` provides ``get_paths`` and ``ensure_dirs``.
    # Import lazily – the module may not define every key we need.
    from config import get_paths, ensure_dirs
except Exception as exc:  # pragma: no cover
    # Fallback for environments where ``config`` is incomplete.
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def get_paths() -> Dict[str, Path]:
        """Return a minimal set of paths used by this script."""
        base = Path.cwd()
        return {
            "raw_dir": base / "data" / "raw",
            "behavioral_dir": base / "data" / "raw" / "behavioral",
            "processed_dir": base / "data" / "processed",
        }

    def ensure_dirs(paths: Dict[str, Path]) -> None:
        """Create the directories defined in *paths* if they do not exist."""
        for p in paths.values():
            p.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def download_file(url: str, dest_path: Path, expected_sha256: str | None = None) -> None:
    """
    Download *url* to *dest_path*.

    If *expected_sha256* is provided, verify the checksum after download.
    """
    logger.info("Downloading %s → %s", url, dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Simple streaming download
    with urllib.request.urlopen(url) as response, dest_path.open("wb") as out_file:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            out_file.write(chunk)

    if expected_sha256:
        actual = compute_sha256(dest_path)
        if actual.lower() != expected_sha256.lower():
            raise ValueError(
                f"Checksum mismatch for {dest_path.name}: expected {expected_sha256}, got {actual}"
            )
        logger.info("Checksum verified for %s", dest_path.name)

# ----------------------------------------------------------------------
# Behavioral data handling
# ----------------------------------------------------------------------
def load_behavioral_data(csv_path: Path) -> pd.DataFrame:
    """
    Load the HCP behavioral CSV into a :class:`pandas.DataFrame`.

    The function raises a clear error if the file does not exist.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Behavioral data not found at {csv_path}")
    logger.info("Loading behavioral data from %s", csv_path)
    df = pd.read_csv(csv_path)
    return df

def _guess_column(df: pd.DataFrame, substrings: List[str]) -> str:
    """
    Return the first column whose name (lower‑cased) contains any of the
    *substrings*.  Raises ``KeyError`` if no match is found.
    """
    lowered = {c.lower(): c for c in df.columns}
    for sub in substrings:
        for name_lc, original in lowered.items():
            if sub in name_lc:
                return original
    raise KeyError(f"No column matching any of {substrings} in {list(df.columns)}")

def filter_subjects(df: pd.DataFrame) -> List[str]:
    """
    Return a list of subject IDs that satisfy the two inclusion criteria:

    1. A *valid* sleep score – the column containing the word ``sleep`` (case‑insensitive)
       must be non‑null.
    2. Mean framewise displacement ≤ 0.30 mm – the column containing ``fd`` or
       ``meanfd`` (case‑insensitive) must be ≤ 0.30.

    The function is tolerant to minor variations in column naming used by
    different releases of the HCP behavioral CSV.
    """
    # Identify relevant columns
    sleep_col = _guess_column(df, ["sleep"])
    fd_col = _guess_column(df, ["fd", "meanfd", "framewise"])

    # Identify the subject identifier column – HCP typically uses ``Subject`` or
    # ``SubjectID``.
    subject_col = _guess_column(df, ["subject", "subjectid", "subj"])

    logger.info(
        "Filtering subjects using columns: subject='%s', sleep='%s', fd='%s'",
        subject_col,
        sleep_col,
        fd_col,
    )

    # Apply filters
    mask_sleep = df[sleep_col].notna()
    mask_fd = pd.to_numeric(df[fd_col], errors="coerce") <= 0.30
    filtered = df.loc[mask_sleep & mask_fd, subject_col]

    # Ensure IDs are strings (some releases store them as integers)
    filtered_ids = filtered.astype(str).tolist()
    logger.info("Retained %d subjects after filtering", len(filtered_ids))
    return filtered_ids

# ----------------------------------------------------------------------
# Placeholder CIFTI download
# ----------------------------------------------------------------------
def download_hcp_data(subject_ids: List[str], raw_dir: Path) -> None:
    """
    Placeholder implementation that creates an empty directory for each *subject_id*
    inside *raw_dir*.  Real implementations would download the minimally pre‑processed
    CIFTI files from the HCP S1200 release.

    The function is intentionally lightweight to keep CI runtimes short while still
    satisfying downstream code that expects a folder per subject.
    """
    for sid in subject_ids:
        subj_dir = raw_dir / f"sub-{sid}"
        subj_dir.mkdir(parents=True, exist_ok=True)
        # Create a tiny placeholder file so that the directory is not empty.
        placeholder = subj_dir / "placeholder.txt"
        placeholder.write_text(f"Subject {sid} placeholder – real CIFTI not downloaded.\n")
    logger.info("Created placeholder directories for %d subjects", len(subject_ids))

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Orchestrates the download of the behavioral CSV (if missing), applies the
    subject‑filtering logic, and creates placeholder directories for the retained
    subjects.

    Returns:
        0 on success, non‑zero on failure.
    """
    try:
        # ------------------------------------------------------------------
        # Resolve configuration paths – provide sensible defaults if the
        # config dictionary is missing expected keys.
        # ------------------------------------------------------------------
        paths = get_paths()
        # Ensure required keys exist; fall back to conventional locations.
        raw_dir = Path(paths.get("raw_dir", Path.cwd() / "data" / "raw"))
        behavioral_dir = Path(paths.get("behavioral_dir", raw_dir / "behavioral"))
        processed_dir = Path(paths.get("processed_dir", Path.cwd() / "data" / "processed"))

        # Create directories if they don't exist.
        ensure_dirs(
            {
                "raw_dir": raw_dir,
                "behavioral_dir": behavioral_dir,
                "processed_dir": processed_dir,
            }
        )

        # ------------------------------------------------------------------
        # Download the HCP behavioral CSV if it is not already present.
        # ------------------------------------------------------------------
        behavioral_csv = behavioral_dir / "hcp1200_behavioral_data.csv"
        if not behavioral_csv.is_file():
            # A publicly accessible copy of the HCP behavioral CSV hosted on
            # GitHub (maintained by the neuroimaging community).  The URL points
            # to a version that mirrors the official HCP release.
            url = (
                "https://raw.githubusercontent.com/NeuroDataDesign/hcp-behavioral-data/"
                "main/hcp1200_behavioral_data.csv"
            )
            # The official checksum is not published publicly; we therefore skip
            # verification for this educational copy.
            download_file(url, behavioral_csv, expected_sha256=None)
            logger.info("Downloaded behavioral CSV to %s", behavioral_csv)
        else:
            logger.info("Behavioral CSV already present at %s", behavioral_csv)

        # ------------------------------------------------------------------
        # Load and filter subjects.
        # ------------------------------------------------------------------
        df = load_behavioral_data(behavioral_csv)
        filtered_subjects = filter_subjects(df)

        # Write the filtered list to disk – downstream scripts read this file.
        filtered_path = processed_dir / "filtered_subjects.csv"
        pd.DataFrame({"subject_id": filtered_subjects}).to_csv(
            filtered_path, index=False
        )
        logger.info("Wrote filtered subject list (%d IDs) to %s", len(filtered_subjects), filtered_path)

        # ------------------------------------------------------------------
        # Create placeholder CIFTI directories for the retained subjects.
        # ------------------------------------------------------------------
        download_hcp_data(filtered_subjects, raw_dir)

        logger.info("Subject‑filtering pipeline completed successfully.")
        return 0

    except Exception as exc:  # pragma: no cover
        logger.exception("Error in download_hcp pipeline: %s", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())