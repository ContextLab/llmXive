"""
Ingestion module for the Social Rejection study.
Handles downloading, validation, design determination, and citation generation.
Updated to implement T004 and T005:
  - T004: load primary CSVs for rejection and reward datasets,
    validate required columns, and produce data/interim/condition_report.json.
  - T005: compute participant‑ID overlap, decide experimental design,
    and emit overlap_report.json, design_branch.json and update metadata.json.
"""
import os
import sys
import json
import hashlib
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import requests
from datasets import load_dataset

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

def estimate_dataset_size_from_api(url: str) -> float:
    """
    Fetch metadata (size, file count) directly from the OpenNeuro API.
    Returns estimated size in GB.
    """
    try:
        api_url = f"{OPENNEURO_API_BASE}/datasets/{url}/files"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        total_size_bytes = 0
        if isinstance(data, list):
            for file_info in data:
                if 'size' in file_info:
                    total_size_bytes += file_info['size']
        elif isinstance(data, dict) and 'files' in data:
            for file_info in data['files']:
                if 'size' in file_info:
                    total_size_bytes += file_info['size']
        total_size_gb = total_size_bytes / (1024 ** 3)
        logger.info(f"Estimated dataset size: {total_size_gb:.2f} GB")
        if total_size_gb > MAX_RAM_GB:
            logger.error(f"Dataset size ({total_size_gb:.2f} GB) exceeds memory limit ({MAX_RAM_GB} GB)")
            sys.exit(1)
        return total_size_gb
    except requests.RequestException as e:
        logger.warning(f"API Unreachable, proceeding to local check: {e}")
        return 0.0

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

def _download_and_save_dataset(dataset_id: str, target_csv_name: str) -> pd.DataFrame:
    """
    Uses the HuggingFace `datasets` library to download the OpenNeuro dataset,
    extracts the first table that contains the required columns, writes it to
    a CSV in the raw directory, and returns the DataFrame.
    """
    logger.info(f"Downloading dataset {dataset_id} via HuggingFace `datasets` library...")
    # The huggingface identifier follows the pattern "openneuro/dsXXXXX"
    hf_name = f"openneuro/{dataset_id}"
    try:
        ds = load_dataset(hf_name, split="train")
    except Exception as e:
        logger.error(f"Failed to load dataset {hf_name}: {e}")
        sys.exit(1)

    # Convert to pandas DataFrame
    df = ds.to_pandas()
    df = _normalize_columns(df)

    # Validate that we have the required columns; if not, try to locate a different split/table
    try:
        _validate_required_columns(df, dataset_id)
    except SystemExit:
        # If validation fails, attempt to search other splits (e.g., 'validation')
        logger.warning(f"Primary split of {dataset_id} does not contain required columns. Trying alternate splits...")
        for split_name in ds.builder_config_names:
            try:
                alt_ds = load_dataset(hf_name, split=split_name)
                alt_df = _normalize_columns(alt_ds.to_pandas())
                _validate_required_columns(alt_df, dataset_id)
                df = alt_df
                logger.info(f"Found required columns in split '{split_name}'.")
                break
            except Exception:
                continue
        else:
            logger.error(f"Unable to locate required columns in any split of {dataset_id}.")
            sys.exit(1)

    # Save to CSV in raw directory
    raw_dir = get_path("raw")
    os.makedirs(raw_dir, exist_ok=True)
    csv_path = os.path.join(raw_dir, target_csv_name)
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved dataset {dataset_id} to {csv_path}")

    return df

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

    # ------------------------------------------------------------------
    # Step 1: Ensure CSV files exist – download if missing
    # ------------------------------------------------------------------
    rejection_csv = os.path.join(raw_dir, "rejection.csv")
    reward_csv = os.path.join(raw_dir, "reward.csv")

    if not os.path.exists(rejection_csv):
        df_rej = _download_and_save_dataset(REJECTION_DATASET_ID, "rejection.csv")
    else:
        df_rej = pd.read_csv(rejection_csv)
        df_rej = _normalize_columns(df_rej)

    if not os.path.exists(reward_csv):
        df_reward = _download_and_save_dataset(REWARD_DATASET_ID, "reward.csv")
    else:
        df_reward = pd.read_csv(reward_csv)
        df_reward = _normalize_columns(df_reward)

    # ------------------------------------------------------------------
    # Step 2: Validate required schema for BOTH datasets.
    # ------------------------------------------------------------------
    _validate_required_columns(df_rej, "rejection")
    _validate_required_columns(df_reward, "reward")

    # ------------------------------------------------------------------
    # Step 3: Condition checks for the rejection dataset.
    # ------------------------------------------------------------------
    rejection_present = "rejection" in df_rej["condition"].unique()
    control_present = "control" in df_rej["condition"].unique()

    # Reward dataset presence – we already validated its schema, so set True.
    reward_present = True

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

    # Load CSVs (they must exist – process_condition_report already ensured this)
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

    # Update/append design information
    metadata.update({
        "design_type": design_type,
        "design_reason": reason,
        "design_determined_at": datetime.utcnow().isoformat()
    })

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata updated at {metadata_path}")

def run_ingestion():
    """Main entry point for the ingestion pipeline."""
    paths = setup_paths()

    # Size estimation (optional – can be activated if needed)
    # estimate_dataset_size_from_api(REJECTION_DATASET_ID)
    # estimate_dataset_size_from_api(REWARD_DATASET_ID)

    # Process condition report (T004)
    process_condition_report()

    # Process overlap and design decision (T005)
    process_overlap_and_design()

    logger.info("Ingestion pipeline (T004 + T005) completed successfully.")

if __name__ == "__main__":
    run_ingestion()