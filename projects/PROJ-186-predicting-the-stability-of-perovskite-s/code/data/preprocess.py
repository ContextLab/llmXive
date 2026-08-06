"""
Preprocessing module for perovskite stability data.

This module handles:
- Loading raw data from downloaded JSON sources
- Cleaning data (handling missing values, filtering invalid entries)
- Validating against schema
- Splitting data into train/test sets
- Saving processed features to CSV
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import json
import numpy as np

# Import from local utils
from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event
from utils.config import get_config_summary

logger = get_logger(__name__)

# Required columns for the final features dataset
REQUIRED_COLUMNS = [
    'material_id', 'formula', 'space_group', 'elements', 
    'a_site', 'b_site', 'x_site',
    'tolerance_factor', 'octahedral_factor', 'ionic_radius_mismatch',
    'electronegativity_difference', 'decomposition_energy'
]

# Columns that must have zero nulls
CRITICAL_COLUMNS = ['decomposition_energy', 'tolerance_factor', 'octahedral_factor']

def load_raw_data(data_dir: str = "data/raw") -> pd.DataFrame:
    """
    Load raw data from downloaded JSON files.
    
    Args:
        data_dir: Directory containing raw JSON files from download scripts
        
    Returns:
        Combined DataFrame with all raw entries
        
    Raises:
        FileNotFoundError: If no raw data files are found
        ValueError: If data files are malformed
    """
    raw_dir = Path(data_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {raw_dir}")
    
    all_data = []
    for json_file in json_files:
        logger.info(f"Loading raw data from: {json_file}")
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                elif isinstance(data, dict) and 'entries' in data:
                    all_data.extend(data['entries'])
                else:
                    logger.warning(f"Unexpected data structure in {json_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file {json_file}: {e}")
            raise
    
    if not all_data:
        raise ValueError("No valid data entries found in any JSON files")
    
    df = pd.DataFrame(all_data)
    log_pipeline_event(f"Loaded {len(df)} raw entries from {len(json_files)} files")
    return df

def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Clean data by handling missing values and filtering invalid entries.
    
    Args:
        df: Raw DataFrame with perovskite data
        
    Returns:
        Tuple of (cleaned DataFrame, count of excluded entries)
    """
    excluded_count = 0
    original_count = len(df)
    
    # Filter out entries with missing critical fields
    critical_fields = ['formula', 'space_group', 'decomposition_energy']
    for field in critical_fields:
        if field in df.columns:
            null_mask = df[field].isna()
            if null_mask.any():
                count = null_mask.sum()
                logger.warning(f"Removing {count} entries with missing '{field}'")
                log_exclusion_reason(f"Missing {field}", count)
                df = df[~null_mask]
                excluded_count += count
    
    # Filter out entries with missing descriptor columns (added by descriptors.py)
    descriptor_cols = ['tolerance_factor', 'octahedral_factor', 'ionic_radius_mismatch', 
                     'electronegativity_difference']
    for col in descriptor_cols:
        if col in df.columns:
            null_mask = df[col].isna()
            if null_mask.any():
                count = null_mask.sum()
                logger.warning(f"Removing {count} entries with missing descriptor: {col}")
                log_exclusion_reason(f"Missing descriptor {col}", count)
                df = df[~null_mask]
                excluded_count += count
    
    # Ensure decomposition_energy is numeric and filter extreme outliers
    if 'decomposition_energy' in df.columns:
        df['decomposition_energy'] = pd.to_numeric(df['decomposition_energy'], errors='coerce')
        # Filter entries with decomposition_energy > 1.0 eV/atom (clearly unstable)
        # This is a heuristic based on perovskite stability literature
        extreme_mask = df['decomposition_energy'] > 1.0
        if extreme_mask.any():
            count = extreme_mask.sum()
            logger.warning(f"Removing {count} entries with extreme decomposition energy (>1.0 eV/atom)")
            log_exclusion_reason("Extreme decomposition energy", count)
            df = df[~extreme_mask]
            excluded_count += count
        
        # Filter negative tolerance factors (physically impossible)
        if 'tolerance_factor' in df.columns:
            invalid_t_mask = (df['tolerance_factor'] <= 0) | (df['tolerance_factor'] > 2.0)
            if invalid_t_mask.any():
                count = invalid_t_mask.sum()
                logger.warning(f"Removing {count} entries with invalid tolerance factor")
                log_exclusion_reason("Invalid tolerance factor", count)
                df = df[~invalid_t_mask]
                excluded_count += count
    
    # Ensure we have the required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}")
        # Add missing columns with NaN (will be filtered out in validation)
        for col in missing_cols:
            df[col] = np.nan
    
    log_pipeline_event(f"Cleaned data: {original_count} -> {len(df)} entries (excluded {excluded_count})")
    return df, excluded_count

def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validate DataFrame against expected schema.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if schema is valid, False otherwise
    """
    # Check required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check for nulls in critical columns
    for col in CRITICAL_COLUMNS:
        if df[col].isna().any():
            logger.error(f"Critical column '{col}' contains null values")
            return False
    
    # Check data types
    if 'space_group' in df.columns:
        if not pd.api.types.is_integer_dtype(df['space_group']):
            logger.warning("space_group should be integer type")
    
    if 'decomposition_energy' in df.columns:
        if not pd.api.types.is_float_dtype(df['decomposition_energy']):
            logger.warning("decomposition_energy should be float type")
    
    logger.info("Schema validation passed")
    return True

def split_data(df: pd.DataFrame, 
              test_size: float = 0.2,
              random_state: int = 42,
              stratify_column: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into training and test sets.
    
    Args:
        df: Input DataFrame
        test_size: Proportion of data to use for testing
        random_state: Random seed for reproducibility
        stratify_column: Column to use for stratified sampling (optional)
        
    Returns:
        Tuple of (train_df, test_df)
    """
    from sklearn.model_selection import train_test_split
    
    logger.info(f"Splitting data with test_size={test_size}, random_state={random_state}")
    
    if stratify_column and stratify_column in df.columns:
        # Create bins for stratification if the column is continuous
        if pd.api.types.is_numeric_dtype(df[stratify_column]):
            n_bins = min(10, len(df))
            bins = pd.qcut(df[stratify_column], q=n_bins, duplicates='drop')
            stratify_col = bins
        else:
            stratify_col = df[stratify_column]
        
        train_df, test_df = train_test_split(
            df, 
            test_size=test_size, 
            random_state=random_state, 
            stratify=stratify_col
        )
        logger.info(f"Stratified split by '{stratify_column}'")
    else:
        train_df, test_df = train_test_split(
            df, 
            test_size=test_size, 
            random_state=random_state
        )
        logger.info("Random split (no stratification)")
    
    log_pipeline_event(f"Data split: train={len(train_df)}, test={len(test_df)}")
    return train_df, test_df

def save_processed_data(df: pd.DataFrame, 
                       output_path: str = "data/processed/features.csv",
                       train_df: Optional[pd.DataFrame] = None,
                       test_df: Optional[pd.DataFrame] = None) -> None:
    """
    Save processed data to CSV and optionally save train/test splits.
    
    Args:
        df: Processed DataFrame to save
        output_path: Path for the main features CSV
        train_df: Optional training split
        test_df: Optional test split
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main features file
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed features to {output_path} ({len(df)} rows)")
    
    # Save train/test splits if provided
    if train_df is not None:
        train_path = str(output_path).replace('.csv', '_train.csv')
        train_df.to_csv(train_path, index=False)
        logger.info(f"Saved training data to {train_path} ({len(train_df)} rows)")
    
    if test_df is not None:
        test_path = str(output_path).replace('.csv', '_test.csv')
        test_df.to_csv(test_path, index=False)
        logger.info(f"Saved test data to {test_path} ({len(test_df)} rows)")
    
    # Log data statistics
    log_pipeline_event(f"Data statistics: {df.shape[0]} samples, {df.shape[1]} features")
    if 'decomposition_energy' in df.columns:
        de_stats = df['decomposition_energy'].describe()
        logger.info(f"Decomposition energy stats: min={de_stats['min']:.4f}, "
                   f"max={de_stats['max']:.4f}, mean={de_stats['mean']:.4f}")

def main():
    """Main preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    
    try:
        # Load raw data
        raw_df = load_raw_data()
        logger.info(f"Loaded {len(raw_df)} raw entries")
        
        # Clean data
        cleaned_df, excluded_count = clean_data(raw_df)
        logger.info(f"Cleaned data: {len(cleaned_df)} entries ({excluded_count} excluded)")
        
        if len(cleaned_df) == 0:
            raise ValueError("No valid entries remaining after cleaning")
        
        # Validate schema
        if not validate_schema(cleaned_df):
            raise ValueError("Schema validation failed")
        
        # Split data
        train_df, test_df = split_data(cleaned_df)
        
        # Save processed data
        save_processed_data(
            cleaned_df,
            output_path="data/processed/features.csv",
            train_df=train_df,
            test_df=test_df
        )
        
        # Verify no nulls in critical columns
        for col in CRITICAL_COLUMNS:
            null_count = cleaned_df[col].isna().sum()
            if null_count > 0:
                raise ValueError(f"Critical column '{col}' has {null_count} null values")
        
        logger.info("Preprocessing completed successfully")
        log_pipeline_event("Preprocessing pipeline completed")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        log_exclusion_reason("Pipeline failure", str(e))
        raise

if __name__ == "__main__":
    main()