import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import json
import numpy as np
import nibabel as nib
import pandas as pd
import logging

from utils import get_logger, read_csv, write_csv, validate_required_keys
from config import ensure_directories

def load_hcp_fmri_data(raw_dir: Path) -> pd.DataFrame:
    """
    Load HCP fMRI metrics (Subject_ID, Global_Signal_SD, Mean_FD, Mean_DVARS)
    from the raw data directory.
    
    This function assumes T009 has downloaded the data and T011/T012 have
    computed the metrics, storing them in a CSV or Parquet file in data/raw/.
    We look for a file matching the pattern 'hcp_fmri_metrics.*'.
    """
    logger = get_logger("ingestion")
    raw_dir = Path(raw_dir)
    
    # Look for the computed metrics file
    candidates = list(raw_dir.glob("hcp_fmri_metrics.*"))
    if not candidates:
        # Fallback: check if there's a specific parquet/zip processed file
        # If T009 downloaded raw zips, we might need to unzip first, but T012
        # implies we already have the SD computed. Let's assume a CSV/Parquet exists
        # from the previous steps or a standard HCP release structure.
        # For robustness, we check for common extensions.
        candidates = list(raw_dir.glob("*metrics*"))
        candidates += list(raw_dir.glob("*global_signal*"))
    
    if not candidates:
        raise FileNotFoundError(
            f"FATAL: No fMRI metrics file found in {raw_dir}. "
            "Ensure T009 (download) and T011/T012 (computation) have run successfully."
        )
    
    # Prefer the first found file
    metrics_file = candidates[0]
    logger.info(f"Loading fMRI metrics from {metrics_file}")
    
    if metrics_file.suffix in ['.csv']:
        df = pd.read_csv(metrics_file)
    elif metrics_file.suffix in ['.parquet', '.pq']:
        df = pd.read_parquet(metrics_file)
    else:
        # Try reading as CSV as default
        try:
            df = pd.read_csv(metrics_file)
        except Exception:
            raise ValueError(f"Unsupported file format for {metrics_file}")
    
    # Ensure Subject_ID is string to match MWQ data
    if 'Subject_ID' in df.columns:
        df['Subject_ID'] = df['Subject_ID'].astype(str)
    
    return df

def load_mwq_data(raw_dir: Path) -> pd.DataFrame:
    """
    Load MWQ (Mind-Wandering Questionnaire) scores and demographics from raw data.
    
    Expects a file like 'hcp_mwq_scores.csv' or similar in data/raw/.
    """
    logger = get_logger("ingestion")
    raw_dir = Path(raw_dir)
    
    candidates = list(raw_dir.glob("*mwq*"))
    candidates += list(raw_dir.glob("*questionnaire*"))
    candidates += list(raw_dir.glob("*survey*"))
    
    if not candidates:
        raise FileNotFoundError(
            f"FATAL: No MWQ data file found in {raw_dir}. "
            "Ensure T009 (download) has successfully retrieved the questionnaire data."
        )
    
    mwq_file = candidates[0]
    logger.info(f"Loading MWQ data from {mwq_file}")
    
    if mwq_file.suffix in ['.csv']:
        df = pd.read_csv(mwq_file)
    elif mwq_file.suffix in ['.parquet', '.pq']:
        df = pd.read_parquet(mwq_file)
    else:
        try:
            df = pd.read_csv(mwq_file)
        except Exception:
            raise ValueError(f"Unsupported file format for {mwq_file}")
    
    # Normalize column names for joining
    # Expected: Subject_ID (or sub_id), MWQ_Score, Age, Sex
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    
    if 'subject_id' in df.columns:
        df['subject_id'] = df['subject_id'].astype(str)
    
    return df

def join_fmri_mwq_data(
    fmri_df: pd.DataFrame,
    mwq_df: pd.DataFrame,
    logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Join fMRI metrics and MWQ data on Subject_ID.
    
    Excludes unmatched pairs (inner join).
    Logs the counts of excluded subjects.
    
    Args:
        fmri_df: DataFrame with fMRI metrics (Subject_ID, Global_Signal_SD, etc.)
        mwq_df: DataFrame with MWQ scores (subject_id, MWQ_Score, Age, Sex)
        logger: Optional logger instance.
    
    Returns:
        Joined DataFrame with both fMRI and MWQ data.
    """
    if logger is None:
        logger = get_logger("ingestion")
    
    # Normalize key names for join
    # fmri_df has 'Subject_ID' (mixed case from HCP usually)
    # mwq_df has 'subject_id' (normalized above)
    fmri_key = 'Subject_ID'
    mwq_key = 'subject_id'
    
    if fmri_key not in fmri_df.columns:
        # Try case-insensitive lookup
        matches = [c for c in fmri_df.columns if c.lower() == 'subject_id']
        if matches:
            fmri_key = matches[0]
        else:
            raise KeyError(f"Subject ID column not found in fMRI data: {fmri_df.columns.tolist()}")
    
    if mwq_key not in mwq_df.columns:
        matches = [c for c in mwq_df.columns if c.lower() == 'subject_id']
        if matches:
            mwq_key = matches[0]
        else:
            raise KeyError(f"Subject ID column not found in MWQ data: {mwq_df.columns.tolist()}")
    
    logger.info(f"Joining on '{fmri_key}' (fMRI) and '{mwq_key}' (MWQ)")
    
    total_fmri = len(fmri_df)
    total_mwq = len(mwq_df)
    
    # Perform inner join to keep only matched pairs
    joined = pd.merge(
        fmri_df,
        mwq_df,
        left_on=fmri_key,
        right_on=mwq_key,
        how='inner'
    )
    
    matched_count = len(joined)
    excluded_fmri = total_fmri - matched_count
    excluded_mwq = total_mwq - matched_count
    
    logger.info(f"Subject Validation Results:")
    logger.info(f"  Total fMRI subjects: {total_fmri}")
    logger.info(f"  Total MWQ subjects: {total_mwq}")
    logger.info(f"  Matched pairs: {matched_count}")
    logger.info(f"  Excluded (fMRI only): {excluded_fmri}")
    logger.info(f"  Excluded (MWQ only): {excluded_mwq}")
    
    if matched_count == 0:
        raise ValueError("FATAL: No subjects matched between fMRI and MWQ datasets. "
                       "Check Subject_ID formatting and data sources.")
    
    # Drop the duplicate key column if it exists (usually the right one)
    if mwq_key in joined.columns and mwq_key != fmri_key:
        joined = joined.drop(columns=[mwq_key])
    
    # Rename the key column to a standard name if needed
    if fmri_key != 'Subject_ID':
        joined = joined.rename(columns={fmri_key: 'Subject_ID'})
    
    return joined

def validate_subject_data(joined_df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """
    Perform basic validation on the joined data (FR-009).
    - Check for missing values in critical columns.
    - Log warnings for any missing data found.
    """
    if logger is None:
        logger = get_logger("ingestion")
    
    critical_cols = ['Subject_ID', 'Global_Signal_SD', 'MWQ_Score', 'Age', 'Sex']
    
    # Ensure columns exist
    missing_cols = [c for c in critical_cols if c not in joined_df.columns]
    if missing_cols:
        raise ValueError(f"Missing critical columns after join: {missing_cols}")
    
    # Check for missing values
    missing_counts = joined_df[critical_cols].isnull().sum()
    total_missing = missing_counts.sum()
    
    if total_missing > 0:
        logger.warning(f"Found {total_missing} missing values in critical columns:")
        for col, count in missing_counts.items():
            if count > 0:
                logger.warning(f"  {col}: {count} missing")
        # For FR-009, we log the counts. The actual exclusion might be handled in T014/T015
        # or we drop them here if strictly required. The task says "excluding unmatched pairs"
        # which we did in the join. It doesn't explicitly say drop rows with NaNs, but
        # standard practice is to drop or impute. We will drop rows with NaN in critical cols.
        initial_count = len(joined_df)
        joined_df = joined_df.dropna(subset=critical_cols)
        dropped_count = initial_count - len(joined_df)
        logger.info(f"Dropped {dropped_count} subjects due to missing critical data.")
    
    return joined_df

def process_subject_validation(raw_dir: str, output_dir: str) -> pd.DataFrame:
    """
    Main entry point for T013: Subject Validation.
    1. Load fMRI data (from T011/T012 outputs).
    2. Load MWQ data.
    3. Join and exclude unmatched pairs.
    4. Validate and log counts.
    5. Return the validated DataFrame.
    """
    logger = get_logger("ingestion")
    raw_path = Path(raw_dir)
    output_path = Path(output_dir)
    
    ensure_directories([output_path])
    
    logger.info("Starting Subject Validation (T013)...")
    
    # Load data
    fmri_df = load_hcp_fmri_data(raw_path)
    mwq_df = load_mwq_data(raw_path)
    
    # Join
    joined_df = join_fmri_mwq_data(fmri_df, mwq_df, logger)
    
    # Validate
    validated_df = validate_subject_data(joined_df, logger)
    
    logger.info(f"Subject validation complete. {len(validated_df)} subjects ready for next stage.")
    
    return validated_df

# Helper functions from previous tasks (T007, T008, T011, T012)
# These are stubs or placeholders if not fully implemented in the user's context,
# but the API surface requires them to exist.

def prepare_bids_structure(subject_id: str, bids_root: str) -> Path:
    """Generate BIDS directory structure for a subject."""
    bids_path = Path(bids_root) / f"sub-{subject_id}" / "func"
    bids_path.mkdir(parents=True, exist_ok=True)
    return bids_path

def generate_bids_filename(subject_id: str, task: str = "rest", run: int = 1) -> str:
    """Generate a BIDS-compliant filename."""
    return f"sub-{subject_id}_task-{task}_run-{run:02d}_bold.nii.gz"

def create_empty_bids_files(bids_path: Path) -> None:
    """Create placeholder BIDS files if needed."""
    pass

def compute_global_signal_mean_time_series(nifti_path: str) -> np.ndarray:
    """Compute mean time series across all voxels."""
    img = nib.load(nifti_path)
    data = img.get_fdata()
    if data.ndim == 4:
        return data.mean(axis=(0, 1, 2))
    elif data.ndim == 3:
        return data.mean()
    raise ValueError("Expected 4D NIfTI file")

def compute_global_signal_sd_per_run(nifti_path: str) -> float:
    """Compute standard deviation of the global signal for a run."""
    ts = compute_global_signal_mean_time_series(nifti_path)
    return float(np.std(ts))

def compute_subject_average_global_signal_sd(sd_values: List[float]) -> float:
    """Average SD across runs for a subject."""
    return float(np.mean(sd_values))
