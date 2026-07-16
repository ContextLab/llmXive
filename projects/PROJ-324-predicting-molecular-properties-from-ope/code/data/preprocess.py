import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
import logging
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logging_utils import setup_logger

logger = setup_logger("preprocess")

# Constants
DATA_RAW_DIR = Path("data/raw")
DATA_DERIVED_DIR = Path("data/derived")
PREPROCESSED_FILE = DATA_DERIVED_DIR / "preprocessed_data.csv"
QUALITY_REPORT_FILE = DATA_DERIVED_DIR / "data_quality_report.csv"

# Thresholds
MIN_CONFIDENCE_SCORE = 0.7  # Example threshold for high confidence
MAX_MISSING_VALUE_RATIO = 0.1 # Max ratio of missing values allowed per column

def load_preprocessed_data(input_file: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the raw dataset. If input_file is None, attempts to find the latest raw data file.
    """
    if input_file is None:
        # Look for CSV or Parquet in data/raw
        candidates = list(DATA_RAW_DIR.glob("*.csv")) + list(DATA_RAW_DIR.glob("*.parquet"))
        if not candidates:
            raise FileNotFoundError(f"No raw data files found in {DATA_RAW_DIR}")
        # Sort by modification time, take latest
        input_file = max(candidates, key=lambda p: p.stat().st_mtime)
        logger.info(f"Loading raw data from {input_file}")
    else:
        logger.info(f"Loading raw data from {input_file}")

    if input_file.suffix == '.csv':
        df = pd.read_csv(input_file)
    elif input_file.suffix == '.parquet':
        df = pd.read_parquet(input_file)
    else:
        raise ValueError(f"Unsupported file format: {input_file.suffix}")

    return df

def filter_high_confidence(df: pd.DataFrame, confidence_col: str = "confidence_score") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter for high-confidence measurements.
    Returns (filtered_df, excluded_df)
    """
    if confidence_col not in df.columns:
        logger.warning(f"Column '{confidence_col}' not found. Skipping confidence filter.")
        return df, pd.DataFrame()

    # Assume confidence is numeric; if not, try to coerce or skip
    try:
        df[confidence_col] = pd.to_numeric(df[confidence_col], errors='coerce')
    except Exception as e:
        logger.warning(f"Could not convert {confidence_col} to numeric: {e}")
        return df, pd.DataFrame()

    filtered = df[df[confidence_col] >= MIN_CONFIDENCE_SCORE].copy()
    excluded = df[df[confidence_col] < MIN_CONFIDENCE_SCORE].copy()
    logger.info(f"Filtered {len(excluded)} low-confidence entries (threshold: {MIN_CONFIDENCE_SCORE})")
    return filtered, excluded

def handle_missing_values(df: pd.DataFrame, strategy: str = "drop") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Handle missing values.
    Strategy: 'drop' removes rows with any missing values in key columns (SMILES, target property).
    Returns (cleaned_df, excluded_df)
    """
    key_cols = ["smiles", "logP", "solubility", "boiling_point"]
    present_key_cols = [c for c in key_cols if c in df.columns]
    
    if not present_key_cols:
        logger.warning("No key columns (smiles, logP, etc.) found. Skipping missing value handling.")
        return df, pd.DataFrame()

    # Identify rows with missing values in key columns
    mask = df[present_key_cols].isnull().any(axis=1)
    cleaned = df[~mask].copy()
    excluded = df[mask].copy()

    logger.info(f"Dropped {len(excluded)} entries with missing values in {present_key_cols}")
    return cleaned, excluded

def detect_missing_covariates(df: pd.DataFrame, covariate_cols: Optional[List[str]] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect missing covariates (e.g., temperature, pH).
    If covariate_cols is None, tries to infer common names.
    Returns (filtered_df, excluded_df)
    """
    if covariate_cols is None:
        covariate_cols = ["temperature", "pH", "pressure"] # Common covariates
    
    present_covariates = [c for c in covariate_cols if c in df.columns]
    
    if not present_covariates:
        logger.info("No common covariate columns found. Skipping covariate check.")
        return df, pd.DataFrame()

    # Check for missing values in covariate columns
    mask = df[present_covariates].isnull().any(axis=1)
    filtered = df[~mask].copy()
    excluded = df[mask].copy()
    
    # Log specific missing covariates for the excluded rows
    if len(excluded) > 0:
        missing_info = excluded[present_covariates].isnull()
        # Create a string representation of missing covariates for each row
        excluded["missing_covariate"] = missing_info.apply(
            lambda row: ",".join(present_covariates[row]), axis=1
        )
        logger.info(f"Detected missing covariates in {len(excluded)} entries: {present_covariates}")
    else:
        excluded["missing_covariate"] = ""

    return filtered, excluded

def generate_quality_report(excluded_data: List[pd.DataFrame], reason_labels: List[str]) -> pd.DataFrame:
    """
    Combine excluded dataframes into a single quality report.
    reason_labels should match the order of excluded_data.
    """
    if not excluded_data:
        return pd.DataFrame()

    report_dfs = []
    for df, reason in zip(excluded_data, reason_labels):
        if df.empty:
            continue
        df_report = df.copy()
        df_report["exclusion_reason"] = reason
        # Ensure missing_covariate column exists if it was set by detect_missing_covariates
        if "missing_covariate" not in df_report.columns:
            df_report["missing_covariate"] = ""
        report_dfs.append(df_report)

    if not report_dfs:
        return pd.DataFrame()

    combined = pd.concat(report_dfs, ignore_index=True)
    
    # Reorder columns to put 'missing_covariate' and 'exclusion_reason' at the end
    cols = [c for c in combined.columns if c not in ["missing_covariate", "exclusion_reason"]]
    cols += ["missing_covariate", "exclusion_reason"]
    combined = combined[cols]

    return combined

def save_processed_data(df: pd.DataFrame, output_path: Optional[Path] = None):
    """
    Save the processed dataframe to CSV.
    """
    if output_path is None:
        output_path = PREPROCESSED_FILE
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path} ({len(df)} rows)")

def save_quality_report(df: pd.DataFrame, output_path: Optional[Path] = None):
    """
    Save the quality report to CSV.
    """
    if output_path is None:
        output_path = QUALITY_REPORT_FILE
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        # Create empty file with headers if no data
        df.to_csv(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    logger.info(f"Saved quality report to {output_path} ({len(df)} rows)")

def maxmin_sampling(df: pd.DataFrame, smiles_col: str = "smiles", target_size: int = 5000) -> pd.DataFrame:
    """
    Placeholder for MaxMin sampling. 
    T010/T011 will implement the actual diversity filtering logic.
    This function returns the input dataframe for now to allow T009 to complete.
    """
    logger.info("MaxMin sampling is a placeholder for T010/T011. Returning full dataset.")
    if len(df) <= target_size:
        return df
    # Simple random sample if implementation is deferred
    return df.sample(n=target_size, random_state=42)

def tanimoto_similarity(fp1: List[int], fp2: List[int]) -> float:
    """
    Placeholder for Tanimoto similarity calculation.
    """
    # Basic implementation for testing
    intersection = sum(a & b for a, b in zip(fp1, fp2))
    union = sum(a | b for a, b in zip(fp1, fp2))
    return intersection / union if union > 0 else 0.0

def main():
    """
    Main entry point for preprocessing pipeline.
    Executes: Load -> Filter Confidence -> Handle Missing -> Detect Covariates -> Report -> Save
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load Data
    try:
        raw_df = load_preprocessed_data()
        logger.info(f"Loaded {len(raw_df)} rows from raw data.")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    excluded_records = []
    reasons = []

    # 2. Filter High Confidence
    try:
        # Determine if confidence column exists, else skip
        if "confidence_score" in raw_df.columns:
            filtered_df, excluded_conf = filter_high_confidence(raw_df)
            if not excluded_conf.empty:
                excluded_records.append(excluded_conf)
                reasons.append("low_confidence")
        else:
            filtered_df = raw_df
            logger.warning("No confidence_score column found. Skipping confidence filter.")
    except Exception as e:
        logger.error(f"Error in confidence filtering: {e}")
        sys.exit(1)

    # 3. Handle Missing Values
    try:
        cleaned_df, excluded_missing = handle_missing_values(filtered_df)
        if not excluded_missing.empty:
            excluded_records.append(excluded_missing)
            reasons.append("missing_values")
    except Exception as e:
        logger.error(f"Error in missing value handling: {e}")
        sys.exit(1)

    # 4. Detect Missing Covariates
    try:
        final_df, excluded_cov = detect_missing_covariates(cleaned_df)
        if not excluded_cov.empty:
            excluded_records.append(excluded_cov)
            reasons.append("missing_covariates")
    except Exception as e:
        logger.error(f"Error in covariate detection: {e}")
        sys.exit(1)

    # 5. Generate Quality Report
    quality_report = generate_quality_report(excluded_records, reasons)
    save_quality_report(quality_report)

    # 6. Save Processed Data
    save_processed_data(final_df)

    logger.info("Preprocessing pipeline completed successfully.")
    logger.info(f"Final dataset size: {len(final_df)}")
    logger.info(f"Total excluded entries: {len(quality_report)}")

if __name__ == "__main__":
    main()
