import os
import sys
import json
import hashlib
import logging
import tempfile
import time
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Local imports based on API surface
from config import get_path, set_random_seed
from data_model import DesignType, Dataset, PreprocessedRecord, AnalysisResult
from logging_utils import get_process_memory_mb, setup_memory_logger, log_memory_snapshot

# Constants
MEMORY_LIMIT_GB = 7.0
TIMEOUT_SECONDS = 300
REJECTION_DATASET_ID = "ds000208"
REWARD_DATASET_ID = "ds003392"

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def setup_paths():
    """Initialize project directories and return path dictionary."""
    paths = {
        "root": get_path("project_root"),
        "raw": get_path("raw_data"),
        "interim": get_path("interim_data"),
        "processed": get_path("processed_data"),
        "checks": get_path("checksums"),
        "logs": get_path("logs")
    }
    
    for path_name, path in paths.items():
        os.makedirs(path, exist_ok=True)
    
    return paths

def get_process_memory_check(limit_gb: float = MEMORY_LIMIT_GB):
    """Returns a function that checks current process memory usage."""
    limit_mb = limit_gb * 1024
    
    def check_memory():
        current_mb = get_process_memory_mb()
        if current_mb > limit_mb:
            logger.error(f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB")
            return False
        return True
    
    return check_memory

def calculate_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksums(paths: Dict[str, str], files: Dict[str, str]):
    """Save checksums to data/raw/checksums.json."""
    checksum_file = os.path.join(paths["raw"], "checksums.json")
    checksums = {}
    
    for name, filepath in files.items():
        if os.path.exists(filepath):
            checksums[name] = {
                "path": filepath,
                "hash": calculate_file_hash(filepath),
                "size_bytes": os.path.getsize(filepath)
            }
    
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Checksums saved to {checksum_file}")
    return checksum_file

def download_dataset(url: str, dest_path: str, timeout: int = TIMEOUT_SECONDS) -> str:
    """Download a dataset from a URL with retry logic."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    logger.info(f"Downloading dataset from {url} to {dest_path}")
    
    try:
        response = session.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if progress % 10 == 0:
                            logger.debug(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Download complete: {dest_path}")
        return dest_path
        
    except requests.RequestException as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def load_dataframe(filepath: str) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def verify_tasks_in_dataset(df: pd.DataFrame, required_tasks: list) -> bool:
    """Check if the dataset contains all required task conditions."""
    # Expected condition columns for Cyberball and Reward tasks
    cyberball_conditions = ["Inclusion", "Exclusion"]
    reward_conditions = ["Win", "Loss"]
    
    has_cyberball = any(cond in df["Condition"].unique() for cond in cyberball_conditions)
    has_reward = any(cond in df["Condition"].unique() for cond in reward_conditions)
    
    if has_cyberball and has_reward:
        logger.info("Dataset contains both Cyberball and Reward tasks")
        return True
    
    if has_cyberball:
        logger.info("Dataset contains only Cyberball task")
        return False
    
    if has_reward:
        logger.info("Dataset contains only Reward task")
        return False
    
    logger.warning("Dataset contains neither Cyberball nor Reward tasks")
    return False

def validate_schema(df: pd.DataFrame) -> bool:
    """Validate that the DataFrame contains required columns."""
    required_columns = ["Participant", "Condition", "Reaction Time", "Mood"]
    
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    
    logger.info("Schema validation passed")
    return True

def verify_single_cohort(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Verify if a single dataset contains both tasks for the same participants.
    Returns (is_single_cohort, design_type).
    """
    if not validate_schema(df):
        return False, "Invalid Schema"
    
    # Check if both tasks exist
    has_both_tasks = verify_tasks_in_dataset(df, ["Cyberball", "Reward"])
    
    if has_both_tasks:
        # Verify participant consistency within single dataset
        participants = df["Participant"].unique()
        logger.info(f"Found {len(participants)} unique participants in single cohort")
        return True, DesignType.WITHIN_SUBJECTS.value
    
    return False, "NEEDS_COMPOSITE"

def log_design_switch(
    paths: Dict[str, str], 
    from_design: str, 
    to_design: str, 
    reason: str = "Single-cohort dataset not found"
):
    """
    Explicitly record the transition from 'Single-Cohort attempt' to 'Composite Fallback'
    in the execution log, ensuring traceability for the 'associational' framing.
    
    This function writes a structured log entry to a dedicated design_switch_log.json
    file in the logs directory.
    """
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": "DESIGN_SWITCH",
        "from_design": from_design,
        "to_design": to_design,
        "reason": reason,
        "traceability": {
            "framing": "associational",
            "rationale": "Transition to Between-Subjects design due to lack of single-cohort data. "
                        "Results will be framed as associational group differences rather than causal modulation."
        }
    }
    
    log_file = os.path.join(paths["logs"], "design_switch_log.json")
    
    # Load existing log if it exists
    existing_logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                existing_logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_logs = []
    
    # Append new entry
    existing_logs.append(log_entry)
    
    # Write back
    with open(log_file, 'w') as f:
        json.dump(existing_logs, f, indent=2)
    
    logger.info(f"Design switch logged: {from_design} -> {to_design} (Reason: {reason})")
    logger.info(f"Log entry saved to {log_file}")
    
    return log_file

def validate_composite_datasets(df_rejection: pd.DataFrame, df_reward: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate composite datasets by matching Participant IDs across distinct datasets.
    Returns (is_valid, design_type).
    """
    if not validate_schema(df_rejection) or not validate_schema(df_reward):
        return False, "Invalid Schema"
    
    # Check for Cyberball in rejection dataset
    has_cyberball = "Exclusion" in df_rejection["Condition"].unique() or "Inclusion" in df_rejection["Condition"].unique()
    if not has_cyberball:
        logger.error("Rejection dataset does not contain Cyberball task")
        return False, "INVALID_REJECTION"
    
    # Check for Reward in reward dataset
    has_reward = "Win" in df_reward["Condition"].unique() or "Loss" in df_reward["Condition"].unique()
    if not has_reward:
        logger.error("Reward dataset does not contain Reward task")
        return False, "INVALID_REWARD"
    
    # Match participant IDs
    participants_rejection = set(df_rejection["Participant"].unique())
    participants_reward = set(df_reward["Participant"].unique())
    
    matching_ids = participants_rejection.intersection(participants_reward)
    
    if not matching_ids:
        logger.error("No matching participant IDs between datasets")
        return False, "NO_MATCHING_IDS"
    
    logger.info(f"Found {len(matching_ids)} matching participant IDs")
    return True, DesignType.BETWEEN_SUBJECTS.value

def run_ingestion():
    """
    Main ingestion pipeline:
    1. Attempt to download single-cohort dataset
    2. If not found, proceed to composite dataset strategy
    3. Log design switch if fallback occurs
    """
    paths = setup_paths()
    check_memory = get_process_memory_check()
    
    # Step 1: Attempt single-cohort download
    logger.info("=== Phase 1: Attempting Single-Cohort Dataset ===")
    single_cohort_url = f"https://api.openneuro.org/datasets/{REJECTION_DATASET_ID}/download"
    single_cohort_path = os.path.join(paths["raw"], f"{REJECTION_DATASET_ID}_combined.csv")
    
    single_cohort_found = False
    
    try:
        # In a real scenario, we would check if the file exists or download it
        # For this implementation, we simulate the check
        if os.path.exists(single_cohort_path):
            df_single = load_dataframe(single_cohort_path)
            is_valid, design_type = verify_single_cohort(df_single)
            
            if is_valid:
                single_cohort_found = True
                logger.info(f"Single-cohort dataset found: {design_type}")
                save_checksums(paths, {"single_cohort": single_cohort_path})
            else:
                logger.info("Single-cohort dataset does not contain both tasks")
        else:
            logger.info("Single-cohort dataset not found, proceeding to composite strategy")
            
    except Exception as e:
        logger.warning(f"Single-cohort check failed: {e}. Proceeding to composite strategy.")
    
    # Step 2: If single-cohort not found, use composite strategy
    if not single_cohort_found:
        logger.info("=== Phase 2: Composite Dataset Strategy (Fallback) ===")
        
        # Log the design switch
        log_design_switch(
            paths=paths,
            from_design="Within-Subjects (Single-Cohort)",
            to_design="Between-Subjects (Composite)",
            reason="Single-cohort dataset not found or does not contain both tasks"
        )
        
        # Download composite datasets
        rejection_path = os.path.join(paths["raw"], f"{REJECTION_DATASET_ID}_rejection.csv")
        reward_path = os.path.join(paths["raw"], f"{REWARD_DATASET_ID}_reward.csv")
        
        try:
            # In real implementation, these would be actual URLs
            # For now, we simulate the existence check
            if not os.path.exists(rejection_path):
                # Simulate download
                logger.info(f"Simulating download of {REJECTION_DATASET_ID}")
                # In real code: download_dataset(url, rejection_path)
                
            if not os.path.exists(reward_path):
                # Simulate download
                logger.info(f"Simulating download of {REWARD_DATASET_ID}")
                # In real code: download_dataset(url, reward_path)
            
            df_rejection = load_dataframe(rejection_path) if os.path.exists(rejection_path) else pd.DataFrame()
            df_reward = load_dataframe(reward_path) if os.path.exists(reward_path) else pd.DataFrame()
            
            if df_rejection.empty or df_reward.empty:
                logger.error("Could not load composite datasets")
                sys.exit(1)
            
            is_valid, design_type = validate_composite_datasets(df_rejection, df_reward)
            
            if is_valid:
                logger.info(f"Composite dataset strategy successful: {design_type}")
                save_checksums(paths, {
                    "rejection": rejection_path,
                    "reward": reward_path
                })
            else:
                logger.error(f"Composite dataset validation failed: {design_type}")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Composite dataset strategy failed: {e}")
            sys.exit(1)
    
    logger.info("Ingestion pipeline completed successfully")
    return paths

if __name__ == "__main__":
    run_ingestion()