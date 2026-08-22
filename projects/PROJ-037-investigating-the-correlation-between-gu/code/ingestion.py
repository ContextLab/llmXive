"""
ingestion.py
Data ingestion, merging, and cleaning pipeline.
"""

import os
import sys
import logging
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import get_logger
from utils.validators import validate_schema, validate_non_null, validate_merged_cohort
from utils.seeding import set_seed
from schemas import get_schema, get_required_columns

logger = get_logger(__name__)
set_seed(42)

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"

def download_file(url: str, dest_path: Path, checksum: str = None) -> Path:
    """
    Download a file from a URL.
    In a real implementation, this would use requests or wget.
    For this task, we assume data is already downloaded or raise an error.
    """
    if not dest_path.exists():
        logger.error(f"Data file not found at {dest_path}. Please download manually.")
        raise FileNotFoundError(f"Missing data file: {dest_path}")
    return dest_path

def parse_biom_table(biom_path: Path) -> pd.DataFrame:
    """
    Parse a BIOM format table into a pandas DataFrame.
    Requires biom-format library.
    """
    try:
        from biom import load_table
        table = load_table(str(biom_path))
        # Convert to observation x sample matrix, then transpose to sample x observation
        obs_ids = table.ids(axis='observation')
        sample_ids = table.ids(axis='sample')
        data = table.matrix_data.toarray()
        df = pd.DataFrame(data, index=sample_ids, columns=obs_ids)
        return df.reset_index().rename(columns={'index': 'sample_id'})
    except ImportError:
        logger.error("biom-format library not installed. Please install it via pip.")
        raise

def ingest_agp_metadata(metadata_path: Path) -> pd.DataFrame:
    """
    Ingest American Gut Project metadata.
    """
    if not metadata_path.exists():
        logger.error(f"AGP metadata not found at {metadata_path}")
        raise FileNotFoundError(f"Missing AGP metadata: {metadata_path}")
    
    df = pd.read_csv(metadata_path, sep='\t')
    logger.info(f"Loaded AGP metadata: {len(df)} rows")
    return df

def ingest_sleep_metadata(metadata_path: Path) -> pd.DataFrame:
    """
    Ingest Open Humans sleep metadata.
    """
    if not metadata_path.exists():
        logger.error(f"Sleep metadata not found at {metadata_path}")
        raise FileNotFoundError(f"Missing sleep metadata: {metadata_path}")
    
    df = pd.read_csv(metadata_path, sep='\t')
    logger.info(f"Loaded sleep metadata: {len(df)} rows")
    return df

def verify_integrity(agp_df: pd.DataFrame, sleep_df: pd.DataFrame) -> Tuple[int, int]:
    """
    Verify data integrity and return counts.
    """
    agp_ids = set(agp_df['Participant ID'].dropna().unique())
    sleep_ids = set(sleep_df['participant_id'].dropna().unique())
    
    intersection = agp_ids.intersection(sleep_ids)
    logger.info(f"Matching participants found: {len(intersection)}")
    return len(agp_ids), len(intersection)

def filter_missing_data(df: pd.DataFrame, required_cols: List[str]) -> pd.DataFrame:
    """
    Filter out rows with missing required data.
    """
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to missing required data.")
    return df

def cap_outliers(df: pd.DataFrame, col: str, lower_pct: float = 0.01, upper_pct: float = 0.99) -> pd.DataFrame:
    """
    Cap outliers at specified percentiles.
    """
    if col not in df.columns:
        return df
    
    lower = df[col].quantile(lower_pct)
    upper = df[col].quantile(upper_pct)
    
    mask = (df[col] < lower) | (df[col] > upper)
    if mask.sum() > 0:
        logger.warning(f"Capping {mask.sum()} outliers in column {col}")
    
    df.loc[df[col] < lower, col] = lower
    df.loc[df[col] > upper, col] = upper
    return df

def impute_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing covariates using median (numeric) or mode (categorical).
    """
    covariates = ['age', 'bmi', 'antibiotic_history']
    for col in covariates:
        if col not in df.columns:
            continue
        if df[col].dtype in ['int64', 'float64']:
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown')
    return df

def generate_summary_report(df: pd.DataFrame) -> str:
    """
    Generate a summary report of the merged cohort.
    """
    n = len(df)
    report = f"=== Cohort Summary Report ===\n"
    report += f"Total participants (N): {n}\n"
    
    if n < 200:
        report += f"\n⚠️ POWER LIMITATION WARNING: Sample size N={n} < 200 reduces ability to detect small effect sizes after adjustment.\n"
    
    report += "\n--- Covariate Distributions ---\n"
    for col in ['age', 'bmi', 'sleep_duration', 'sleep_quality', 'chronotype']:
        if col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                report += f"{col}: mean={df[col].mean():.2f}, std={df[col].std():.2f}, min={df[col].min():.2f}, max={df[col].max():.2f}\n"
            else:
                report += f"{col}: {df[col].value_counts().to_dict()}\n"
    
    if 'antibiotic_history' in df.columns:
        report += f"antibiotic_history: {df['antibiotic_history'].value_counts().to_dict()}\n"
    
    return report

def save_cohort(df: pd.DataFrame, output_path: Path):
    """
    Save the merged cohort to CSV.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Saved merged cohort to {output_path}")

def main():
    """
    Main ingestion pipeline.
    """
    try:
        # Define paths
        agp_biom = DATA_RAW_DIR / "agp_table.biom"
        agp_meta = DATA_RAW_DIR / "agp_metadata.tsv"
        sleep_meta = DATA_RAW_DIR / "sleep_metadata.tsv"
        output_path = DATA_PROCESSED_DIR / "cohort_merged.csv"
        
        # Ensure output directory exists
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        # Ingest data
        logger.info("Ingesting AGP metadata...")
        agp_df = ingest_agp_metadata(agp_meta)
        
        logger.info("Ingesting sleep metadata...")
        sleep_df = ingest_sleep_metadata(sleep_meta)

        # Verify integrity
        total_agp, matching = verify_integrity(agp_df, sleep_df)
        
        if matching == 0:
            logger.error("ERROR: No matching participants found. Cohort matching failed per Constitution Principle VI.")
            return 1
        
        if matching < 200:
            logger.warning(f"Power Limitation: N={matching} < 200. Proceeding with caution.")

        # Merge datasets
        logger.info("Merging datasets...")
        merged = pd.merge(
            agp_df,
            sleep_df,
            left_on='Participant ID',
            right_on='participant_id',
            how='inner'
        )

        # Verify 'diet type' presence
        if 'diet_type' not in merged.columns:
            logger.error("ERROR: 'diet_type' variable missing from Open Humans dataset. Manual intervention required.")
            return 1

        # Filter missing data
        required_cols = get_required_columns()
        merged = filter_missing_data(merged, required_cols)
        
        # Validate schema
        if not validate_merged_cohort(merged):
            logger.error("Schema validation failed.")
            return 1

        # Cap outliers
        merged = cap_outliers(merged, 'sleep_duration', 0.01, 0.99)

        # Impute covariates
        merged = impute_covariates(merged)

        # Generate summary report
        report = generate_summary_report(merged)
        logger.info("\n" + report)
        
        # Save cohort
        save_cohort(merged, output_path)

        return 0
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        return 1
