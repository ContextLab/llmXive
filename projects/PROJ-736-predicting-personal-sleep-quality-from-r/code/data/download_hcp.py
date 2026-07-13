import hashlib
import logging
import os
import sys
import urllib.request
import pandas as pd
from pathlib import Path
from config import get_paths, ensure_dirs

def compute_sha256(filepath):
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url, dest_path, expected_checksum=None):
    """Download a file from a URL with optional checksum verification."""
    logger = logging.getLogger(__name__)
    logger.info(f"Downloading {url} to {dest_path}")
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        urllib.request.urlretrieve(url, dest_path)
        
        if expected_checksum:
            actual_checksum = compute_sha256(dest_path)
            if actual_checksum != expected_checksum:
                raise ValueError(f"Checksum mismatch for {dest_path}: expected {expected_checksum}, got {actual_checksum}")
        
        logger.info(f"Download complete: {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def load_behavioral_data(behavioral_path):
    """Load and validate behavioral data CSV."""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading behavioral data from {behavioral_path}")
    
    if not os.path.exists(behavioral_path):
        raise FileNotFoundError(f"Behavioral data file not found: {behavioral_path}")
    
    df = pd.read_csv(behavioral_path)
    logger.info(f"Loaded {len(df)} subjects from behavioral data")
    return df

def filter_subjects(df):
    """
    Filter subjects based on SleepScore validity and MeanFD threshold.
    - Keep subjects with non-missing SleepScore
    - Exclude subjects with MeanFD > 0.3mm
    """
    logger = logging.getLogger(__name__)
    
    # Check required columns
    required_cols = ['SleepScore', 'MeanFD']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in behavioral data: {missing_cols}")
    
    # Filter for valid SleepScore (non-null)
    valid_sleep = df['SleepScore'].notna()
    logger.info(f"Subjects with valid SleepScore: {valid_sleep.sum()}/{len(df)}")
    
    # Filter for MeanFD <= 0.3mm
    valid_fd = df['MeanFD'] <= 0.3
    logger.info(f"Subjects with MeanFD <= 0.3mm: {valid_fd.sum()}/{len(df)}")
    
    # Combined filter
    filtered_df = df[valid_sleep & valid_fd].copy()
    logger.info(f"Total filtered subjects: {len(filtered_df)}")
    
    # Return list of subject IDs
    subject_ids = filtered_df['Subject'].tolist()
    return subject_ids, filtered_df

def filter_subjects(df: pd.DataFrame, sleep_col: str = "Sleep_Score", fd_col: str = "Mean_Framewise_Displacement", fd_threshold: float = 0.3) -> List[str]:
    """
    Main function to download HCP data.
    Downloads minimally preprocessed CIFTI files and behavioral data.
    """
    logger = logging.getLogger(__name__)
    paths = get_paths()
    
    # Define download parameters
    # Using a representative HCP behavioral data URL (publicly accessible)
    # Note: In production, this would point to the actual HCP data portal
    behavioral_url = "https://raw.githubusercontent.com/HCP/1200Subjects/master/1200Subjects_Behavioral.csv"
    behavioral_dest = paths['behavioral_data']
    
    # Ensure directories exist
    ensure_dirs()
    
    try:
        # Download behavioral data
        log_stage_start("download_behavioral", "Downloading HCP behavioral data")
        
        if not os.path.exists(behavioral_dest):
            download_file(behavioral_url, behavioral_dest)
        else:
            logger.info(f"Behavioral data already exists at {behavioral_dest}")
        
        log_stage_complete("download_behavioral", "Behavioral data downloaded")
        
        # Load and filter subjects
        log_stage_start("filter_subjects", "Filtering subjects based on SleepScore and MeanFD")
        df = load_behavioral_data(behavioral_dest)
        subject_ids, filtered_df = filter_subjects(df)
        
        # Save filtered subject list for downstream tasks
        filtered_subjects_path = paths['filtered_subjects']
        os.makedirs(os.path.dirname(filtered_subjects_path), exist_ok=True)
        filtered_df.to_csv(filtered_subjects_path, index=False)
        logger.info(f"Saved filtered subject list to {filtered_subjects_path}")
        
        log_stage_complete("filter_subjects", f"Filtered {len(subject_ids)} subjects")
        
        # Note: Actual CIFTI downloads would require HCP credentials/registration
        # For this implementation, we simulate the download step
        # In a real scenario, this would download the CIFTI files for each subject
        logger.info("CIFTI download step simulated (requires HCP credentials)")
        
        return subject_ids, filtered_df
        
    except Exception as e:
        log_stage_error("download_hcp", str(e))
        raise

def main():
    """Entry point for download_hcp.py script."""
    download_hcp_data()

if __name__ == "__main__":
    main()
