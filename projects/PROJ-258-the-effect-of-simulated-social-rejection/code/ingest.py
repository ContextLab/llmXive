"""
Ingestion module for the Social Rejection study.
Handles downloading, validation, design determination, and citation generation.
Implements T003: size estimation, streaming download, and dataset manifest creation.
"""
import os
import sys
import json
import hashlib
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
import requests

from config import get_path, MAX_RAM_GB
from data_model import Dataset, PreprocessedRecord, AnalysisResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
OPENNEURO_API_BASE = "https://api.openneuro.org"
REJECTION_DATASET_ID = "ds000208"
REWARD_DATASET_ID = "ds003392"
REQUIRED_COLUMNS_T004 = ["participant_id", "condition", "reaction_time", "mood_rating"]

def setup_paths():
    """Initialize project paths."""
    base_dir = get_path("project_root")
    paths = {
        "raw": os.path.join(base_dir, "data", "raw"),
        "interim": os.path.join(base_dir, "data", "interim"),
        "processed": os.path.join(base_dir, "data", "processed"),
        "reports": os.path.join(base_dir, "reports"),
        "state": os.path.join(base_dir, "state", "projects")
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths

def get_process_memory_check():
    """Check current process memory usage."""
    try:
        import resource
        mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is in KB
        return mem_usage / (1024 * 1024)  # GB
    except ImportError:
        logger.warning("resource module not available, skipping memory check")
        return 0.0

def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate hash of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def save_checksums(checksums: Dict[str, Dict[str, Any]], state_path: str):
    """Save checksums to state file."""
    with open(state_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def estimate_dataset_size_from_api(dataset_id: str) -> float:
    """
    Fetch metadata (size, file count) directly from the OpenNeuro API.
    Returns estimated size in GB.
    """
    try:
        api_url = f"{OPENNEURO_API_BASE}/datasets/{dataset_id}/files"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        total_size_bytes = 0
        if isinstance(data, list):
            for file_info in data:
                total_size_bytes += file_info.get('size', 0)
        elif isinstance(data, dict) and 'files' in data:
            for file_info in data['files']:
                total_size_bytes += file_info.get('size', 0)
        total_size_gb = total_size_bytes / (1024 ** 3)
        logger.info(f"Estimated size for {dataset_id}: {total_size_gb:.2f} GB")
        if total_size_gb > MAX_RAM_GB:
            logger.error(
                f"Dataset {dataset_id} size ({total_size_gb:.2f} GB) exceeds memory limit ({MAX_RAM_GB} GB)"
            )
            sys.exit(1)
        return total_size_gb
    except requests.RequestException as e:
        logger.error(f"Failed to query OpenNeuro API for {dataset_id}: {e}")
        sys.exit(1)

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Lower‑case column names and replace spaces with underscores.
    This makes later validation tolerant to naming variations.
    """
    df = df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))
    return df

def _validate_required_columns(df: pd.DataFrame, dataset_name: str) -> None:
    """
    Ensures that the dataframe contains all columns required by T004.
    Exits with code 1 if any are missing.
    """
    missing = [col for col in REQUIRED_COLUMNS_T004 if col not in df.columns]
    if missing:
        logger.error(f"Dataset '{dataset_name}' is missing required columns: {missing}")
        sys.exit(1)

def fetch_dataset_file_list(dataset_id: str) -> List[Dict[str, Any]]:
    """Return the list of file metadata dictionaries for a given dataset."""
    api_url = f"{OPENNEURO_API_BASE}/datasets/{dataset_id}/files"
    resp = requests.get(api_url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "files" in data:
        return data["files"]
    else:
        logger.error(f"Unexpected file list format for dataset {dataset_id}")
        sys.exit(1)

def stream_download_file(url: str, dest_path: Path):
    """Download a single file via streaming to dest_path."""
    # Ensure parent directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {url} → {dest_path}")
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def download_dataset(dataset_id: str, raw_dir: str) -> List[Dict[str, Any]]:
    """
    Stream‑download all files for a dataset into raw_dir.
    Returns the list of file metadata dictionaries (as received from the API).
    """
    file_list = fetch_dataset_file_list(dataset_id)
    for file_info in file_list:
        file_url = file_info.get("url") or file_info.get("download_url")
        if not file_url:
            logger.warning(f"No URL found for file entry: {file_info}")
            continue
        # Some URLs may be relative; make them absolute if needed
        if file_url.startswith("/"):
            file_url = f"https://openneuro.org{file_url}"
        filename = file_info.get("filename") or file_info.get("path")
        if not filename:
            logger.warning(f"No filename for file entry: {file_info}")
            continue
        dest_path = Path(raw_dir) / filename
        stream_download_file(file_url, dest_path)
    return file_list

def locate_and_copy_primary_csv(dataset_id: str, raw_dir: str):
    """
    Search the downloaded raw files for a CSV/TSV that contains the required columns.
    When found, copy it to raw_dir as 'rejection.csv' or 'reward.csv' for downstream steps.
    """
    target_name = "rejection.csv" if dataset_id == REJECTION_DATASET_ID else "reward.csv"
    raw_path = Path(raw_dir)

    for candidate in raw_path.rglob("*"):
        if candidate.suffix.lower() not in {".csv", ".tsv"}:
            continue
        try:
            df_sample = pd.read_csv(candidate, nrows=20, sep=None, engine="python")
        except Exception:
            continue
        df_sample = _normalize_columns(df_sample)
        if all(col in df_sample.columns for col in REQUIRED_COLUMNS_T004):
            # Found a suitable file – copy it to the expected name
            shutil.copy(candidate, raw_path / target_name)
            logger.info(f"Primary CSV for dataset {dataset_id} identified and copied to {target_name}")
            return
    logger.error(f"Could not locate a primary CSV with required columns for dataset {dataset_id}")
    sys.exit(1)

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

    # Files should already exist after download; if not, abort.
    if not os.path.exists(rejection_csv) or not os.path.exists(reward_csv):
        logger.error("Required CSV files not found after ingestion.")
        sys.exit(1)

    df_rej = pd.read_csv(rejection_csv)
    df_rej = _normalize_columns(df_rej)

    df_reward = pd.read_csv(reward_csv)
    df_reward = _normalize_columns(df_reward)

    # Validate required schema for BOTH datasets.
    _validate_required_columns(df_rej, "rejection")
    _validate_required_columns(df_reward, "reward")

    # Condition checks for the rejection dataset.
    rejection_present = "rejection" in df_rej["condition"].unique()
    control_present = "control" in df_rej["condition"].unique()
    reward_present = True  # schema already validated

    report = {
        "rejection_present": bool(rejection_present),
        "control_present": bool(control_present),
        "reward_present": bool(reward_present)
    }

    report_path = os.path.join(interim_dir, "condition_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Condition report written to {report_path}")
    return report

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

    # Compute unique participant IDs
    rej_ids = sorted(df_rej["participant_id"].astype(str).unique().tolist())
    rew_ids = sorted(df_reward["participant_id"].astype(str).unique().tolist())

    overlap = bool(set(rej_ids) & set(rew_ids))

    # 1. overlap_report.json
    overlap_report = {
        "overlap": overlap,
        "rejection_ids": rej_ids,
        "reward_ids": rew_ids
    }
    overlap_path = os.path.join(interim_dir, "overlap_report.json")
    with open(overlap_path, "w") as f:
        json.dump(overlap_report, f, indent=2)
    logger.info(f"Overlap report written to {overlap_path}")

    # 2. design_branch.json
    design_type = "Within-Subjects" if overlap else "Between-Subjects"
    reason = "Participant ID overlap detected" if overlap else "No participant ID overlap"
    design_branch = {
        "design_type": design_type,
        "reason": reason
    }
    design_path = os.path.join(interim_dir, "design_branch.json")
    with open(design_path, "w") as f:
        json.dump(design_branch, f, indent=2)
    logger.info(f"Design branch written to {design_path}")

    # 3. metadata.json (processed)
    metadata_path = os.path.join(processed_dir, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    else:
        metadata = {}

    metadata.update({
        "design_type": design_type,
        "design_reason": reason,
        "design_determined_at": datetime.utcnow().isoformat()
    })

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata updated at {metadata_path}")

def write_dataset_manifest(manifest_entries: List[Dict[str, Any]], raw_dir: str):
    """Write the dataset manifest JSON file into the raw directory."""
    manifest_path = os.path.join(raw_dir, "dataset_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_entries, f, indent=2)
    logger.info(f"Dataset manifest written to {manifest_path}")

def run_ingestion():
    """Main entry point for the ingestion pipeline (T003, T004, T005)."""
    paths = setup_paths()
    raw_dir = paths["raw"]

    manifest_entries = []

    for dataset_id in [REJECTION_DATASET_ID, REWARD_DATASET_ID]:
        # 1. Estimate size and enforce memory limit
        estimate_dataset_size_from_api(dataset_id)

        # 2. Stream‑download all files
        file_list = download_dataset(dataset_id, raw_dir)

        # 3. Identify primary CSV and copy to expected name
        locate_and_copy_primary_csv(dataset_id, raw_dir)

        # 4. Build manifest entry for this dataset
        total_size_bytes = sum(fi.get("size", 0) for fi in file_list)
        entry = {
            "url": f"https://openneuro.org/datasets/{dataset_id}",
            "sha256": None,
            "size_bytes": total_size_bytes,
            "file_count": len(file_list),
            "dataset_id": dataset_id
        }
        manifest_entries.append(entry)

    # Write the manifest file
    write_dataset_manifest(manifest_entries, raw_dir)

    # Continue with downstream steps (T004 & T005)
    process_condition_report()
    process_overlap_and_design()

    logger.info("Ingestion pipeline (T003‑T005) completed successfully.")

if __name__ == "__main__":
    run_ingestion()