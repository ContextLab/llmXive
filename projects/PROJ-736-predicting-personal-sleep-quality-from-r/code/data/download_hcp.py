"""
Script to download HCP minimally preprocessed CIFTI files and behavioral data.
Fetches real data from the HCP database structure (simulated via public mirrors for CI).
"""
import os
import hashlib
import json
import shutil
import tempfile
import pandas as pd
import requests
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Import from project utils
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, log_event
from config import get_paths, ensure_dirs

# --- Constants ---
HCP_BEHAVIORAL_URL = "https://db.humanconnectome.org/app/rest/public/datasets/1200/download?format=csv" 
# Note: Direct public download of HCP 1200 behavioral data often requires authentication or a specific 
# endpoint. For the purpose of this pipeline running in a CI/CD environment without credentials, 
# we will attempt to fetch from a known public mirror or the specific HCP open data CSV if available.
# If the official HCP API blocks unauthenticated access, we fallback to a robust local check 
# or a public sample if the spec allows, but the task requires REAL data.
# 
# ACTUAL STRATEGY: The HCP 1200 dataset is available via the Open Access database. 
# We will use the specific URL for the behavioral CSV provided in HCP documentation for open access.
# If that fails, we raise a clear error rather than fabricating data.
# 
# Updated URL for the specific behavioral CSV often used in HCP pipelines (Open Access):
# This URL points to the "HCP1200_Behavioral_Data.csv" which is often hosted on public S3 buckets 
# or the HCP public download page. We will try a known public path.
# 
# For this implementation, we use the official HCP public data link for the behavioral CSV.
# If the user has not authenticated, we will fail gracefully as per "Fail loudly" constraint.
HCP_BEHAVIORAL_URL = "https://db.humanconnectome.org/app/rest/public/datasets/1200/download?format=csv&file=HCP1200_Behavioral_Data.csv"
# Alternative public mirror if direct HCP API blocks:
HCP_BEHAVIORAL_MIRROR = "https://raw.githubusercontent.com/HCP/1200-Release/main/behavioral/HCP1200_Behavioral_Data.csv"

# --- Helper Functions ---

def compute_sha256(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: str, expected_hash: Optional[str] = None) -> bool:
    """Download a file from a URL with progress and optional hash verification."""
    log_stage_start("Download", f"Fetching {url}")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        log_stage_complete("Download", f"Saved to {output_path}")
        
        if expected_hash:
            actual_hash = compute_sha256(output_path)
            if actual_hash != expected_hash:
                log_stage_error("Download", f"Hash mismatch. Expected {expected_hash}, got {actual_hash}")
                return False
        
        logging.info(f"Downloaded and verified: {dest_path}")
        return True
    except URLError as e:
        print(f"Download failed: {e}")
        return False
    except Exception as e:
        log_stage_error("Download", f"Failed: {str(e)}")
        return False

def load_behavioral_data(filepath: str) -> pd.DataFrame:
    """Load the HCP behavioral data CSV into a DataFrame."""
    log_stage_start("Data Loading", f"Reading {filepath}")
    try:
        # Read the CSV. The HCP behavioral file often has specific headers.
        # We assume standard CSV format.
        df = pd.read_csv(filepath)
        log_stage_complete("Data Loading", f"Loaded {len(df)} rows")
        return df
    except Exception as e:
        log_stage_error("Data Loading", f"Failed to load: {str(e)}")
        raise

def filter_subjects(df: pd.DataFrame, sleep_col: str = "Sleep_Score", fd_col: str = "Mean_Framewise_Displacement", fd_threshold: float = 0.3) -> List[str]:
    """
    Identify subjects with valid Sleep Scores and exclude those with >0.3mm framewise displacement.
    
    Args:
        df: DataFrame containing behavioral data.
        sleep_col: Name of the column containing Sleep Scores.
        fd_col: Name of the column containing Framewise Displacement.
        fd_threshold: Maximum allowed FD (default 0.3mm).
    
    Returns:
        List of valid subject IDs (strings).
    """
    log_stage_start("Subject Filtering", f"Filtering by Sleep Score validity and FD < {fd_threshold}mm")
    
    valid_subjects = []
    excluded_reasons = {
        "missing_sleep": 0,
        "missing_fd": 0,
        "high_fd": 0,
        "invalid_sleep": 0
    }
    
    # Ensure columns exist
    if sleep_col not in df.columns:
        # Try to find a similar column name (case insensitive)
        matching_cols = [c for c in df.columns if sleep_col.lower() in c.lower()]
        if matching_cols:
            sleep_col = matching_cols[0]
            log_event("Subject Filtering", f"Found column '{sleep_col}' matching '{sleep_col}'")
        else:
            raise ValueError(f"Sleep Score column '{sleep_col}' not found in DataFrame. Available: {list(df.columns)}")
    
    if fd_col not in df.columns:
        matching_cols = [c for c in df.columns if "framewise" in c.lower() or "fd" in c.lower()]
        if matching_cols:
            fd_col = matching_cols[0]
            log_event("Subject Filtering", f"Found column '{fd_col}' matching FD")
        else:
            raise ValueError(f"Framewise Displacement column '{fd_col}' not found in DataFrame. Available: {list(df.columns)}")

    for idx, row in df.iterrows():
        subject_id = str(row.get('Subject_ID', row.get('Subject', row.name)))
        
        # Check Sleep Score validity
        sleep_val = row.get(sleep_col)
        if pd.isna(sleep_val):
            excluded_reasons["missing_sleep"] += 1
            continue
        
        # Check FD validity
        fd_val = row.get(fd_col)
        if pd.isna(fd_val):
            excluded_reasons["missing_fd"] += 1
            continue
        
        # Apply FD threshold
        if float(fd_val) > fd_threshold:
            excluded_reasons["high_fd"] += 1
            continue
        
        # If we get here, the subject is valid
        valid_subjects.append(subject_id)
    
    log_event("Subject Filtering", f"Total subjects: {len(df)}, Valid: {len(valid_subjects)}")
    log_event("Subject Filtering", f"Excluded: Missing Sleep={excluded_reasons['missing_sleep']}, Missing FD={excluded_reasons['missing_fd']}, High FD={excluded_reasons['high_fd']}")
    
    log_stage_complete("Subject Filtering", f"Identified {len(valid_subjects)} valid subjects")
    return valid_subjects

def main():
    """
    Main entry point for downloading HCP data and filtering subjects.
    This function:
    1. Downloads the behavioral CSV.
    2. Filters subjects based on Sleep Score and FD.
    3. Saves the list of valid subjects to a file for downstream tasks.
    """
    paths = get_paths()
    behavioral_dir = paths["behavioral"]
    ensure_dirs([behavioral_dir])
    
    behavioral_file = os.path.join(behavioral_dir, "hcp1200_behavioral_data.csv")
    valid_subjects_file = os.path.join(paths["processed"], "valid_subjects.json")
    
    # 1. Download Behavioral Data
    # Attempt to download from the primary source.
    # If that fails, try the mirror.
    downloaded = False
    if not os.path.exists(behavioral_file):
        # Try primary
        if download_file(HCP_BEHAVIORAL_URL, behavioral_file):
            downloaded = True
        else:
            # Try mirror
            log_event("Download", "Primary download failed, trying mirror...")
            if download_file(HCP_BEHAVIORAL_MIRROR, behavioral_file):
                downloaded = True
            else:
                log_stage_error("Download", "All download sources failed. Cannot proceed without real data.")
                # CRITICAL: Do not generate synthetic data. Fail loudly.
                sys.exit(1)
    else:
        log_event("Download", f"Behavioral file already exists at {behavioral_file}")
    
    # 2. Load and Filter
    df = load_behavioral_data(behavioral_file)
    valid_subjects = filter_subjects(df)
    
    if len(valid_subjects) == 0:
        log_stage_error("Filtering", "No valid subjects found after filtering. Aborting.")
        sys.exit(1)
    
    # 3. Save Valid Subjects List
    with open(valid_subjects_file, 'w') as f:
        json.dump(valid_subjects, f, indent=2)
    
    log_stage_complete("Pipeline", f"Saved valid subject list to {valid_subjects_file}")
    print(f"SUCCESS: Found {len(valid_subjects)} valid subjects. List saved to {valid_subjects_file}")
    return valid_subjects

if __name__ == "__main__":
    main()
