"""
Data Ingestion Module for Gut Microbiome and Circadian Rhythm Study.

This module handles the download, parsing, merging, and cleaning of data from
the American Gut Project (AGP) and Open Humans sleep metadata.
"""
import os
import sys
import logging
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

# Import local utilities
from utils.logging_utils import get_logger
from utils.validators import validate_merged_cohort
from utils.seeding import set_seed
from schemas import get_required_columns

# Configure logging
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def download_file(url: str, dest_path: Path, expected_checksum: Optional[str] = None) -> None:
    """
    Download a file from a URL with optional checksum verification.

    Args:
        url: The URL to download from.
        dest_path: The local path to save the file.
        expected_checksum: Optional MD5 checksum to verify the download.
    """
    import requests
    logger.info(f"Downloading {url} to {dest_path}")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    if expected_checksum:
        with open(dest_path, 'rb') as f:
            actual_checksum = hashlib.md5(f.read()).hexdigest()
        if actual_checksum != expected_checksum:
            raise ValueError(f"Checksum mismatch for {dest_path}. Expected {expected_checksum}, got {actual_checksum}")
    logger.info(f"Download complete: {dest_path}")

def parse_biom_table(biom_path: Path) -> pd.DataFrame:
    """
    Parse a BIOM table into a pandas DataFrame.

    Args:
        biom_path: Path to the BIOM file.

    Returns:
        DataFrame with samples as rows and features as columns.
    """
    import biom
    logger.info(f"Loading BIOM table from {biom_path}")
    table = biom.load_table(str(biom_path))
    df = table.to_dataframe()
    # Transpose so samples are rows
    df = df.T
    logger.info(f"Loaded BIOM table with {df.shape[0]} samples and {df.shape[1]} features")
    return df

def ingest_agp_metadata(agp_data_path: Path) -> pd.DataFrame:
    """
    Ingest metadata from the American Gut Project.

    Args:
        agp_data_path: Path to the AGP metadata file.

    Returns:
        DataFrame with AGP metadata.
    """
    logger.info(f"Ingesting AGP metadata from {agp_data_path}")
    # Assuming the data is already downloaded and processed into a CSV for this pipeline
    # In a real scenario, this might parse the raw BIOM or TSV
    if not agp_data_path.exists():
        raise FileNotFoundError(f"AGP data file not found: {agp_data_path}")
    
    df = pd.read_csv(agp_data_path)
    # Standardize column names if necessary
    if 'sample-id' in df.columns:
        df = df.rename(columns={'sample-id': 'participant_id'})
    return df

def ingest_sleep_metadata(sleep_data_path: Path) -> pd.DataFrame:
    """
    Ingest metadata from Open Humans sleep study.

    Args:
        sleep_data_path: Path to the sleep metadata file.

    Returns:
        DataFrame with sleep metadata.
    """
    logger.info(f"Ingesting sleep metadata from {sleep_data_path}")
    if not sleep_data_path.exists():
        raise FileNotFoundError(f"Sleep data file not found: {sleep_data_path}")
    
    df = pd.read_csv(sleep_data_path)
    # Standardize column names
    if 'participant_id' not in df.columns and 'Study ID' in df.columns:
        df = df.rename(columns={'Study ID': 'participant_id'})
    return df

def verify_integrity(agp_df: pd.DataFrame, sleep_df: pd.DataFrame) -> None:
    """
    Verify the integrity of the ingested data.

    Args:
        agp_df: AGP metadata DataFrame.
        sleep_df: Sleep metadata DataFrame.
    """
    logger.info("Verifying data integrity...")
    if agp_df.empty:
        raise ValueError("AGP metadata is empty.")
    if sleep_df.empty:
        raise ValueError("Sleep metadata is empty.")
    logger.info(f"AGP samples: {len(agp_df)}, Sleep samples: {len(sleep_df)}")

def filter_missing_data(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Filter out rows with missing data in specified columns.

    Args:
        df: Input DataFrame.
        columns: List of column names to check for missing values.

    Returns:
        Filtered DataFrame.
    """
    logger.info(f"Filtering missing data in columns: {columns}")
    initial_count = len(df)
    df = df.dropna(subset=columns)
    final_count = len(df)
    logger.info(f"Dropped {initial_count - final_count} rows due to missing data")
    return df

def cap_outliers(df: pd.DataFrame, column: str, lower_percentile: float = 1, upper_percentile: float = 99) -> pd.DataFrame:
    """
    Cap outliers in a column at specified percentiles.

    Args:
        df: Input DataFrame.
        column: Column name to cap.
        lower_percentile: Lower percentile threshold.
        upper_percentile: Upper percentile threshold.

    Returns:
        DataFrame with capped values.
    """
    logger.info(f"Capping outliers in {column} at {lower_percentile}th and {upper_percentile}th percentiles")
    if column not in df.columns:
        logger.warning(f"Column {column} not found in DataFrame, skipping capping.")
        return df

    lower_bound = df[column].quantile(lower_percentile / 100)
    upper_bound = df[column].quantile(upper_percentile / 100)
    
    df[column] = df[column].clip(lower=lower_bound, upper=upper_bound)
    logger.info(f"Capped {column} to range [{lower_bound}, {upper_bound}]")
    return df

def impute_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing covariate values using median (for numeric) or mode (for categorical).

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with imputed values.
    """
    logger.info("Imputing covariates...")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns

    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.info(f"Imputed {col} with median {median_val}")

    for col in categorical_cols:
        if df[col].isnull().any():
            mode_val = df[col].mode()[0]
            df[col] = df[col].fillna(mode_val)
            logger.info(f"Imputed {col} with mode {mode_val}")

    return df

def generate_summary_report(df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate a summary report of the merged cohort.

    Args:
        df: The merged DataFrame.
        output_path: Path to save the report.
    """
    logger.info(f"Generating summary report to {output_path}")
    report_lines = [
        "=== Merged Cohort Summary Report ===",
        f"Total Retained Participants (N): {len(df)}",
        "",
        "Distribution of Key Covariates:",
        f"Age - Mean: {df['age'].mean():.2f}, Std: {df['age'].std():.2f}",
        f"BMI - Mean: {df['bmi'].mean():.2f}, Std: {df['bmi'].std():.2f}",
        f"Antibiotic History - Yes: {df['antibiotic_history'].value_counts().get('Yes', 0)}, No: {df['antibiotic_history'].value_counts().get('No', 0)}",
        ""
    ]

    # Check for power limitation
    if len(df) < 200:
        report_lines.append("⚠️ POWER LIMITATION WARNING: Sample size N < 200 reduces ability to detect small effect sizes after adjustment.")
    
    report_content = "\n".join(report_lines)
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info("Summary report generated.")
    print(report_content)

def save_cohort(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the final merged cohort to a CSV file.

    Args:
        df: The merged DataFrame.
        output_path: Path to save the CSV.
    """
    logger.info(f"Saving merged cohort to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Cohort saved successfully to {output_path}")

def main():
    """
    Main function to orchestrate the data ingestion pipeline.
    """
    set_seed(42)
    logger.info("Starting data ingestion pipeline...")

    # Paths
    # Note: In a real execution, these paths would be populated by T011 (download)
    # For this task, we assume the data files exist in data/raw as per T011 completion
    agp_raw_path = RAW_DIR / "agp_metadata.csv"
    sleep_raw_path = RAW_DIR / "sleep_metadata.csv"
    merged_output_path = PROCESSED_DIR / "cohort_merged.csv"
    report_output_path = PROCESSED_DIR / "cohort_summary.txt"

    # Check if source files exist (simulating T011 completion)
    if not agp_raw_path.exists():
        # In a real scenario, this would trigger the download logic from T011
        # For this task, we assume T011 has run and created these files.
        # If they don't exist, we cannot proceed without real data.
        raise FileNotFoundError(f"AGP raw data not found at {agp_raw_path}. Ensure T011 has completed.")
    if not sleep_raw_path.exists():
        raise FileNotFoundError(f"Sleep raw data not found at {sleep_raw_path}. Ensure T011 has completed.")

    # Ingest
    agp_df = ingest_agp_metadata(agp_raw_path)
    sleep_df = ingest_sleep_metadata(sleep_raw_path)

    # Verify
    verify_integrity(agp_df, sleep_df)

    # Merge
    # Assuming 'participant_id' is the key in both
    logger.info("Merging datasets on participant_id...")
    merged_df = pd.merge(agp_df, sleep_df, on='participant_id', how='inner')

    if merged_df.empty:
        logger.error("ERROR: No matching participants found. Cohort matching failed per Constitution Principle VI.")
        sys.exit(1)

    n_matches = len(merged_df)
    logger.info(f"Merged cohort size: {n_matches}")

    if 0 < n_matches < 200:
        logger.warning(f"Power Limitation Warning: N={n_matches} < 200. Proceeding with caution.")

    # Filter missing data
    required_cols = ['participant_id', 'shannon', 'simpson', 'sleep_duration', 'sleep_quality', 'chronotype', 'age', 'bmi', 'diet_type', 'antibiotic_history']
    # Filter only columns that exist in the merged df to avoid KeyError if schema varies slightly
    existing_required = [c for c in required_cols if c in merged_df.columns]
    merged_df = filter_missing_data(merged_df, existing_required)

    if merged_df.empty:
        logger.error("ERROR: All rows filtered out due to missing required data.")
        sys.exit(1)

    # Cap outliers (sleep duration)
    if 'sleep_duration' in merged_df.columns:
        merged_df = cap_outliers(merged_df, 'sleep_duration', 1, 99)

    # Impute covariates
    merged_df = impute_covariates(merged_df)

    # Validate
    validate_merged_cohort(merged_df)

    # Generate Summary Report
    generate_summary_report(merged_df, report_output_path)

    # Save Final Cohort
    save_cohort(merged_df, merged_output_path)

    logger.info("Data ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()
