"""
Ingestion and processing module for fMRI and MWQ data.
Implements data loading, schema validation, global signal computation,
subject joining, motion exclusion, zero-variance filtering, and final CSV generation.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
import yaml

# Ensure imports from config and utils are available if needed, 
# but we rely on the API surface provided.
# We assume standard libraries and pandas/numpy are available.

logger = logging.getLogger(__name__)

# Constants
REQUIRED_COLUMNS = [
    "Subject_ID", 
    "global_signal", 
    "global_signal_sd", 
    "MWQ_Score", 
    "Age", 
    "Sex", 
    "Mean_FD", 
    "Mean_DVARS"
]

def load_hcp_fmri_data():
    """
    Loads HCP fMRI data.
    In a real execution, this would fetch from datasets.load_dataset or a local path.
    For this implementation, we assume the data is available in a standard format 
    or we simulate the structure based on the 'real data' constraint by 
    attempting to load from a known path or raising an error if not found.
    
    Since we cannot fabricate data, this function must fail loudly if real data 
    is not present. In a real pipeline, T009 would have downloaded this.
    We expect a parquet or csv file in data/raw/ if T009 succeeded.
    """
    # Attempt to find a pre-processed raw file if T009 ran
    candidates = [
        "data/raw/hcp_fmri_data.parquet",
        "data/raw/hcp_fmri_data.csv",
        "data/raw/hcp_resting_state.csv"
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            logger.info(f"Loading fMRI data from {candidate}")
            if candidate.endswith('.parquet'):
                return pd.read_parquet(candidate)
            else:
                return pd.read_csv(candidate)
    
    # If not found, we cannot proceed without real data.
    # We do NOT generate synthetic data.
    raise FileNotFoundError(
        "FATAL: Real fMRI data not found. "
        "Ensure T009 (load_hcp_fmri_data) has successfully downloaded data to data/raw/."
    )

def load_mwq_data():
    """
    Loads MWQ (Mind-Wandering Questionnaire) data.
    Similar to load_hcp_fmri_data, expects real data from T009.
    """
    candidates = [
        "data/raw/mwq_scores.parquet",
        "data/raw/mwq_scores.csv",
        "data/raw/hcp_mwq_data.csv"
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            logger.info(f"Loading MWQ data from {candidate}")
            if candidate.endswith('.parquet'):
                return pd.read_parquet(candidate)
            else:
                return pd.read_csv(candidate)
    
    raise FileNotFoundError(
        "FATAL: Real MWQ data not found. "
        "Ensure T009 has successfully downloaded data to data/raw/."
    )

def validate_schema(data: pd.DataFrame, schema_path: str = "contracts/dataset.schema.yaml") -> bool:
    """
    Validates the dataframe against the schema defined in contracts/dataset.schema.yaml.
    Halts with FATAL error if required columns are missing.
    """
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file {schema_path} not found. Skipping validation.")
        return True

    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_fields = schema.get('required_columns', [])
    
    missing = [col for col in required_fields if col not in data.columns]
    if missing:
        logger.error(f"FATAL: Dataset Mismatch - Required columns not found: {missing}")
        sys.exit(1)
    
    logger.info("Schema validation passed.")
    return True

def compute_global_signal_mean_time_series(data: pd.DataFrame) -> pd.DataFrame:
    """
    Computes voxel-wise mean time series (global signal) per run.
    Assumes data has time series columns or a way to compute this.
    For this implementation, we assume the input data already has 'global_signal'
    or we compute it from raw time series if present.
    
    Given the constraints of T009-T011, we assume the data loaded has the necessary
    columns or we are working with the output of those steps.
    """
    # Placeholder for logic if raw time series were passed.
    # Here we assume 'global_signal' column exists or is computed.
    if 'global_signal' not in data.columns:
        # If we have raw time series, we would compute mean here.
        # For now, we rely on the data being pre-processed by T011.
        logger.warning("global_signal column missing. Assuming T011 computed it or data is raw.")
        # In a real scenario, we'd calculate mean across voxel columns.
        # Since we can't fake data, we assume the column exists or fail.
        raise ValueError("global_signal column missing from input data.")
    
    return data

def compute_global_signal_sd_per_run(data: pd.DataFrame) -> pd.DataFrame:
    """
    Computes standard deviation of global signal per run.
    """
    if 'global_signal' in data.columns:
        # Group by run if multiple runs exist, otherwise just one SD per subject/run row
        # Assuming data is at run-level granularity here
        data['global_signal_sd'] = data.groupby('Subject_ID')['global_signal'].transform('std')
    elif 'global_signal_sd' in data.columns:
        # Already computed
        pass
    else:
        raise ValueError("Cannot compute SD: missing global_signal or global_signal_sd.")
    return data

def compute_subject_average_global_signal_sd(data: pd.DataFrame) -> pd.DataFrame:
    """
    Averages global signal SD across runs per subject.
    """
    if 'global_signal_sd' not in data.columns:
        raise ValueError("global_signal_sd column missing.")
    
    # Aggregate by Subject_ID
    subject_stats = data.groupby('Subject_ID')['global_signal_sd'].mean().reset_index()
    subject_stats.rename(columns={'global_signal_sd': 'Global_Signal_SD'}, inplace=True)
    return subject_stats

def join_fmri_mwq_data(fmri_data: pd.DataFrame, mwq_data: pd.DataFrame) -> pd.DataFrame:
    """
    Joins fMRI and MWQ data. Excludes unmatched pairs.
    """
    # Standardize column names for join if necessary
    # Assuming both have 'Subject_ID'
    if 'Subject_ID' not in fmri_data.columns or 'Subject_ID' not in mwq_data.columns:
        raise ValueError("Subject_ID missing in one of the datasets.")
    
    merged = pd.merge(fmri_data, mwq_data, on='Subject_ID', how='inner')
    
    dropped_count = len(fmri_data) + len(mwq_data) - len(merged)
    logger.info(f"Joined data. Dropped {dropped_count} unmatched pairs.")
    
    return merged

def apply_motion_exclusion(data: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """
    Filters subjects where per-subject mean FD > 0.5mm.
    Logs exclusion counts and IDs.
    """
    if 'Mean_FD' not in data.columns:
        raise ValueError("Mean_FD column missing.")
    
    # Ensure Mean_FD is numeric
    data['Mean_FD'] = pd.to_numeric(data['Mean_FD'], errors='coerce')
    
    excluded = data[data['Mean_FD'] > threshold]
    included = data[data['Mean_FD'] <= threshold]
    
    if not excluded.empty:
        logger.warning(f"Motion Exclusion: Excluding {len(excluded)} subjects with Mean_FD > {threshold}mm.")
        logger.warning(f"Excluded Subject IDs: {list(excluded['Subject_ID'])}")
    else:
        logger.info("Motion Exclusion: No subjects excluded.")
        
    return included

def check_zero_variance_subjects(data: pd.DataFrame) -> pd.DataFrame:
    """
    Excludes subjects with global_signal_sd == 0.
    Logs exclusion count.
    """
    if 'Global_Signal_SD' not in data.columns:
        # Try to find the column if named differently
        candidates = [c for c in data.columns if 'sd' in c.lower() and 'global' in c.lower()]
        if candidates:
            col = candidates[0]
        else:
            raise ValueError("global_signal_sd column missing.")
    else:
        col = 'Global_Signal_SD'
    
    zero_var = data[data[col] == 0]
    included = data[data[col] != 0]
    
    if not zero_var.empty:
        logger.warning(f"Zero Variance Check: Excluding {len(zero_var)} subjects with {col} == 0.")
        logger.warning(f"Excluded Subject IDs: {list(zero_var['Subject_ID'])}")
    else:
        logger.info("Zero Variance Check: No subjects excluded.")
        
    return included

def generate_cleaned_data() -> pd.DataFrame:
    """
    Orchestrates the full pipeline to generate cleaned_data.csv.
    Steps:
    1. Load FMRI and MWQ data.
    2. Validate schema.
    3. Compute/Verify Global Signal SD.
    4. Join data.
    5. Apply motion exclusion.
    6. Apply zero-variance check.
    7. Select and rename columns for final output.
    """
    logger.info("Starting generate_cleaned_data pipeline.")
    
    # 1. Load Data
    fmri_raw = load_hcp_fmri_data()
    mwq_raw = load_mwq_data()
    
    # 2. Validate Schema (T010)
    validate_schema(fmri_raw)
    validate_schema(mwq_raw)
    
    # 3. Compute Global Signal SD (T011, T012)
    # Assuming raw data has global_signal per run
    fmri_processed = compute_global_signal_mean_time_series(fmri_raw)
    fmri_processed = compute_global_signal_sd_per_run(fmri_processed)
    fmri_agg = compute_subject_average_global_signal_sd(fmri_processed)
    
    # 4. Join Data (T013)
    # We need to merge the aggregated FMRI stats with MWQ data
    # Ensure MWQ data has the required columns
    merged_data = join_fmri_mwq_data(fmri_agg, mwq_raw)
    
    # 5. Motion Exclusion (T014)
    merged_data = apply_motion_exclusion(merged_data)
    
    # 6. Zero Variance Check (T015)
    merged_data = check_zero_variance_subjects(merged_data)
    
    # 7. Final Formatting (T016)
    required_output_cols = [
        "Subject_ID", "Global_Signal_SD", "MWQ_Score", "Age", "Sex", "Mean_FD", "Mean_DVARS"
    ]
    
    # Ensure all required columns exist
    missing_cols = [c for c in required_output_cols if c not in merged_data.columns]
    if missing_cols:
        # Try to map common aliases if any, otherwise fail
        raise ValueError(f"Missing required columns for output: {missing_cols}")
    
    final_df = merged_data[required_output_cols].copy()
    
    # Ensure types are correct
    final_df['Subject_ID'] = final_df['Subject_ID'].astype(str)
    final_df['Global_Signal_SD'] = pd.to_numeric(final_df['Global_Signal_SD'], errors='coerce')
    final_df['MWQ_Score'] = pd.to_numeric(final_df['MWQ_Score'], errors='coerce')
    final_df['Age'] = pd.to_numeric(final_df['Age'], errors='coerce')
    final_df['Mean_FD'] = pd.to_numeric(final_df['Mean_FD'], errors='coerce')
    final_df['Mean_DVARS'] = pd.to_numeric(final_df['Mean_DVARS'], errors='coerce')
    
    # Drop rows with any NaNs in required columns (Data Hygiene)
    initial_len = len(final_df)
    final_df = final_df.dropna(subset=required_output_cols)
    if len(final_df) < initial_len:
        logger.warning(f"Dropped {initial_len - len(final_df)} rows due to missing values.")
    
    logger.info(f"Final cleaned data generated with {len(final_df)} subjects.")
    return final_df

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        df = generate_cleaned_data()
        output_path = Path("data/processed/cleaned_data.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Cleaned data saved to {output_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
