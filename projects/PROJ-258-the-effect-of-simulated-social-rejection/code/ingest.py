"""
Ingestion module for the Social Rejection study.
Handles downloading, validation, design determination, and citation generation.
Implements T003: size estimation, streaming download, and dataset manifest creation.
Updated to use the OpenNeuro “crn” download endpoint and robust ZIP validation.
"""
import os
import sys
import json
import hashlib
import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
import requests

from config import get_path, MAX_RAM_GB
from data_model import Dataset, PreprocessedRecord, AnalysisResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
REJECTION_DATASET_ID = "ds000208"
REWARD_DATASET_ID = "ds003392"
REQUIRED_COLUMNS_T004 = [
    "participant_id",
    "condition",
    "reaction_time",
    "mood_rating",
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def setup_paths() -> Dict[str, str]:
    """Initialize project paths."""
    base_dir = get_path("project_root")
    paths = {
        "raw": os.path.join(base_dir, "data", "raw"),
        "interim": os.path.join(base_dir, "data", "interim"),
        "processed": os.path.join(base_dir, "data", "processed"),
        "reports": os.path.join(base_dir, "reports"),
        "state": os.path.join(base_dir, "state", "projects"),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths

def get_process_memory_check() -> float:
    """Check current process memory usage (GB)."""
    try:
        import resource

        mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is in KiB
        return mem_usage / (1024 * 1024)
    except Exception:
        logger.warning("resource module not available, skipping memory check")
        return 0.0

def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate hash of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def save_checksums(
    checksums: Dict[str, Dict[str, Any]], state_path: str
) -> None:
    """Save checksums to a state file."""
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

# ----------------------------------------------------------------------
# Size estimation (HEAD request) – abort if > MAX_RAM_GB
# ----------------------------------------------------------------------
def _zip_download_url(dataset_id: str) -> str:
    """
    Construct the OpenNeuro CRN download URL.
    This endpoint reliably redirects to the actual ZIP archive.
    """
    return f"https://openneuro.org/crn/datasets/{dataset_id}/download?format=zip"

def estimate_dataset_size_from_zip(dataset_id: str) -> float:
    """
    Perform a HEAD request on the OpenNeuro ZIP download endpoint.
    Returns size in GB. Exits with code 1 if size exceeds MAX_RAM_GB.
    """
    zip_url = _zip_download_url(dataset_id)
    try:
        head = requests.head(
            zip_url, timeout=15, allow_redirects=True, headers={"User-Agent": "python-requests"}
        )
        head.raise_for_status()
        size_bytes = int(head.headers.get("Content-Length", 0))
        size_gb = size_bytes / (1024 ** 3)
        logger.info(f"Estimated ZIP size for {dataset_id}: {size_gb:.2f} GB")
        if size_gb > MAX_RAM_GB:
            logger.error(
                f"Dataset {dataset_id} estimated size ({size_gb:.2f} GB) exceeds "
                f"memory limit ({MAX_RAM_GB} GB). Halting."
            )
            sys.exit(1)
        return size_gb
    except requests.RequestException as e:
        logger.error(f"Failed to estimate size for {dataset_id}: {e}")
        sys.exit(1)

# ----------------------------------------------------------------------
# Download ZIP, extract, and return list of extracted file metadata
# ----------------------------------------------------------------------
def _is_zip_file(path: Path) -> bool:
    """Very light check: first four bytes should be PK\x03\x04."""
    try:
        with open(path, "rb") as f:
            signature = f.read(4)
        return signature == b"PK\x03\x04"
    except Exception:
        return False

def download_and_extract_zip(dataset_id: str, raw_dir: str) -> List[Dict[str, Any]]:
    """
    Downloads the dataset ZIP, streams it to disk, validates it,
    extracts all files into ``raw_dir`` preserving internal folder structure,
    and returns a list of metadata dictionaries for each extracted file.
    """
    zip_url = _zip_download_url(dataset_id)
    zip_path = Path(raw_dir) / f"{dataset_id}.zip"
    logger.info(f"Downloading ZIP for {dataset_id} → {zip_path}")

    # Stream download to avoid loading whole ZIP into memory
    with requests.get(zip_url, stream=True, timeout=60, headers={"User-Agent": "python-requests"}) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    # Verify that the downloaded file is a valid ZIP archive
    if not _is_zip_file(zip_path):
        logger.error(f"The downloaded file for {dataset_id} is not a valid ZIP archive.")
        zip_path.unlink(missing_ok=True)
        sys.exit(1)

    # Extract
    logger.info(f"Extracting {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(raw_dir)

    # Build file list metadata
    extracted_files = []
    for file_path in Path(raw_dir).rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(raw_dir)
            size = file_path.stat().st_size
            extracted_files.append(
                {
                    "filename": str(rel_path),
                    "size": size,
                    "url": zip_url,
                }
            )

    # Clean up the downloaded ZIP (keep only extracted contents)
    zip_path.unlink(missing_ok=True)

    logger.info(f"Extracted {len(extracted_files)} files for {dataset_id}")
    return extracted_files

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Lower‑case column names and replace spaces with underscores.
    This makes later validation tolerant to naming variations.
    """
    return df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))

def _validate_required_columns(df: pd.DataFrame, dataset_name: str) -> None:
    """
    Ensures that the dataframe contains all columns required by T004.
    Exits with code 1 if any are missing.
    """
    missing = [col for col in REQUIRED_COLUMNS_T004 if col not in df.columns]
    if missing:
        logger.error(
            f"Dataset '{dataset_name}' is missing required columns: {missing}"
        )
        sys.exit(1)

# ----------------------------------------------------------------------
# Locate primary CSV (contains required columns) and copy to canonical name
# ----------------------------------------------------------------------
def locate_and_copy_primary_csv(dataset_id: str, raw_dir: str) -> None:
    """
    Search the extracted files for a CSV/TSV that contains the required columns.
    When found, copy it to raw_dir as 'rejection.csv' or 'reward.csv'.
    """
    target_name = "rejection.csv" if dataset_id == REJECTION_DATASET_ID else "reward.csv"
    raw_path = Path(raw_dir)

    for candidate in raw_path.rglob("*"):
        if candidate.suffix.lower() not in {".csv", ".tsv"}:
            continue
        try:
            # Read a small sample to infer delimiter
            df_sample = pd.read_csv(candidate, nrows=20, sep=None, engine="python")
        except Exception:
            continue
        df_sample = _normalize_columns(df_sample)
        if all(col in df_sample.columns for col in REQUIRED_COLUMNS_T004):
            shutil.copy(candidate, raw_path / target_name)
            logger.info(
                f"Primary CSV for dataset {dataset_id} identified and copied to {target_name}"
            )
            return
    logger.error(
        f"Could not locate a primary CSV with required columns for dataset {dataset_id}"
    )
    sys.exit(1)

# ----------------------------------------------------------------------
# Condition report (T004)
# ----------------------------------------------------------------------
def process_condition_report() -> Dict[str, Any]:
    """
    Loads the primary CSV from each dataset (rejection and reward),
    validates column presence, checks that both 'Rejection' and 'Control'
    conditions appear in the rejection dataset, and that the reward
    dataset contains the required variables. Writes the report to
    data/interim/condition_report.json and returns the report dict.
    """
    raw_dir = get_path("raw")
    interim_dir = get_path("interim")
    os.makedirs(interim_dir, exist_ok=True)

    rejection_csv = os.path.join(raw_dir, "rejection.csv")
    reward_csv = os.path.join(raw_dir, "reward.csv")

    if not os.path.exists(rejection_csv) or not os.path.exists(reward_csv):
        logger.error("Required CSV files not found after ingestion.")
        sys.exit(1)

    df_rej = pd.read_csv(rejection_csv)
    df_rej = _normalize_columns(df_rej)

    df_reward = pd.read_csv(reward_csv)
    df_reward = _normalize_columns(df_reward)

    _validate_required_columns(df_rej, "rejection")
    _validate_required_columns(df_reward, "reward")

    # Condition checks for the rejection dataset.
    rejection_present = "rejection" in df_rej["condition"].unique()
    control_present = "control" in df_rej["condition"].unique()
    reward_present = True  # schema already validated

    report = {
        "rejection_present": bool(rejection_present),
        "control_present": bool(control_present),
        "reward_present": bool(reward_present),
    }

    report_path = os.path.join(interim_dir, "condition_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Condition report written to {report_path}")
    return report

# ----------------------------------------------------------------------
# Overlap and design determination (T005)
# ----------------------------------------------------------------------
def process_overlap_and_design() -> None:
    """
    T005 implementation:
    1. Compute participant ID sets for rejection (across all conditions) and reward datasets.
    2. Write overlap_report.json containing overlap flag and the two ID lists.
    3. Decide design_type based on overlap and write design_branch.json.
    4. Append (or create) data/processed/metadata.json with the design decision.
    """
    raw_dir = get_path("raw")
    interim_dir = get_path("interim")
    processed_dir = get_path("processed")
    os.makedirs(interim_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    rejection_csv = os.path.join(raw_dir, "rejection.csv")
    reward_csv = os.path.join(raw_dir, "reward.csv")

    df_rej = pd.read_csv(rejection_csv)
    df_rej = _normalize_columns(df_rej)

    df_reward = pd.read_csv(reward_csv)
    df_reward = _normalize_columns(df_reward)

    rej_ids = sorted(df_rej["participant_id"].astype(str).unique().tolist())
    rew_ids = sorted(df_reward["participant_id"].astype(str).unique().tolist())

    overlap = bool(set(rej_ids) & set(rew_ids))

    # 1. overlap_report.json
    overlap_report = {
        "overlap": overlap,
        "rejection_ids": rej_ids,
        "reward_ids": rew_ids,
    }
    overlap_path = os.path.join(interim_dir, "overlap_report.json")
    with open(overlap_path, "w", encoding="utf-8") as f:
        json.dump(overlap_report, f, indent=2)
    logger.info(f"Overlap report written to {overlap_path}")

    # 2. design_branch.json
    design_type = "Within-Subjects" if overlap else "Between-Subjects"
    reason = "Participant ID overlap detected" if overlap else "No participant ID overlap"
    design_branch = {"design_type": design_type, "reason": reason}
    design_path = os.path.join(interim_dir, "design_branch.json")
    with open(design_path, "w", encoding="utf-8") as f:
        json.dump(design_branch, f, indent=2)
    logger.info(f"Design branch written to {design_path}")

    # 3. metadata.json (processed)
    metadata_path = os.path.join(processed_dir, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = {}

    metadata.update(
        {
            "design_type": design_type,
            "design_reason": reason,
            "design_determined_at": datetime.utcnow().isoformat(),
        }
    )

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata updated at {metadata_path}")

# ----------------------------------------------------------------------
# Dataset manifest (T003)
# ----------------------------------------------------------------------
def write_dataset_manifest(manifest_entries: List[Dict[str, Any]], raw_dir: str) -> None:
    """Write the dataset manifest JSON file into the raw directory."""
    manifest_path = os.path.join(raw_dir, "dataset_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_entries, f, indent=2)
    logger.info(f"Dataset manifest written to {manifest_path}")

# ----------------------------------------------------------------------
# Citation generation (T006 – part of ingestion)
# ----------------------------------------------------------------------
def write_citation_file() -> None:
    """
    Creates data/raw/CITATION.md citing both OpenNeuro datasets with DOI
    and the access date.
    """
    citation_path = Path(get_path("raw")) / "CITATION.md"
    access_date = datetime.utcnow().strftime("%Y-%m-%d")
    content = (
        f"# Dataset Citations\n\n"
        f"- ds000208 (Rejection): DOI 10.18112/openneuro.ds000208.v1.0.0, accessed {access_date}\n"
        f"- ds003392 (Reward):   DOI 10.18112/openneuro.ds003392.v1.0.0, accessed {access_date}\n"
    )
    citation_path.write_text(content, encoding="utf-8")
    logger.info(f"Citation file written to {citation_path}")

# ----------------------------------------------------------------------
# Main ingestion entry point
# ----------------------------------------------------------------------
def run_ingestion() -> None:
    """Main entry point for the ingestion pipeline (T003‑T006)."""
    paths = setup_paths()
    raw_dir = paths["raw"]

    manifest_entries: List[Dict[str, Any]] = []

    for dataset_id in [REJECTION_DATASET_ID, REWARD_DATASET_ID]:
        # 1. Estimate size (via HEAD) and enforce memory limit
        estimate_dataset_size_from_zip(dataset_id)

        # 2. Download ZIP and extract
        file_list = download_and_extract_zip(dataset_id, raw_dir)

        # 3. Identify primary CSV and copy to canonical name
        locate_and_copy_primary_csv(dataset_id, raw_dir)

        # 4. Build manifest entry for this dataset
        total_size_bytes = sum(fi.get("size", 0) for fi in file_list)
        entry = {
            "url": f"https://openneuro.org/datasets/{dataset_id}",
            "sha256": None,
            "size_bytes": total_size_bytes,
            "file_count": len(file_list),
            "dataset_id": dataset_id,
        }
        manifest_entries.append(entry)

    # Write the manifest file
    write_dataset_manifest(manifest_entries, raw_dir)

    # Generate citation file
    write_citation_file()

    # Continue with downstream validation steps (T004 & T005)
    process_condition_report()
    process_overlap_and_design()

    logger.info("Ingestion pipeline (T003‑T006) completed successfully.")

if __name__ == "__main__":
    run_ingestion()