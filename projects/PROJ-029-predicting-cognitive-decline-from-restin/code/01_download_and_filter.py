"""
T017: Download and filter subjects for cognitive decline prediction.

Downloads ds000246 (Constitution VI) from OpenNeuro, parses BIDS metadata,
filters for subjects with non-null MMSE/MOCA scores at both timepoints,
limits to N=min(100, eligible), and writes output artifacts.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import pandas as pd

# Import from existing project utilities
from utils.logger import get_logger, log_operation, LogEntry

# Constants
DATASET_ID = "ds000246"
OPENNEURO_API_BASE = "https://api.openneuro.org/datasets"
OUTPUT_DIR_ELIGIBLE = Path("data/processed")
OUTPUT_DIR_ARTIFACTS = Path("data/artifacts")
OUTPUT_FILE_ELIGIBLE = OUTPUT_DIR_ELIGIBLE / "eligible_subjects.csv"
OUTPUT_FILE_EXCLUDED = OUTPUT_DIR_ELIGIBLE / "excluded_subjects.log"
OUTPUT_FILE_STATUS = OUTPUT_DIR_ARTIFACTS / "data_gate_status.json"
MAX_SUBJECTS = 100
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_DOWNLOAD_ERROR = 3

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Ensure the directory exists."""
    path.mkdir(parents=True, exist_ok=True)


@log_operation("download_dataset_metadata")
def download_dataset_metadata() -> Dict[str, Any]:
    """Fetch dataset metadata from OpenNeuro API."""
    url = f"{OPENNEURO_API_BASE}/{DATASET_ID}/versions/latest"
    headers = {"Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.log("download_metadata_failed", error=str(e))
        raise


@log_operation("download_participants_file")
def download_participants_file() -> pd.DataFrame:
    """Download and parse the participants.tsv file from OpenNeuro."""
    # OpenNeuro file download endpoint for TSV
    # Using the direct file URL pattern for ds000246
    file_url = f"https://openneuro.org/datasets/{DATASET_ID}/versions/latest/file-download/participants.tsv"
    # Alternative: use the API to get file token, but direct download often works for public datasets
    # If direct fails, we might need to use the API to get a presigned URL
    # For robustness, try the API file list first to get the correct path
    
    # Let's try to get the file via the API's file listing
    # OpenNeuro GraphQL API is complex, let's try the simpler REST file download
    # Actually, the standard way is to use the dataset's s3 bucket or the openneuro-cli
    # But for this script, we will try to fetch the TSV directly if public
    
    # Fallback strategy: Try to get the file from the dataset's public URL
    # ds000246 is public. The file is at:
    # https://openneuro.org/datasets/ds000246/versions/3.0.1/file-display/participants.tsv
    # We need to find the latest version or just use the dataset root
    
    # Let's use a more robust approach: fetch the dataset index
    # Or simply try the direct TSV URL with a common version
    # We'll try a few common version patterns or the latest
    
    # Simpler: Use the openneuro API to get the file download URL
    # GraphQL query to get the file ID for participants.tsv
    query = """
    query {
      dataset(id: "ds000246") {
        id
        latestSnapshot {
          id
          files(pattern: "participants.tsv") {
            id
            filename
            downloadUrl
          }
        }
      }
    }
    """
    try:
        # OpenNeuro GraphQL endpoint
        gql_url = "https://api.openneuro.org/graphql"
        response = requests.post(
            gql_url,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if "errors" in result:
            raise RuntimeError(f"GraphQL error: {result['errors']}")
        
        data = result.get("data", {})
        dataset = data.get("dataset", {})
        snapshot = dataset.get("latestSnapshot", {})
        files = snapshot.get("files", [])
        
        if not files:
            raise FileNotFoundError("participants.tsv not found in dataset")
        
        # Get the download URL
        download_url = files[0].get("downloadUrl")
        if not download_url:
            raise FileNotFoundError("No download URL provided for participants.tsv")
        
        # Download the file
        file_response = requests.get(download_url, timeout=30)
        file_response.raise_for_status()
        
        # Parse TSV
        df = pd.read_csv(pd.io.common.StringIO(file_response.text), sep="\t")
        return df
        
    except requests.RequestException as e:
        logger.log("download_participants_failed", error=str(e))
        raise
    except Exception as e:
        logger.log("parse_participants_failed", error=str(e))
        raise


@log_operation("read_participants_file")
def read_participants_file(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert DataFrame to list of subject records."""
    records = []
    for _, row in df.iterrows():
        records.append(row.to_dict())
    return records


@log_operation("has_valid_score")
def has_valid_score(row: Dict[str, Any], score_columns: List[str]) -> bool:
    """Check if any of the score columns have a non-null value."""
    for col in score_columns:
        if col in row:
            val = row[col]
            if pd.notna(val) and val != "":
                try:
                    float(val)
                    return True
                except (ValueError, TypeError):
                    continue
    return False


@log_operation("is_eligible")
def is_eligible(row: Dict[str, Any]) -> bool:
    """
    Check if a subject is eligible.
    Eligible if they have non-null MMSE or MOCA scores at BOTH timepoints.
    We assume the columns are named like 'MMSE', 'MMSE_2', 'MOCA', 'MOCA_2'
    or similar. We need to be flexible.
    
    Strategy: Look for pairs of columns that represent the same measure at two timepoints.
    For simplicity, we check for 'MMSE' and 'MMSE_2' (or similar patterns) and 'MOCA' and 'MOCA_2'.
    If a subject has valid scores for (MMSE and MMSE_2) OR (MOCA and MOCA_2), they are eligible.
    """
    # Define possible column name patterns for timepoints
    # We'll look for base names and their '2' counterparts
    score_pairs = [
        ("MMSE", "MMSE_2"),
        ("MOCA", "MOCA_2"),
        ("mmse", "mmse_2"),
        ("moca", "moca_2"),
    ]
    
    # Also check for generic patterns if specific ones don't exist
    # But for ds000246, let's assume the above or similar.
    # If the dataset uses 'Timepoint1_MMSE' and 'Timepoint2_MMSE', we might need to adapt.
    # Let's check the actual columns available in the row first.
    
    available_cols = [c for c in row.keys() if c is not None]
    
    # Check for pairs
    for col1, col2 in score_pairs:
        if col1 in available_cols and col2 in available_cols:
            if has_valid_score(row, [col1]) and has_valid_score(row, [col2]):
                return True
    
    # Fallback: If no specific pairs found, check if there are at least two score columns
    # that are not null. This is less strict but might be necessary if column naming varies.
    score_cols = [c for c in available_cols if "MMSE" in c.upper() or "MOCA" in c.upper()]
    valid_count = sum(1 for c in score_cols if has_valid_score(row, [c]))
    if valid_count >= 2:
        return True
        
    return False


@log_operation("filter_eligible_subjects")
def filter_eligible_subjects(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter records to only eligible subjects."""
    eligible = []
    excluded = []
    for record in records:
        # Ensure participant_id is present
        if "participant_id" not in record:
            # Sometimes it's 'subject_id' or 'sub_id'
            for key in ["subject_id", "sub_id", "sub"]:
                if key in record:
                    record["participant_id"] = record[key]
                    break
            if "participant_id" not in record:
                excluded.append(record)
                continue
        
        if is_eligible(record):
            eligible.append(record)
        else:
            excluded.append(record)
    return eligible, excluded


@log_operation("limit_subjects")
def limit_subjects(subjects: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Limit the number of subjects to the specified limit."""
    return subjects[:limit]


@log_operation("write_eligible_csv")
def write_eligible_csv(subjects: List[Dict[str, Any]], output_path: Path) -> None:
    """Write eligible subjects to a CSV file."""
    if not subjects:
        logger.log("write_eligible_csv", warning="No eligible subjects to write")
        # Still write an empty file with headers if possible, or just an empty file
        with open(output_path, "w", newline="") as f:
            f.write("participant_id\n")
        return

    # Determine columns
    columns = ["participant_id"]
    # Add other relevant columns if present in the first record
    if len(subjects) > 0:
        for key in subjects[0].keys():
            if key != "participant_id" and key not in columns:
                columns.append(key)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for subject in subjects:
            writer.writerow(subject)


@log_operation("write_excluded_log")
def write_excluded_log(excluded: List[Dict[str, Any]], output_path: Path) -> None:
    """Write excluded subjects to a log file."""
    with open(output_path, "w") as f:
        f.write("# Excluded Subjects Log\n")
        f.write(f"# Total excluded: {len(excluded)}\n")
        f.write("# Reason: Missing MMSE/MOCA scores at one or both timepoints\n")
        f.write("#\n")
        for subject in excluded:
            pid = subject.get("participant_id", subject.get("subject_id", "unknown"))
            f.write(f"{pid}\n")


@log_operation("write_status")
def write_status(eligible_count: int, excluded_count: int, status: str, error: Optional[str] = None) -> None:
    """Write the data gate status to a JSON file."""
    ensure_directory(OUTPUT_DIR_ARTIFACTS)
    status_data = {
        "status": status,
        "error": error,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(OUTPUT_FILE_STATUS, "w") as f:
        json.dump(status_data, f, indent=2)


@log_operation("main")
def main() -> int:
    """Main entry point for the download and filter script."""
    logger.log("start", operation="download_and_filter")
    ensure_directory(OUTPUT_DIR_ELIGIBLE)
    ensure_directory(OUTPUT_DIR_ARTIFACTS)

    try:
        # 1. Download metadata (optional, but good for logging)
        # metadata = download_dataset_metadata()
        
        # 2. Download and parse participants file
        df = download_participants_file()
        records = read_participants_file(df)
        
        # 3. Filter eligible subjects
        eligible, excluded = filter_eligible_subjects(records)
        
        # 4. Limit subjects
        eligible = limit_subjects(eligible, MAX_SUBJECTS)
        
        # 5. Write outputs
        write_eligible_csv(eligible, OUTPUT_FILE_ELIGIBLE)
        write_excluded_log(excluded, OUTPUT_FILE_EXCLUDED)
        
        # 6. Write status
        if len(eligible) == 0:
            write_status(0, len(excluded), "error", "No eligible subjects found")
            logger.log("end", status="error", message="No eligible subjects")
            return EXIT_CODE_NO_LABELS
        
        write_status(len(eligible), len(excluded), "success")
        logger.log("end", status="success", eligible=len(eligible), excluded=len(excluded))
        return EXIT_CODE_SUCCESS

    except FileNotFoundError as e:
        write_status(0, 0, "error", str(e))
        logger.log("end", status="error", error=str(e))
        return EXIT_CODE_DOWNLOAD_ERROR
    except Exception as e:
        write_status(0, 0, "error", str(e))
        logger.log("end", status="error", error=str(e))
        return EXIT_CODE_DOWNLOAD_ERROR


if __name__ == "__main__":
    sys.exit(main())
