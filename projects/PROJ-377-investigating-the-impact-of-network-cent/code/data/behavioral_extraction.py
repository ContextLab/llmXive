"""
Behavioral Metric Extraction Module

Implements T017: Extract behavioral metrics (pre/post motor scores, age, sex)
from the downloaded metadata CSV. Validates required columns, calculates
improvement scores, and logs excluded subjects.
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

# Import logging setup from existing utility
from utils.logging import setup_logger

# Configure logger
logger = setup_logger(__name__)

# Required columns as per T017 specification
REQUIRED_COLUMNS = [
    'subject_id',
    'pre_motor_score',
    'post_motor_score',
    'age',
    'sex'
]

def load_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Load the metadata CSV file.

    Args:
        metadata_path: Path to the metadata CSV file.

    Returns:
        DataFrame containing the metadata.

    Raises:
        FileNotFoundError: If the file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    logger.info(f"Loading metadata from {metadata_path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from metadata")
    return df

def extract_behavioral_metrics(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract and validate behavioral metrics.

    Verifies the presence of required columns.
    Calculates improvement_score = post_motor_score - pre_motor_score.
    Filters out rows with missing critical data.
    Logs excluded subjects to a separate DataFrame.

    Args:
        df: Input DataFrame from metadata.

    Returns:
        Tuple of (valid_data_df, exclusion_log_df).
        valid_data_df contains columns: subject_id, pre_motor_score, post_motor_score,
            age, sex, improvement_score.
        exclusion_log_df contains columns: subject_id, exclusion_reason.

    Raises:
        ValueError: If required columns are missing.
    """
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        error_msg = f"Fatal: Metadata lacks required columns: {missing_cols}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("All required columns present in metadata.")

    # Create a copy to avoid modifying the original
    data = df[REQUIRED_COLUMNS].copy()

    # Calculate improvement score
    data['improvement_score'] = data['post_motor_score'] - data['pre_motor_score']

    # Identify exclusions
    # Exclusion criteria: Missing values in any of the required columns
    # or non-numeric values where numeric is expected
    exclusion_reasons = []
    valid_indices = []

    for idx, row in data.iterrows():
        reason = None
        # Check for NaN in required fields
        if row.isnull().any():
            missing_fields = [col for col in REQUIRED_COLUMNS if pd.isna(row[col])]
            reason = f"Missing values in: {', '.join(missing_fields)}"
        elif not isinstance(row['age'], (int, float)) or pd.isna(row['age']):
            reason = "Invalid age value"
        elif not isinstance(row['pre_motor_score'], (int, float)) or pd.isna(row['pre_motor_score']):
            reason = "Invalid pre_motor_score value"
        elif not isinstance(row['post_motor_score'], (int, float)) or pd.isna(row['post_motor_score']):
            reason = "Invalid post_motor_score value"
        elif not isinstance(row['sex'], (str, int, float)) or pd.isna(row['sex']):
            reason = "Invalid sex value"

        if reason:
            exclusion_reasons.append({'subject_id': row['subject_id'], 'exclusion_reason': reason})
        else:
            valid_indices.append(idx)

    # Log exclusions
    if exclusion_reasons:
        exclusion_log_df = pd.DataFrame(exclusion_reasons)
        logger.warning(f"Excluding {len(exclusion_reasons)} subjects due to invalid data.")
        for _, row in exclusion_log_df.iterrows():
            logger.info(f"Excluded subject {row['subject_id']}: {row['exclusion_reason']}")
    else:
        exclusion_log_df = pd.DataFrame(columns=['subject_id', 'exclusion_reason'])

    # Filter valid data
    valid_data = data.loc[valid_indices].reset_index(drop=True)

    # Ensure correct data types
    valid_data['subject_id'] = valid_data['subject_id'].astype(str)
    valid_data['age'] = pd.to_numeric(valid_data['age'], errors='coerce')
    valid_data['pre_motor_score'] = pd.to_numeric(valid_data['pre_motor_score'], errors='coerce')
    valid_data['post_motor_score'] = pd.to_numeric(valid_data['post_motor_score'], errors='coerce')
    valid_data['improvement_score'] = pd.to_numeric(valid_data['improvement_score'], errors='coerce')
    # Convert sex to string if it's numeric (e.g., 0/1)
    if valid_data['sex'].dtype in ['int64', 'float64']:
        valid_data['sex'] = valid_data['sex'].astype(str)

    return valid_data, exclusion_log_df

def save_behavioral_metrics(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the processed behavioral metrics to CSV.

    Args:
        df: DataFrame with subject scores.
        output_path: Path to save the CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved behavioral metrics to {output_path}")

def save_exclusion_log(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the exclusion log to CSV.

    Args:
        df: DataFrame with exclusion reasons.
        output_path: Path to save the CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved exclusion log to {output_path}")

def run_behavioral_extraction(metadata_path: str, output_path: str, exclusion_log_path: str) -> None:
    """
    Main entry point for behavioral metric extraction.

    1. Loads metadata.
    2. Validates columns.
    3. Extracts metrics and calculates improvement.
    4. Saves valid data and exclusion log.

    Args:
        metadata_path: Path to input metadata CSV.
        output_path: Path to save subject_scores.csv.
        exclusion_log_path: Path to save exclusion_log.csv.
    """
    try:
        df = load_metadata(metadata_path)
        valid_data, exclusion_log = extract_behavioral_metrics(df)

        save_behavioral_metrics(valid_data, output_path)
        save_exclusion_log(exclusion_log, exclusion_log_path)

        logger.info(f"Extraction complete. Valid subjects: {len(valid_data)}, Excluded: {len(exclusion_log)}")

    except ValueError as e:
        # Re-raise validation errors to stop the pipeline
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}")
        raise e

def main():
    """
    CLI entry point for T017.
    """
    # Paths based on project structure
    metadata_path = "data/raw/metadata.csv"
    output_path = "data/processed/behavioral/subject_scores.csv"
    exclusion_log_path = "data/processed/logs/exclusion_log.csv"

    run_behavioral_extraction(metadata_path, output_path, exclusion_log_path)

if __name__ == "__main__":
    main()