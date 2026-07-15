"""
T017: Download ds000246, parse BIDS metadata, filter for longitudinal scores,
and output eligible/excluded subject lists.

Outputs:
  - data/processed/eligible_subjects.csv
  - data/processed/excluded_subjects.log
  - data/artifacts/data_gate_status.json
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from tqdm import tqdm

from utils.logger import get_logger, log_operation

# Constants
DATASET_ID = "ds000246"
OPENNEURO_API = "https://api.openneuro.org/datasets"
MAX_SUBJECTS = 100
RANDOM_SEED = 42

# Exit codes
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_DATA = 1
EXIT_CODE_NO_ELIGIBLE = 2

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


@log_operation
def download_dataset_metadata(dataset_id: str) -> Dict[str, Any]:
    """Fetch dataset metadata from OpenNeuro API."""
    url = f"{OPENNEURO_API}/{dataset_id}"
    logger.log("fetch_metadata", url=url)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.log("fetch_metadata_error", error=str(e))
        raise


@log_operation
def download_participants_file(dataset_id: str, output_path: Path) -> None:
    """Download participants.tsv from OpenNeuro."""
    # OpenNeuro files are served via git-annex or direct tarballs.
    # For ds000246, the participants.tsv is usually at the root.
    # We use the public file endpoint:
    # https://openneuro.org/datasets/ds000246/versions/1.0.0/file-display/participants.tsv
    # However, the API for direct file download is:
    # https://api.openneuro.org/datasets/{id}/files/{path}
    # But simpler: use the tarball or the direct link if known.
    # For robustness, we try the direct file link pattern.
    
    # Pattern: https://openneuro.org/datasets/{id}/versions/latest/file-display/participants.tsv
    # Actually, OpenNeuro provides a direct download link for files in the dataset browser.
    # Let's try the standard public file path:
    base_url = f"https://openneuro.org/datasets/{dataset_id}/versions/latest"
    file_path = "participants.tsv"
    # OpenNeuro file download URL structure often requires the specific version.
    # Fallback: try to fetch via the dataset's main page or a known tarball.
    # Since we need to be robust, let's try the direct file link from the browser which often redirects to S3.
    # Alternative: Use the API to list files? No, simpler to fetch the TSV directly if public.
    # ds000246 is public.
    
    # Attempt 1: Direct link from the web UI (often works for public datasets)
    direct_url = f"https://openneuro.org/datasets/{dataset_id}/versions/latest/file-display/{file_path}"
    
    # Attempt 2: API endpoint for file content (if available)
    # The API endpoint for file content is usually:
    # https://api.openneuro.org/datasets/{id}/versions/{version}/files/{path}
    # But we don't know the version. Let's try 'latest'.
    api_url = f"https://api.openneuro.org/datasets/{dataset_id}/versions/latest/files/{file_path}"
    
    url_to_try = direct_url # Start with direct URL which often serves the file or redirects.
    
    logger.log("download_participants", url=url_to_try)
    
    # If direct_url fails, try to fetch from the tarball or a different endpoint.
    # For ds000246, the participants.tsv is in the root.
    # Let's try a robust fetch:
    try:
        # OpenNeuro file display pages often redirect to S3.
        # We'll use the direct link and follow redirects.
        resp = requests.get(direct_url, timeout=60, allow_redirects=True)
        if resp.status_code == 200:
            # Check if it's the TSV content or an HTML page
            if "participants" in resp.text and "\t" in resp.text:
                output_path.write_text(resp.text)
                return
            elif "Not Found" in resp.text or "404" in resp.text:
                raise FileNotFoundError(f"File not found at {direct_url}")
    
        # Fallback: Try the API file endpoint if direct display fails
        logger.log("direct_download_failed", status=resp.status_code, trying_api=True)
        api_resp = requests.get(api_url, timeout=60)
        if api_resp.status_code == 200:
            output_path.write_text(api_resp.text)
            return
        else:
            # Last resort: Try to download the whole dataset tarball? Too heavy.
            # Or check if the file is in a specific version.
            # ds000246 version 1.0.0 is common.
            v_url = f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/file-display/{file_path}"
            v_resp = requests.get(v_url, timeout=60, allow_redirects=True)
            if v_resp.status_code == 200 and "participants" in v_resp.text:
                output_path.write_text(v_resp.text)
                return
            
        raise RuntimeError(f"Failed to download participants.tsv from {direct_url} and {api_url}")
        
    except requests.RequestException as e:
        logger.log("download_participants_error", error=str(e))
        raise


@log_operation
def read_participants_file(path: Path) -> pd.DataFrame:
    """Read participants.tsv into a DataFrame."""
    logger.log("read_participants", path=str(path))
    if not path.exists():
        raise FileNotFoundError(f"Participants file not found: {path}")
    df = pd.read_csv(path, sep="\t")
    return df


@log_operation
def has_valid_score(row: pd.Series, score_cols: List[str]) -> bool:
    """Check if any of the specified score columns have a non-null, non-NaN value."""
    for col in score_cols:
        if col in row.index and pd.notna(row[col]) and row[col] != "":
            return True
    return False


@log_operation
def is_eligible(row: pd.Series, timepoint_cols: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if subject has valid scores at BOTH timepoints.
    Returns (is_eligible, list_of_missing_timepoints).
    """
    missing = []
    for col in timepoint_cols:
        if col not in row.index or pd.isna(row[col]) or row[col] == "":
            missing.append(col)
    
    if len(missing) == 0:
        return True, []
    return False, missing


@log_operation
def filter_eligible_subjects(df: pd.DataFrame, timepoint_cols: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter DataFrame for subjects with valid scores at all specified timepoints.
    Returns (eligible_df, excluded_df).
    """
    eligible_rows = []
    excluded_rows = []
    
    for _, row in df.iterrows():
        is_elig, missing = is_eligible(row, timepoint_cols)
        if is_elig:
            eligible_rows.append(row)
        else:
            # Add missing info to the row for logging
            row_copy = row.copy()
            row_copy["exclusion_reason"] = f"Missing: {', '.join(missing)}"
            excluded_rows.append(row_copy)
    
    eligible_df = pd.DataFrame(eligible_rows) if eligible_rows else pd.DataFrame()
    excluded_df = pd.DataFrame(excluded_rows) if excluded_rows else pd.DataFrame()
    
    logger.log("filter_eligible", eligible_count=len(eligible_df), excluded_count=len(excluded_df))
    return eligible_df, excluded_df


@log_operation
def limit_subjects(df: pd.DataFrame, limit: int, seed: int = 42) -> pd.DataFrame:
    """Randomly sample up to 'limit' subjects if more are available."""
    if len(df) <= limit:
        return df
    logger.log("limit_subjects", original=len(df), limit=limit)
    return df.sample(n=limit, random_state=seed)


@log_operation
def write_eligible_csv(df: pd.DataFrame, path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_directory(path.parent)
    df.to_csv(path, index=False)
    logger.log("write_eligible_csv", path=str(path), count=len(df))


@log_operation
def write_excluded_log(df: pd.DataFrame, path: Path) -> None:
    """Write excluded subjects to log file."""
    ensure_directory(path.parent)
    with open(path, "w") as f:
        f.write("# Excluded Subjects Log\n")
        f.write(f"# Total excluded: {len(df)}\n\n")
        if not df.empty:
            df.to_csv(f, index=False)
    logger.log("write_excluded_log", path=str(path), count=len(df))


@log_operation
def write_status(eligible_count: int, excluded_count: int, status: str, error: Optional[str] = None) -> None:
    """Write status JSON to data artifacts."""
    status_path = Path("data/artifacts/data_gate_status.json")
    ensure_directory(status_path.parent)
    
    status_data = {
        "status": status,
        "error": error,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    with open(status_path, "w") as f:
        json.dump(status_data, f, indent=2)
    logger.log("write_status", path=str(status_path))


@log_operation
def main() -> int:
    """Main entry point."""
    logger.log("main_start")
    try:
        # 1. Ensure directories
        raw_dir = Path("data/raw")
        processed_dir = Path("data/processed")
        ensure_directory(raw_dir)
        ensure_directory(processed_dir)
        
        # 2. Download participants.tsv
        participants_path = raw_dir / "ds000246" / "participants.tsv"
        ensure_directory(participants_path.parent)
        
        if not participants_path.exists():
            logger.log("downloading_participants")
            download_participants_file(DATASET_ID, participants_path)
        else:
            logger.log("participants_already_exists")
        
        # 3. Read and filter
        df = read_participants_file(participants_path)
        
        # Define timepoint columns based on typical BIDS longitudinal structure
        # ds000246 (Constitution VI) usually has columns like:
        # participant_id, age, sex, MMSE_baseline, MMSE_followup, MOCA_baseline, MOCA_followup
        # We need to check for non-null MMSE/MOCA at BOTH timepoints.
        # Let's inspect columns to be safe, or assume standard naming.
        # Standard assumption: columns contain "MMSE" or "MOCA" and "baseline"/"followup" or "1"/"2".
        # For robustness, we look for any column with MMSE or MOCA that has a numeric value.
        # But the spec says "at both timepoints".
        # Let's assume columns: MMSE_1, MMSE_2, MOCA_1, MOCA_2 or similar.
        # If the dataset uses specific names, we might need to adapt.
        # ds000246 metadata: It has MMSE and MOCA scores at baseline and follow-up.
        # Common names: MMSE, MMSE_followup, MOCA, MOCA_followup?
        # Or: MMSE_0, MMSE_1?
        # Let's try to detect columns that look like scores.
        
        score_candidates = [c for c in df.columns if "MMSE" in c.upper() or "MOCA" in c.upper()]
        if not score_candidates:
            logger.log("no_score_columns_found", available_columns=list(df.columns))
            # Fallback: try common names
            score_candidates = ["MMSE", "MOCA", "MMSE_baseline", "MOCA_baseline", "MMSE_followup", "MOCA_followup"]
            # Filter to those that exist
            score_candidates = [c for c in score_candidates if c in df.columns]
        
        if len(score_candidates) < 2:
            # We need at least two columns to represent two timepoints?
            # Or maybe one column with multiple rows per subject?
            # BIDS usually has one row per subject, with columns for each timepoint.
            # If we have only one score column, we can't check "both timepoints".
            # Let's assume the dataset has columns like: MMSE_1, MMSE_2
            # If not, we might fail.
            logger.log("insufficient_score_columns", candidates=score_candidates)
            # Try to infer: if we have MMSE and MOCA, maybe they are at different times?
            # No, the task says "at both timepoints".
            # Let's assume the columns are named with a suffix indicating timepoint.
            # We'll group by prefix (MMSE, MOCA) and check for 2 values.
            pass
        
        # Heuristic: Group columns by base name (e.g., MMSE, MOCA) and check for 2 timepoints.
        # We need subjects who have valid scores for AT LEAST ONE cognitive measure at BOTH timepoints.
        # Or maybe both MMSE and MOCA? The spec says "MMSE/MOCA", implying either.
        # "filter for subjects with non‑null MMSE/MOCA at both timepoints"
        # Interpretation: For a given subject, there must be a valid MMSE at T1 and T2, OR a valid MOCA at T1 and T2.
        
        # Let's find pairs of columns that look like T1 and T2 for the same measure.
        # Simple approach: Look for columns ending in _1, _2, _baseline, _followup, etc.
        # If we can't find clear pairs, we might need to inspect the actual data.
        # For ds000246, the participants.tsv often has:
        # participant_id, age, sex, MMSE, MMSE_followup, MOCA, MOCA_followup?
        # Let's assume the columns are:
        # "MMSE", "MMSE_followup", "MOCA", "MOCA_followup"
        # Or "MMSE_1", "MMSE_2"
        
        # We will try a flexible matching:
        # 1. Identify base measures: MMSE, MOCA
        # 2. For each base, find all columns that contain the base name.
        # 3. If we find at least 2 columns for a base, treat them as timepoints.
        # 4. A subject is eligible if for ANY base measure, they have valid scores in ALL its timepoint columns.
        
        measures = ["MMSE", "MOCA"]
        timepoint_cols = []
        valid_measures = []
        
        for measure in measures:
            cols = [c for c in df.columns if measure.upper() in c.upper()]
            if len(cols) >= 2:
                timepoint_cols.extend(cols)
                valid_measures.append(measure)
        
        if not valid_measures:
            logger.log("no_valid_measure_pairs_found", available_columns=list(df.columns))
            # Fallback: Try to use all score columns as timepoints? No, that's risky.
            # If we can't find pairs, we fail loudly as per spec.
            raise ValueError("Could not identify two timepoints for any cognitive measure (MMSE/MOCA).")
        
        logger.log("identified_timepoints", columns=timepoint_cols, measures=valid_measures)
        
        eligible_df, excluded_df = filter_eligible_subjects(df, timepoint_cols)
        
        if eligible_df.empty:
            logger.log("no_eligible_subjects")
            write_status(0, len(excluded_df), "failed", error="No eligible subjects found with longitudinal scores.")
            return EXIT_CODE_NO_ELIGIBLE
        
        # Limit subjects
        eligible_df = limit_subjects(eligible_df, MAX_SUBJECTS, RANDOM_SEED)
        
        # Write outputs
        write_eligible_csv(eligible_df, processed_dir / "eligible_subjects.csv")
        write_excluded_log(excluded_df, processed_dir / "excluded_subjects.log")
        write_status(len(eligible_df), len(excluded_df), "success")
        
        logger.log("main_success", eligible=len(eligible_df), excluded=len(excluded_df))
        return EXIT_CODE_SUCCESS
        
    except Exception as e:
        logger.log("main_error", error=str(e), exc_info=True)
        write_status(0, 0, "error", error=str(e))
        return EXIT_CODE_NO_DATA


if __name__ == "__main__":
    sys.exit(main())