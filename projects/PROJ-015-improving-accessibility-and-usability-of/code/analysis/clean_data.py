"""
T021c: Orchestrate the cleaning pipeline.

Implements CLI to load raw session data, filter incomplete sessions,
impute SUS scores, coerce types, and write a checksummed CSV.

Dependencies: T021a (filter_incomplete), T021b (impute_sus).
"""
import argparse
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Optional

import pandas as pd

# Import existing API surface
from analysis.data_cleaner import DataCleaner
from utils.logger import get_logger
from utils.checksum import compute_file_checksum

logger = get_logger(__name__)

def load_raw_sessions(input_dir: str) -> pd.DataFrame:
    """
    Load all JSON session files from input_dir into a DataFrame.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    json_files = list(input_path.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {input_dir}")
    
    records = []
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure file path is included for audit if needed, 
                # though the schema defines the content.
                records.append(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {file_path}: {e}")
            # Per T021-exclude, we only exclude based on status='incomplete'.
            # Malformed files are excluded by not adding to records.
            continue
    
    if not records:
        raise ValueError("No valid session records found in input directory.")
    
    return pd.DataFrame(records)

def filter_incomplete(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    T021a Logic: Filter out sessions where status == 'incomplete'.
    Returns (filtered_df, excluded_count).
    """
    initial_count = len(df)
    # Filter out rows where status == 'incomplete'
    df_filtered = df[df['status'] != 'incomplete'].copy()
    excluded_count = initial_count - len(df_filtered)
    return df_filtered, excluded_count

def impute_sus(df: pd.DataFrame) -> pd.DataFrame:
    """
    T021b Logic: Impute SUS scores.
    Uses DataCleaner.impute_sus which handles the logic:
    If <=1 item missing, impute with participant mean; if >1, mark incomplete.
    Since we are working with aggregated scores here, we assume the DataCleaner
    handles the granular item logic if raw items exist, or just validates the score.
    For this orchestration, we call the cleaner's method.
    """
    cleaner = DataCleaner()
    return cleaner.impute_sus(df)

def main():
    parser = argparse.ArgumentParser(description="Clean session data pipeline.")
    parser.add_argument(
        "--input", 
        type=str, 
        required=True, 
        help="Path to directory containing raw JSON session files (data/raw/)."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        required=True, 
        help="Path to output CSV file (data/processed/cleaned_sessions.csv)."
    )
    args = parser.parse_args()

    logger.info(f"Starting data cleaning pipeline. Input: {args.input}, Output: {args.output}")

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load Raw Data
    try:
        df_raw = load_raw_sessions(args.input)
        logger.info(f"Loaded {len(df_raw)} sessions.")
    except Exception as e:
        logger.critical(f"Failed to load raw data: {e}")
        sys.exit(1)

    # 2. Filter Incomplete Sessions (T021a logic)
    df_filtered, excluded_count = filter_incomplete(df_raw)
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} incomplete sessions.")
        # Verify dropout_reason for excluded sessions (audit)
        excluded_df = df_raw[df_raw['status'] == 'incomplete']
        if 'dropout_reason' in excluded_df.columns:
            reasons = excluded_df['dropout_reason'].dropna().unique().tolist()
            logger.debug(f"Dropout reasons found: {reasons}")
            # Log to a specific file for audit as per T021c requirement
            audit_log_path = output_path.parent / "dropout_audit_log.txt"
            with open(audit_log_path, 'w', encoding='utf-8') as f:
                f.write(f"Excluded Count: {excluded_count}\n")
                f.write(f"Dropout Reasons: {reasons}\n")
                logger.info(f"Wrote dropout audit log to {audit_log_path}")
        else:
            logger.warning("No 'dropout_reason' column found in incomplete sessions.")
    else:
        logger.info("No incomplete sessions found.")

    # 3. Impute SUS Scores (T021b logic)
    df_clean = impute_sus(df_filtered)
    
    # 4. Type Coercion
    # Ensure types match the analysis requirements
    # Columns: participant_id (str), interface_type (str), completion_time_seconds (float),
    # error_count (int), sus_score (float/int), explanation_engagement_time_seconds (float)
    if 'participant_id' in df_clean.columns:
        df_clean['participant_id'] = df_clean['participant_id'].astype(str)
    if 'interface_type' in df_clean.columns:
        df_clean['interface_type'] = df_clean['interface_type'].astype(str)
    if 'completion_time_seconds' in df_clean.columns:
        df_clean['completion_time_seconds'] = pd.to_numeric(df_clean['completion_time_seconds'], errors='coerce')
    if 'error_count' in df_clean.columns:
        df_clean['error_count'] = pd.to_numeric(df_clean['error_count'], errors='coerce').astype('Int64')
    if 'sus_score' in df_clean.columns:
        df_clean['sus_score'] = pd.to_numeric(df_clean['sus_score'], errors='coerce')
    if 'explanation_engagement_time_seconds' in df_clean.columns:
        df_clean['explanation_engagement_time_seconds'] = pd.to_numeric(df_clean['explanation_engagement_time_seconds'], errors='coerce')

    # Drop rows with NaN in critical columns if any occurred during coercion
    # (DataCleaner should have handled SUS, but coercion might fail on bad data)
    critical_cols = ['participant_id', 'interface_type', 'completion_time_seconds', 'error_count', 'sus_score']
    existing_critical = [c for c in critical_cols if c in df_clean.columns]
    df_clean = df_clean.dropna(subset=existing_critical)

    logger.info(f"Final cleaned dataset size: {len(df_clean)} rows.")

    # 5. Write Output
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Wrote cleaned data to {output_path}")

    # 6. Checksum (Constitution Principle III)
    checksum = compute_file_checksum(output_path)
    checksum_file = output_path.with_suffix(output_path.suffix + '.sha256')
    with open(checksum_file, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {output_path.name}\n")
    logger.info(f"Checksum written to {checksum_file}: {checksum}")

    logger.info("Data cleaning pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())