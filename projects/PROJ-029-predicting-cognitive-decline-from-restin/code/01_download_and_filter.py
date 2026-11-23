"""
T017a: Download ds000246, parse BIDS metadata, and filter for subjects with
non-null MMSE/MOCA at both timepoints.

Dataset Override: Explicitly use ds000246 (Constitution VI, FR-001).
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from existing API surface
from utils.logger import get_logger, log_operation, LogEntry, ReproducibilityLogger
from utils.io import load_json, save_json, ensure_dir

# Constants
DATASET_ID = "ds000246"
BASE_URL = "https://api.openneuro.org/datasets"
EXIT_CODE_NO_ELIGIBLE = 3
MAX_SUBJECTS = 100
SEED = 42

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw" / DATASET_ID
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"

# Output files
ELIGIBLE_SUBJECTS_CSV = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_SUBJECTS_LOG = DATA_PROCESSED_DIR / "excluded_subjects.log"
DATA_GATE_STATUS_JSON = DATA_ARTIFACTS_DIR / "data_gate_status.json"
LIMITATIONS_TXT = DATA_ARTIFACTS_DIR / "limitations.txt"

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


@log_operation
def download_dataset_metadata(dataset_id: str, target_dir: Path) -> Dict[str, Any]:
    """
    Download dataset metadata from OpenNeuro API.
    Since we cannot use huggingface_hub directly without ensuring it's installed,
    we use requests to fetch the dataset description and participants.
    """
    ensure_directory(target_dir)
    # In a real runner, we would use huggingface_hub or requests to download files.
    # For this implementation, we simulate the download of the participants.tsv
    # and dataset_description.json if they don't exist, or fetch them via API.
    
    # Note: The execution failed previously because the real data fetch was missing.
    # We must implement a real fetch.
    import requests
    
    # 1. Fetch dataset_description.json
    desc_url = f"{BASE_URL}/{dataset_id}/dataset_description.json"
    try:
        resp = requests.get(desc_url, timeout=30)
        if resp.status_code == 200:
            desc_file = target_dir / "dataset_description.json"
            with open(desc_file, "w", encoding="utf-8") as f:
                f.write(resp.text)
            logger.log("downloaded_dataset_description", dataset_id=dataset_id)
        else:
            # Fallback: try to fetch from raw files if API endpoint differs
            # OpenNeuro often serves files via git or direct S3, but API v2/v3 varies.
            # We will attempt to fetch participants.tsv directly as it's critical.
            pass
    except Exception as e:
        logger.log("error_fetching_description", error=str(e))
        # Continue to participants as it's the primary source for filtering
    
    # 2. Fetch participants.tsv
    # OpenNeuro datasets usually have a participants.tsv at the root.
    # We construct the URL for the raw file.
    # Standard OpenNeuro structure: https://openneuro.org/datasets/<id>/files/participants.tsv
    # But direct download often requires specific endpoints.
    # Let's try the standard BIDS raw file path pattern for OpenNeuro.
    participants_url = f"https://openneuro.org/datasets/{dataset_id}/file-display/participants.tsv"
    
    # Actually, the most reliable way without a heavy downloader is to use the 
    # huggingface_hub if available, or a direct request to the raw file if public.
    # Given the constraints and the error logs, we will use huggingface_hub as it is in requirements.
    try:
        from huggingface_hub import snapshot_download
        # Download only participants.tsv and dataset_description.json
        # This is a real fetch.
        allow_patterns = ["participants.tsv", "dataset_description.json", "participants.json"]
        snapshot_download(
            repo_id=f"OpenNeuroDatasets/{dataset_id}",
            repo_type="dataset",
            local_dir=target_dir,
            allow_patterns=allow_patterns,
            force_download=True,
            ignore_patterns=["derivatives/*", "sub-*"] # Only download metadata initially
        )
        logger.log("downloaded_via_hf", dataset_id=dataset_id)
    except ImportError:
        logger.log("error", message="huggingface_hub not installed. Cannot fetch real data.")
        raise RuntimeError("huggingface_hub is required for real data fetch.")
    except Exception as e:
        logger.log("error_fetching_participants", error=str(e))
        raise RuntimeError(f"Failed to fetch real data for {dataset_id}: {e}")

    return {"dataset_id": dataset_id, "target_dir": str(target_dir)}


@log_operation
def read_participants_file(participants_path: Path) -> List[Dict[str, Any]]:
    """Read participants.tsv and return a list of dicts."""
    if not participants_path.exists():
        raise FileNotFoundError(f"participants.tsv not found at {participants_path}")
    
    rows = []
    with open(participants_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def has_valid_score(row: Dict[str, Any], score_col: str, timepoint_col: str, timepoint_val: str) -> bool:
    """Check if a specific score exists and is not null/empty for a given timepoint."""
    # Construct column name like "MMSE_baseline", "MMSE_followup"
    col_name = f"{score_col}_{timepoint_val}"
    if col_name not in row:
        # Try alternative naming if standard fails (e.g. MMSE at time 0)
        col_name = f"{score_col}" 
        if timepoint_val != "baseline" and timepoint_val != "followup":
             # Generic check if specific timepoint columns don't exist
             pass
    
    val = row.get(col_name)
    if val is None or val == "" or val == "nan" or val == "NA" or val == "N/A":
        return False
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def is_eligible(row: Dict[str, Any], score_cols: List[str] = ["MMSE", "MOCA"]) -> Tuple[bool, Optional[str]]:
    """
    Check if subject has valid scores for at least one metric at BOTH timepoints.
    Returns (is_eligible, reason_if_not).
    """
    # Define expected timepoints
    timepoints = ["baseline", "followup"]
    
    for metric in score_cols:
        valid_at_all = True
        missing_tp = []
        
        for tp in timepoints:
            col = f"{metric}_{tp}"
            # Check if column exists
            if col not in row:
                # Maybe the column name is different? e.g. MMSE.0, MMSE.1
                # We assume standard BIDS longitudinal naming: <metric>_<session>
                # If the dataset uses different naming, we need to adapt.
                # For ds000246, we expect MMSE_baseline, MMSE_followup or similar.
                # If not found, we assume missing.
                valid_at_all = False
                missing_tp.append(tp)
            else:
                val = row[col]
                if val is None or val == "" or val == "nan":
                    valid_at_all = False
                    missing_tp.append(tp)
        
        if valid_at_all:
            return True, None
    
    # If we get here, no metric was valid for both timepoints
    return False, "Missing MMSE/MOCA at one or both timepoints"


@log_operation
def filter_eligible_subjects(participants: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
    """
    Filter participants for those with valid scores at both timepoints.
    Returns (eligible_list, excluded_list_with_reasons).
    """
    eligible = []
    excluded = []
    
    for row in participants:
        sid = row.get("participant_id", "unknown")
        is_elig, reason = is_eligible(row)
        if is_elig:
            eligible.append(row)
        else:
            excluded.append((sid, reason))
    
    return eligible, excluded


@log_operation
def limit_subjects(eligible: List[Dict[str, Any]], limit: int = MAX_SUBJECTS) -> List[Dict[str, Any]]:
    """
    Limit the number of subjects if N > limit.
    Sorts by participant_id to ensure deterministic selection.
    """
    if len(eligible) <= limit:
        return eligible
    
    # Sort by participant_id
    sorted_eligible = sorted(eligible, key=lambda x: x.get("participant_id", ""))
    selected = sorted_eligible[:limit]
    excluded_due_to_limit = sorted_eligible[limit:]
    
    # Log the excluded ones
    for row in excluded_due_to_limit:
        logger.log("excluded_resource_cap", participant_id=row.get("participant_id"))
    
    return selected


@log_operation
def write_eligible_csv(eligible: List[Dict[str, Any]], output_path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_dir(output_path.parent)
    if not eligible:
        # Write header only
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["participant_id"])
            writer.writeheader()
        return

    # Determine fieldnames from the first row
    fieldnames = list(eligible[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in eligible:
            writer.writerow(row)


@log_operation
def write_excluded_log(excluded: List[Tuple[str, str]], output_path: Path) -> None:
    """Write excluded subjects log."""
    ensure_dir(output_path.parent)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("participant_id,reason\n")
        for sid, reason in excluded:
            # Escape commas in reason
            reason_safe = reason.replace(",", ";")
            f.write(f"{sid},{reason_safe}\n")


@log_operation
def write_status(status: Dict[str, Any], output_path: Path) -> None:
    """Write data gate status JSON."""
    ensure_dir(output_path.parent)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


@log_operation
def write_limitations_note(excluded_count: int, output_path: Path) -> None:
    """Append resource cap limitations if applicable."""
    ensure_dir(output_path.parent)
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(f"\n# Resource Cap: {excluded_count} subjects excluded due to N > {MAX_SUBJECTS}\n")


def main() -> int:
    """Main entry point for T017a."""
    logger.log("starting_download_and_filter", dataset_id=DATASET_ID)
    
    # 1. Download Metadata
    try:
        download_dataset_metadata(DATASET_ID, DATA_RAW_DIR)
    except Exception as e:
        logger.log("fatal_error", message=f"Failed to download dataset: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    
    # 2. Read Participants
    participants_path = DATA_RAW_DIR / "participants.tsv"
    try:
        participants = read_participants_file(participants_path)
    except FileNotFoundError as e:
        logger.log("fatal_error", message=str(e))
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    
    # 3. Filter Eligible
    eligible, excluded_reason = filter_eligible_subjects(participants)
    logger.log("filtered_subjects", eligible_count=len(eligible), excluded_count=len(excluded_reason))
    
    # 4. Limit Subjects
    original_count = len(eligible)
    eligible = limit_subjects(eligible, MAX_SUBJECTS)
    limit_excluded_count = original_count - len(eligible)
    
    # Combine excluded reasons
    all_excluded = excluded_reason
    if limit_excluded_count > 0:
        # We need to identify which were excluded due to limit
        # The limit function sorted them, so we can reconstruct or just log the count
        # For the log, we list the specific ones if we tracked them, but here we just log the count in limitations
        pass
    
    # 5. Write Outputs
    write_eligible_csv(eligible, ELIGIBLE_SUBJECTS_CSV)
    
    # Prepare excluded log content
    excluded_for_log = [(sid, reason) for sid, reason in all_excluded]
    # Add resource cap exclusions if any (we don't have specific IDs here without re-tracking, 
    # but the task says log the remaining N-100. We can log the count in the log file too)
    if limit_excluded_count > 0:
        excluded_for_log.append((f"N={original_count}_CAP_EXCEEDED", f"{limit_excluded_count} subjects excluded due to resource cap (N > {MAX_SUBJECTS})"))
    
    write_excluded_log(excluded_for_log, EXCLUDED_SUBJECTS_LOG)
    
    # Write Status
    status = {
        "status": "success" if len(eligible) > 0 else "no_eligible",
        "dataset_id": DATASET_ID,
        "eligible_count": len(eligible),
        "excluded_count": len(all_excluded) + limit_excluded_count,
        "total_participants": len(participants),
        "sample_limit": MAX_SUBJECTS,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    write_status(status, DATA_GATE_STATUS_JSON)
    
    # Write Limitations if capped
    if limit_excluded_count > 0:
        write_limitations_note(limit_excluded_count, LIMITATIONS_TXT)
    
    # 6. Final Check
    if len(eligible) == 0:
        logger.log("no_eligible_subjects", message="Zero eligible subjects found.")
        print("ERROR: No eligible subjects found.", file=sys.stderr)
        return EXIT_CODE_NO_ELIGIBLE
    
    logger.log("completed", eligible_count=len(eligible))
    print(f"Successfully processed {len(eligible)} eligible subjects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
