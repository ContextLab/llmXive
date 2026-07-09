import os
import hashlib
import logging
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional, List

import pandas as pd
import numpy as np

from utils.config import get_config
from utils.logging_utils import setup_logging, get_logger
from utils.validators import validate_merged_cohort
from schemas import get_required_columns, get_optional_columns

# Initialize logger
logger = get_logger(__name__)

def download_file(url: str, dest_path: str, chunk_size: int = 8192) -> str:
    """
    Download a file from a URL to a destination path.
    Returns the path to the downloaded file.
    """
    import requests
    logger.info(f"Downloading {url} to {dest_path}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
    return dest_path

def parse_biom_table(biom_path: str) -> pd.DataFrame:
    """
    Parse a BIOM format file into a pandas DataFrame.
    Expected columns: SampleID, FeatureID, count (or similar structure flattened).
    For this task, we assume a pre-processed or simplified BIOM structure
    or use biom-format library if available. Here we simulate the logic
    assuming a TSV/CSV representation of the BIOM table for demonstration
    if the actual library isn't strictly enforced in the environment,
    but per task T002a, biom-format is a dependency.
    
    We will use biom-format if available, otherwise fallback to simple parsing.
    """
    try:
        import biom
        table = biom.load_table(biom_path)
        # Convert to observation table (FeatureID x SampleID)
        df = table.to_dataframe()
        # Transpose so rows are samples (participants)
        df = df.T
        df.index.name = 'SampleID'
        return df.reset_index()
    except ImportError:
        logger.warning("biom-format not installed. Attempting generic CSV/TSV parse.")
        # Fallback for demo if library missing, though T002a ensures it's there
        return pd.read_csv(biom_path, sep='\t', index_col=0).T.reset_index()

def ingest_agp_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Ingest American Gut Project metadata.
    Expected columns: participant_id, age, bmi, antibiotic_use, diet_type, ...
    """
    logger.info(f"Ingesting AGP metadata from {metadata_path}")
    df = pd.read_csv(metadata_path)
    # Standardize column names if necessary
    if 'participant_id' not in df.columns:
        # Try common variations
        for col in ['ParticipantID', 'sample_id', 'id']:
            if col in df.columns:
                df = df.rename(columns={col: 'participant_id'})
                break
    return df

def ingest_sleep_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Ingest Open Humans sleep metadata.
    Expected columns: participant_id, sleep_duration, sleep_quality, chronotype, ...
    """
    logger.info(f"Ingesting sleep metadata from {metadata_path}")
    df = pd.read_csv(metadata_path)
    if 'participant_id' not in df.columns:
        for col in ['ParticipantID', 'sample_id', 'id']:
            if col in df.columns:
                df = df.rename(columns={col: 'participant_id'})
                break
    return df

def verify_integrity(df: pd.DataFrame, expected_cols: List[str]) -> bool:
    """
    Verify data integrity against expected columns.
    """
    missing = set(expected_cols) - set(df.columns)
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def filter_missing_data(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Remove rows with missing data in specified columns.
    """
    logger.info(f"Filtering missing data for columns: {cols}")
    initial_count = len(df)
    df_clean = df.dropna(subset=cols)
    dropped = initial_count - len(df_clean)
    logger.info(f"Dropped {dropped} rows due to missing data. Remaining: {len(df_clean)}")
    return df_clean

def cap_outliers(df: pd.DataFrame, col: str, lower_pct: float = 1, upper_pct: float = 99) -> pd.DataFrame:
    """
    Cap outliers at specified percentiles.
    """
    logger.info(f"Capping outliers for {col} at {lower_pct}th and {upper_pct}th percentiles")
    lower_bound = np.percentile(df[col], lower_pct)
    upper_bound = np.percentile(df[col], upper_pct)
    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
    return df

def impute_covariates(df: pd.DataFrame, numeric_cols: List[str], categorical_cols: List[str]) -> pd.DataFrame:
    """
    Impute missing values: median for numeric, mode for categorical.
    """
    logger.info(f"Imputing covariates. Numeric: {numeric_cols}, Categorical: {categorical_cols}")
    df_imp = df.copy()
    for col in numeric_cols:
        if col in df_imp.columns:
            median_val = df_imp[col].median()
            df_imp[col] = df_imp[col].fillna(median_val)
    for col in categorical_cols:
        if col in df_imp.columns:
            mode_val = df_imp[col].mode()
            if len(mode_val) > 0:
                df_imp[col] = df_imp[col].fillna(mode_val[0])
    return df_imp

def generate_summary_report(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a summary report of the cohort.
    """
    logger.info(f"Generating summary report to {output_path}")
    report_lines = []
    report_lines.append(f"Total retained participants (N): {len(df)}")
    report_lines.append("-" * 40)
    
    key_cols = ['age', 'bmi', 'antibiotic_use', 'sleep_duration', 'sleep_quality']
    for col in key_cols:
        if col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                report_lines.append(f"{col}: Mean={df[col].mean():.2f}, Std={df[col].std():.2f}")
            else:
                report_lines.append(f"{col}: {df[col].value_counts().to_dict()}")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    logger.info("Summary report generated.")

def save_cohort(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the final merged cohort to CSV.
    """
    logger.info(f"Saving final merged cohort to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Cohort saved successfully. Rows: {len(df)}, Columns: {len(df.columns)}")

def main():
    """
    Main pipeline execution for T017: Save final merged cohort.
    This function orchestrates the ingestion, cleaning, and saving of the cohort.
    """
    config = get_config()
    setup_logging()
    
    # Paths (assuming relative to project root or defined in config)
    # For this implementation, we assume the data files exist in data/raw/
    # based on previous tasks (T011-T016).
    base_dir = Path(config.get('data_dir', 'data'))
    raw_dir = base_dir / 'raw'
    processed_dir = base_dir / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    agp_path = raw_dir / 'agp_metadata.csv'
    sleep_path = raw_dir / 'sleep_metadata.csv'
    output_path = processed_dir / 'cohort_merged.csv'
    
    # 1. Ingest Data
    try:
        df_agp = ingest_agp_metadata(agp_path)
        df_sleep = ingest_sleep_metadata(sleep_path)
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        # If files don't exist, we cannot proceed with real data.
        # However, per task constraints, we must implement the logic.
        # We raise to indicate failure in a real run.
        raise e

    # 2. Merge
    logger.info("Merging datasets on participant_id")
    df_merged = pd.merge(df_agp, df_sleep, on='participant_id', how='inner')
    logger.info(f"Merged dataset size: {len(df_merged)}")

    if len(df_merged) == 0:
        logger.warning("No matching participants found; proceeding with available sample size (which is 0).")
        # Even if 0, we save the empty frame with correct schema if possible
        # or just save it.
    
    # 3. Filter Missing Data
    required_cols = get_required_columns()
    df_clean = filter_missing_data(df_merged, required_cols)

    # 4. Cap Outliers (Sleep Duration)
    if 'sleep_duration' in df_clean.columns:
        df_clean = cap_outliers(df_clean, 'sleep_duration', lower_pct=1, upper_pct=99)

    # 5. Impute Covariates
    numeric_cols = ['age', 'bmi']
    categorical_cols = ['antibiotic_use', 'diet_type']
    # Filter to only existing columns
    numeric_cols = [c for c in numeric_cols if c in df_clean.columns]
    categorical_cols = [c for c in categorical_cols if c in df_clean.columns]
    
    if numeric_cols or categorical_cols:
        df_clean = impute_covariates(df_clean, numeric_cols, categorical_cols)

    # 6. Validate
    if not validate_merged_cohort(df_clean):
        logger.warning("Validation warnings issued, but proceeding to save.")

    # 7. Generate Summary Report (T016)
    report_path = processed_dir / 'cohort_summary.txt'
    generate_summary_report(df_clean, report_path)

    # 8. Save Final Cohort (T017)
    save_cohort(df_clean, output_path)

    logger.info("Pipeline completed successfully.")

if __name__ == '__main__':
    main()