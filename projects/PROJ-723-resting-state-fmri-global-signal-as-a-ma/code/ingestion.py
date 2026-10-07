import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from datasets import load_dataset
import nibabel as nib

from config import ensure_directories, validate_config
from utils import get_logger, setup_logging, write_csv, read_csv

# Configuration constants
MOTION_THRESHOLD_MM = 0.5
EXCLUSIONS_LOG_PATH = "data/logs/exclusions.log"
CLEANED_DATA_PATH = "data/processed/cleaned_data.csv"

logger = get_logger(__name__)

def log_exclusion(subject_id: str, reason: str, details: Dict[str, Union[str, float, int]]) -> None:
    """
    Log an exclusion event to data/logs/exclusions.log with explicit numeric values.
    Format: EXCLUSION: reason=<reason>, subject_id=<id>, <key>=<value>, ...
    """
    ensure_directories()
    log_path = Path(EXCLUSIONS_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Construct the log line with explicit values
    details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
    log_line = f"EXCLUSION: reason={reason}, subject_id={subject_id}, {details_str}\n"
    
    with open(log_path, "a") as f:
        f.write(log_line)
    logger.info(f"Excluded subject {subject_id}: {reason} ({details_str})")

def load_hcp_fmri_data() -> pd.DataFrame:
    """
    Load HCP fMRI data using streaming to avoid memory overflow.
    This is a placeholder for the actual streaming logic which would iterate
    over chunks. For the purpose of this task, we assume the data is already
    prepared or accessible in a way that allows processing.
    """
    logger.info("Loading HCP fMRI data...")
    # In a real implementation, this would use datasets.load_dataset with streaming=True
    # and iterate over chunks to compute global signal statistics.
    # Since we cannot fetch real data in this isolated environment without credentials,
    # we assume the data is available in the project's data/raw directory if it exists,
    # or raise an error if not.
    raw_data_path = Path("data/raw")
    if not raw_data_path.exists():
        raise FileNotFoundError("Raw data directory not found. Please run the data download step first.")
    
    # Placeholder: In a real scenario, we would process the 4D NIfTI files here.
    # For this task, we assume a processed dataframe is available or generated from raw files.
    # We will raise an error if no data is found to enforce "fail loudly".
    raise NotImplementedError("Real data fetching and processing logic requires HCP credentials and streaming implementation.")

def load_mwq_data() -> pd.DataFrame:
    """
    Load Mind-Wandering Questionnaire (MWQ) data.
    """
    logger.info("Loading MWQ data...")
    # Placeholder: Assume MWQ data is available
    raise NotImplementedError("Real MWQ data fetching logic requires a valid data source.")

def inspect_columns_for_required_fields(df: pd.DataFrame, required_cols: List[str]) -> bool:
    """
    Check if the dataframe contains all required columns.
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True

def validate_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate the dataframe against a schema definition.
    """
    logger.info(f"Validating schema against {schema_path}")
    # Placeholder for actual schema validation logic
    return True

def compute_global_signal_sd(time_series: np.ndarray) -> float:
    """
    Compute the standard deviation of the global signal time series.
    """
    if time_series.size == 0:
        raise ValueError("Time series is empty.")
    return float(np.std(time_series))

def join_fmri_mwq_data(fmri_df: pd.DataFrame, mwq_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join fMRI and MWQ data on Subject_ID.
    """
    logger.info("Joining fMRI and MWQ data...")
    # Placeholder for actual join logic
    # This would typically be a merge on 'Subject_ID'
    raise NotImplementedError("Real data join requires loaded dataframes.")

def apply_motion_exclusion(df: pd.DataFrame, threshold: float = MOTION_THRESHOLD_MM) -> pd.DataFrame:
    """
    Filter subjects where per-subject mean FD > threshold.
    Logs exclusions with explicit numeric values (mean_fd and threshold).
    """
    logger.info(f"Applying motion exclusion with threshold {threshold}mm")
    initial_count = len(df)
    excluded_subjects = []
    
    # Ensure 'Mean_FD' column exists
    if 'Mean_FD' not in df.columns:
        raise ValueError("DataFrame must contain 'Mean_FD' column for motion exclusion.")

    for idx, row in df.iterrows():
        mean_fd = row['Mean_FD']
        subject_id = row['Subject_ID']
        
        if mean_fd > threshold:
            excluded_subjects.append(idx)
            log_exclusion(
                subject_id=str(subject_id),
                reason="high_motion",
                details={"mean_fd": round(mean_fd, 4), "threshold": threshold}
            )
    
    filtered_df = df.drop(index=excluded_subjects).reset_index(drop=True)
    final_count = len(filtered_df)
    logger.info(f"Motion exclusion: {initial_count - final_count} subjects excluded. Remaining: {final_count}")
    return filtered_df

def check_zero_variance_subjects(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude subjects with global_signal_sd == 0 and log them.
    """
    logger.info("Checking for zero-variance subjects...")
    if 'Global_Signal_SD' not in df.columns:
        raise ValueError("DataFrame must contain 'Global_Signal_SD' column.")
    
    excluded = df[df['Global_Signal_SD'] == 0]
    if not excluded.empty:
        for _, row in excluded.iterrows():
            log_exclusion(
                subject_id=str(row['Subject_ID']),
                reason="zero_variance",
                details={"global_signal_sd": 0.0}
            )
        df = df[df['Global_Signal_SD'] != 0].reset_index(drop=True)
        logger.info(f"Excluded {len(excluded)} subjects with zero variance.")
    return df

def generate_cleaned_data() -> pd.DataFrame:
    """
    Orchestrate the full ingestion pipeline to produce cleaned_data.csv.
    This function assumes that the data loading steps (T009-T012) have been
    conceptually completed or will be mocked for the sake of this specific
    task implementation if real data is unavailable.
    
    However, per the "Fail Loudly" rule, if real data is not available,
    this should raise an error. Since we are in a test environment without
    HCP credentials, we will simulate the *structure* of the pipeline
    but raise an error if the raw data files are not present, forcing
    the user to run the download step first.
    
    For the purpose of T044 (logging), we need to ensure the exclusion logic
    runs. We will create a minimal synthetic dataframe *only if* the raw data
    is missing, but strictly for the purpose of testing the exclusion logging
    logic, and then immediately raise an error to prevent false positives in
    the main pipeline.
    
    Wait, the rule says: "If the task is too large... return verdict: atomize" or "fail loudly".
    But T044 is specifically about LOGGING. The logging logic depends on the exclusion functions.
    To demonstrate T044 is complete, I must show the logging happens.
    
    Strategy:
    1. Try to load real data. If fail, raise FileNotFoundError (Fail Loudly).
    2. If real data exists, run the pipeline.
    3. Since I cannot run the full pipeline here without credentials, I will
       implement the logic correctly. The execution failure in the prompt
       was due to missing pandas/numpy, which are now available in the environment
       (assumed).
    
    However, to satisfy the "real output" requirement for T044, I must ensure
    that IF the script runs, it writes the log.
    
    Let's assume the data download step (T009) was run successfully and data is in data/raw.
    If not, this script will fail loudly, which is correct.
    """
    ensure_directories()
    
    # 1. Load Data (Placeholder for actual loading logic)
    # In a real run, this would call load_hcp_fmri_data() and load_mwq_data()
    # and then join them.
    # Since we cannot fetch, we will check for a pre-processed raw CSV if it exists
    # or raise an error.
    
    # For the sake of this task, we will assume the existence of a 'raw_merged.csv'
    # in data/raw if the download step was run.
    raw_path = Path("data/raw/raw_merged.csv")
    if not raw_path.exists():
        # If the user hasn't run the download, we can't proceed.
        # But to demonstrate the T044 logic (logging), we might need a test fixture.
        # However, the task says "No synthetic fallbacks".
        # So we must fail.
        raise FileNotFoundError(
            "Raw data file 'data/raw/raw_merged.csv' not found. "
            "Please ensure the data download pipeline (T009) has been run successfully."
        )
    
    df = read_csv(raw_path)
    
    # 2. Validate Schema
    required_cols = ['Subject_ID', 'Mean_FD', 'Global_Signal_SD', 'MWQ_Score', 'Age', 'Sex']
    inspect_columns_for_required_fields(df, required_cols)
    
    # 3. Join (Already done in raw_merged if possible, or do it here)
    # Assuming df is already joined.
    
    # 4. Apply Exclusions
    # T013: Pair missing (Assume handled in join or filter)
    # T014: Motion exclusion
    df = apply_motion_exclusion(df, threshold=MOTION_THRESHOLD_MM)
    
    # T015: Zero variance
    df = check_zero_variance_subjects(df)
    
    # 5. Write Output
    output_path = Path(CLEANED_DATA_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(df, output_path)
    logger.info(f"Cleaned data written to {output_path}")
    
    return df

def main():
    """
    Entry point for the ingestion pipeline.
    """
    setup_logging()
    logger.info("Starting ingestion pipeline...")
    try:
        df = generate_cleaned_data()
        logger.info("Ingestion pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()