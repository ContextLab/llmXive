"""
Fetch HCP behavioral/phenotypic data for the specified subjects.

This script downloads the HCP "Minimal Preprocessed" phenotypic CSV
from the official HCP S3 bucket (publicly accessible). It writes the
full CSV to ``data/raw/hcp_phenotypic.csv`` and, when a list of subject
IDs is supplied, creates a filtered version ``hcp_phenotypic_filtered.csv``.
No synthetic data are generated; if the real download fails the script
raises an exception so the failure is visible to the pipeline runner.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
import requests

from code.logging_config import get_logger
from code.config import get_hcp_credentials

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants – HCP phenotypic data location
# ----------------------------------------------------------------------
# The phenotypic CSV is publicly hosted in the HCP 1200 release.
# The URL points to the latest version of the file.  If HCP changes the
# location the script will raise a clear error, prompting an update.
HCP_S3_BASE = "https://db.humanconnectome.org/data/archive/projects/HCP_1200"
PHENOTYPIC_FILE_NAME = "HCP_1200_Phenotypic_v1.csv"
PHENOTYPIC_URL = f"{HCP_S3_BASE}/Phenotypic/{PHENOTYPIC_FILE_NAME}"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _download_file(url: str, dest: Path, auth: Optional[tuple] = None) -> None:
    """
    Stream‑download a file from ``url`` to ``dest`` using ``requests``.
    Raises ``RuntimeError`` on any HTTP or network error.

    Parameters
    ----------
    url: str
        The HTTP(S) URL to download.
    dest: Path
        Destination file path (parent directories are created automatically).
    auth: tuple | None
        Optional ``(username, password)`` for HTTP Basic Auth.
    """
    logger.log("download_start", url=url, destination=str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(url, stream=True, timeout=120, auth=auth) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except requests.RequestException as e:
        logger.log("download_failed", url=url, error=str(e))
        raise RuntimeError(f"Failed to download {url}: {e}") from e

    logger.log("download_complete", path=str(dest), size_bytes=dest.stat().st_size)

def _load_csv(path: Path) -> pd.DataFrame:
    """
    Load a CSV file with pandas, ensuring that the file is a valid CSV.
    Raises ``RuntimeError`` if parsing fails.
    """
    logger.log("csv_load_start", path=str(path))
    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.log("csv_load_failed", path=str(path), error=str(e))
        raise RuntimeError(f"Unable to parse CSV at {path}: {e}") from e
    logger.log("csv_load_success", path=str(path), rows=len(df))
    return df

def _find_subject_column(df: pd.DataFrame) -> str:
    """
    Heuristically locate the column that contains HCP subject identifiers.
    Returns the column name or raises ``ValueError`` if none is found.
    """
    candidates = [c for c in df.columns if "subj" in str(c).lower() or "subject" in str(c).lower()]
    if not candidates:
        raise ValueError("Could not locate a subject ID column in phenotypic data.")
    # Prefer a column named exactly 'Subject' if it exists.
    for c in candidates:
        if c.lower() == "subject":
            return c
    return candidates[0]

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def fetch_hcp_phenotypic_data(
    output_dir: Path,
    subjects: Optional[List[str]] = None,
) -> Path:
    """
    Download (or reuse) the HCP phenotypic CSV and optionally filter it.

    Parameters
    ----------
    output_dir: Path
        Directory where the CSV (and any filtered version) will be saved.
    subjects: list[str] | None
        If provided, ``subjects`` must be a list of 6‑digit HCP IDs.
        The function will write a filtered CSV containing only those rows.

    Returns
    -------
    Path
        Path to the CSV file that contains the requested data
        (filtered if ``subjects`` was supplied, otherwise the full file).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    full_path = output_dir / "hcp_phenotypic.csv"

    # ------------------------------------------------------------------
    # 1. Download if the full file does not already exist.
    # ------------------------------------------------------------------
    if not full_path.is_file():
        # Use HCP credentials if they are configured; otherwise attempt anonymous.
        credentials = get_hcp_credentials()
        auth = None
        if credentials and credentials.get("access_key") and credentials.get("secret_key"):
            auth = (credentials["access_key"], credentials["secret_key"])
            logger.log("using_hcp_credentials")
        _download_file(PHENOTYPIC_URL, full_path, auth=auth)

    # ------------------------------------------------------------------
    # 2. Load the CSV (validates that the download succeeded).
    # ------------------------------------------------------------------
    df = _load_csv(full_path)

    # ------------------------------------------------------------------
    # 3. If a subject filter is requested, produce a filtered CSV.
    # ------------------------------------------------------------------
    if subjects:
        subject_col = _find_subject_column(df)
        # Ensure subject IDs are strings for reliable matching.
        df[subject_col] = df[subject_col].astype(str)
        filtered_df = df[df[subject_col].isin(subjects)].copy()
        filtered_path = output_dir / "hcp_phenotypic_filtered.csv"
        filtered_df.to_csv(filtered_path, index=False)
        logger.log(
            "filtered_csv_written",
            path=str(filtered_path),
            subject_count=len(filtered_df),
            requested=len(subjects),
        )
        return filtered_path

    # ------------------------------------------------------------------
    # 4. No filtering requested – return the full CSV path.
    # ------------------------------------------------------------------
    logger.log("full_csv_available", path=str(full_path), rows=len(df))
    return full_path

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch HCP behavioral/phenotypic data."
    )
    parser.add_argument(
        "--subjects",
        type=str,
        nargs="+",
        help="Space‑separated list of HCP subject IDs (e.g., 100307).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw"),
        help="Directory where the phenotypic CSV will be stored.",
    )
    args = parser.parse_args()

    # Normalise subject IDs (strip whitespace, ensure 6‑digit numeric strings)
    subjects: Optional[List[str]] = None
    if args.subjects:
        subjects = []
        for sub in args.subjects:
            sub_clean = sub.strip()
            if not sub_clean.isdigit() or len(sub_clean) != 6:
                logger.log("invalid_subject_id", subject=sub_clean)
                print(
                    f"Warning: Subject ID {sub_clean} does not look like a standard HCP ID.",
                    file=sys.stderr,
                )
            else:
                subjects.append(sub_clean)

    try:
        result_path = fetch_hcp_phenotypic_data(args.output, subjects)
        print(f"Successfully fetched HCP phenotypic data to: {result_path}")
    except Exception as exc:
        logger.log("fetch_failed", error=str(exc))
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()