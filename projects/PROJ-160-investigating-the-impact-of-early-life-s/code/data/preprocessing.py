"""
Data Preprocessing Module for User Story 1.

Implements:
- T015: Filter missing ACE and poor MRI quality
- T016: Normalize volumes by ICV
- T017: Log-transform ACE if skewed
- T018: Flag extreme outliers
- T019: Orchestrate full pipeline for final dataset generation
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import logging
import json

logger = logging.getLogger(__name__)

# Column names constants (matching ABCD study conventions)
COL_ACE = 'ace_score' # Assuming 'ace_score' or similar. We will try to detect.
COL_AGE = 'age'
COL_SEX = 'sex'
COL_SITE = 'scanner_site'
COL_FAMILY_ID = 'family_id'
COL_ICV = 'icv'

# Subfield volumes
COL_CA3 = 'ca3_volume'
COL_DG = 'dg_volume'
COL_SUBICULUM = 'subiculum_volume'

def detect_mri_qc_column(df: pd.DataFrame) -> Optional[str]:
    """Detect the column representing MRI quality flags."""
    possible_names = ['mri_qc', 'quality_flag', 'mri_quality', 'qc_flag']
    for name in possible_names:
        if name in df.columns:
            return name
    # Fallback: search for columns containing 'qc' or 'quality'
    for col in df.columns:
        if 'qc' in col.lower() or 'quality' in col.lower():
            return col
    return None

def filter_missing_ace(df: pd.DataFrame, ace_col: str = 'ace_score') -> pd.DataFrame:
    """
    T015: Exclude participants with missing ACE scores.
    """
    if ace_col not in df.columns:
        # Try to find a column with 'ace' in the name
        matches = [c for c in df.columns if 'ace' in c.lower()]
        if matches:
            ace_col = matches[0]
            logger.info(f"Using detected ACE column: {ace_col}")
        else:
            raise ValueError("No ACE score column found in dataset.")
    
    initial_count = len(df)
    df = df.dropna(subset=[ace_col])
    df = df[df[ace_col].notna() & (df[ace_col] != '')]
    
    # Ensure numeric
    df[ace_col] = pd.to_numeric(df[ace_col], errors='coerce')
    df = df.dropna(subset=[ace_col])
    
    final_count = len(df)
    logger.info(f"Filtered missing ACE scores. Dropped {initial_count - final_count} rows.")
    return df, ace_col

def filter_poor_mri_quality(df: pd.DataFrame) -> pd.DataFrame:
    """
    T015: Exclude participants with poor MRI quality flags.
    Assuming 'good' quality is 1 or 'pass', and 'poor' is 0 or 'fail'.
    We keep rows where quality is good/missing (if missing is treated as good in some contexts)
    or specifically filter out known bad flags.
    """
    qc_col = detect_mri_qc_column(df)
    if not qc_col:
        logger.warning("No MRI QC column found. Skipping MRI quality filter.")
        return df
    
    initial_count = len(df)
    
    # Logic: Assume 1 = good, 0 = bad, or 'pass'/'fail'.
    # We will keep rows where the flag is NOT 'fail' or 0.
    # If the column is numeric: keep > 0 or == 1.
    # If string: keep != 'fail' and != 'poor'.
    
    if pd.api.types.is_numeric_dtype(df[qc_col]):
        # Keep if value is 1 (or > 0.5)
        mask = df[qc_col] > 0.5
    else:
        # String logic
        bad_values = ['fail', 'poor', 'bad', '0']
        mask = ~df[qc_col].astype(str).str.lower().isin(bad_values)
    
    df = df[mask]
    final_count = len(df)
    logger.info(f"Filtered poor MRI quality. Dropped {initial_count - final_count} rows.")
    return df

def normalize_volumes_by_icv(df: pd.DataFrame, icv_col: str = 'icv', 
                             subfields: List[str] = ['ca3_volume', 'dg_volume', 'subiculum_volume']) -> pd.DataFrame:
    """
    T016: Normalize CA3, DG, subiculum volumes by dividing by ICV.
    Stores with >= 4 decimal precision.
    """
    # Ensure ICV is numeric and non-zero
    if icv_col not in df.columns:
        # Try to detect
        matches = [c for c in df.columns if 'icv' in c.lower()]
        if matches:
            icv_col = matches[0]
        else:
            raise ValueError("ICV column not found.")
    
    df[icv_col] = pd.to_numeric(df[icv_col], errors='coerce')
    df = df[df[icv_col] > 0] # Avoid division by zero
    
    normalized_cols = []
    for sub in subfields:
        if sub in df.columns:
            norm_col = f"{sub}_normalized"
            df[norm_col] = df[sub] / df[icv_col]
            df[norm_col] = df[norm_col].round(6) # Store with high precision
            normalized_cols.append(norm_col)
            logger.info(f"Normalized {sub} -> {norm_col}")
        else:
            # Try to detect
            matches = [c for c in df.columns if sub.replace('_volume', '').lower() in c.lower()]
            if matches:
                src_col = matches[0]
                norm_col = f"{src_col}_normalized"
                df[norm_col] = df[src_col] / df[icv_col]
                df[norm_col] = df[norm_col].round(6)
                normalized_cols.append(norm_col)
                logger.info(f"Normalized {src_col} -> {norm_col}")
            else:
                logger.warning(f"Subfield volume column {sub} not found. Skipping.")
    
    return df

def apply_log_transformation_if_skewed(df: pd.DataFrame, ace_col: str = 'ace_score', threshold: float = 1.0) -> pd.DataFrame:
    """
    T017: Check ACE score skewness. Apply log-transformation if |skewness| > 1.0.
    """
    if ace_col not in df.columns:
        matches = [c for c in df.columns if 'ace' in c.lower()]
        if matches:
            ace_col = matches[0]
        else:
            return df # No ACE column to transform
    
    skewness = df[ace_col].skew()
    logger.info(f"ACE score skewness: {skewness:.4f}")
    
    if abs(skewness) > threshold:
        logger.info(f"Skewness ({skewness:.4f}) exceeds threshold ({threshold}). Applying log transformation.")
        # Add small constant if values are 0 or negative to avoid log(0)
        min_val = df[ace_col].min()
        if min_val <= 0:
            offset = abs(min_val) + 1
            df[ace_col] = df[ace_col] + offset
            logger.info(f"Added offset {offset} to ACE scores for log transformation.")
        
        df[ace_col] = np.log(df[ace_col])
        df[ace_col] = df[ace_col].round(6)
    else:
        logger.info("Skewness within acceptable range. No log transformation applied.")
    
    return df

def flag_extreme_outliers(df: pd.DataFrame, ace_col: str = 'ace_score', sd_threshold: float = 3.0) -> pd.DataFrame:
    """
    T018: Flag extreme ACE outliers (> 3 SD) for sensitivity analysis.
    Appends a flag column 'ace_outlier_flag'.
    """
    if ace_col not in df.columns:
        matches = [c for c in df.columns if 'ace' in c.lower()]
        if matches:
            ace_col = matches[0]
        else:
            return df
    
    mean_val = df[ace_col].mean()
    std_val = df[ace_col].std()
    
    if std_val == 0:
        logger.warning("Standard deviation is 0. Cannot flag outliers.")
        df['ace_outlier_flag'] = False
        return df
    
    lower_bound = mean_val - sd_threshold * std_val
    upper_bound = mean_val + sd_threshold * std_val
    
    df['ace_outlier_flag'] = (df[ace_col] < lower_bound) | (df[ace_col] > upper_bound)
    
    outlier_count = df['ace_outlier_flag'].sum()
    logger.info(f"Flagged {outlier_count} extreme ACE outliers (> {sd_threshold} SD).")
    
    return df

def preprocess_for_us1(raw_dir: Path) -> pd.DataFrame:
    """
    Orchestrates the full US1 preprocessing pipeline.
    1. Load raw data (phenotypic + segmentation).
    2. Filter missing ACE.
    3. Filter poor MRI quality.
    4. Normalize volumes.
    5. Log-transform ACE if needed.
    6. Flag outliers.
    """
    # 1. Load Data
    # We assume the raw directory contains specific files.
    # Since we don't have the exact filenames from the prompt, we try common patterns.
    # The acquisition module should have placed them here.
    
    phenotypic_file = None
    segmentation_file = None
    
    # Try to find files
    files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.tsv"))
    logger.info(f"Found {len(files)} files in raw directory.")
    
    # Heuristic: Identify files
    for f in files:
        name = f.name.lower()
        if 'phenotype' in name or 'phenotypic' in name or 'study' in name:
            phenotypic_file = f
        elif 'segment' in name or 'subcortical' in name or 'volume' in name:
            segmentation_file = f
    
    if not phenotypic_file:
        # Fallback: use the first file if only one exists
        if len(files) >= 1:
            phenotypic_file = files[0]
            logger.warning(f"Using {phenotypic_file} as phenotypic data.")
        else:
            raise FileNotFoundError("No phenotypic data file found in raw directory.")
    
    if not segmentation_file and len(files) > 1:
        # Use the other file
        segmentation_file = [f for f in files if f != phenotypic_file][0]
        logger.warning(f"Using {segmentation_file} as segmentation data.")
    elif not segmentation_file:
        # Maybe all data is in one file?
        segmentation_file = phenotypic_file
        logger.warning("No separate segmentation file found. Using phenotypic file for all data.")
    
    # Load
    df_pheno = pd.read_csv(phenotypic_file)
    df_seg = pd.read_csv(segmentation_file)
    
    # Merge on subject ID (assuming 'subjectkey' or 'participant_id')
    # We need a common key. ABCD usually uses 'subjectkey'.
    key_col = None
    for col in ['subjectkey', 'participant_id', 'subject_id', 'npi']:
        if col in df_pheno.columns and col in df_seg.columns:
            key_col = col
            break
    
    if not key_col:
        # Try to find a common column
        common = set(df_pheno.columns) & set(df_seg.columns)
        if common:
            key_col = list(common)[0]
            logger.warning(f"Using detected key column: {key_col}")
        else:
            raise ValueError("Cannot find a common key column to merge phenotypic and segmentation data.")
    
    logger.info(f"Merging on key: {key_col}")
    df = pd.merge(df_pheno, df_seg, on=key_col, how='inner')
    logger.info(f"Merged dataset shape: {df.shape}")
    
    # 2. Filter Missing ACE
    df, ace_col = filter_missing_ace(df)
    
    # 3. Filter Poor MRI Quality
    df = filter_poor_mri_quality(df)
    
    # 4. Normalize Volumes
    df = normalize_volumes_by_icv(df)
    
    # 5. Log Transform ACE
    df = apply_log_transformation_if_skewed(df, ace_col)
    
    # 6. Flag Outliers
    df = flag_extreme_outliers(df, ace_col)
    
    return df

def main():
    """Entry point for standalone execution."""
    from code.config_env import get_raw_dir
    raw_dir = get_raw_dir()
    df = preprocess_for_us1(raw_dir)
    print(f"Preprocessing complete. Rows: {len(df)}")
    print(df.head())

if __name__ == "__main__":
    main()
