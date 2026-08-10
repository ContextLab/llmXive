import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from src.utils.logger import get_module_logger
from src.exceptions import InsufficientDataError

logger = get_module_logger(__name__)

def calculate_row_hash(row: pd.Series) -> str:
    """Calculate a hash for a row to detect duplicates."""
    # Convert row to a string representation, handling NaNs
    row_str = str(row.tolist())
    return hashlib.sha256(row_str.encode()).hexdigest()

def merge_datasets(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """Merge multiple dataframes into a single dataframe."""
    if not dataframes:
        raise ValueError("No dataframes provided for merging.")
    
    # Concatenate all dataframes
    merged_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Merged {len(dataframes)} datasets. Total rows: {len(merged_df)}")
    return merged_df

def validate_traceability(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Validate that all rows have non-null 'source_name' and 'source_id'.
    
    Args:
        df: The merged dataframe to validate.
        
    Returns:
        A tuple containing:
            - The validated dataframe (with rows lacking traceability filtered out)
            - The count of rows that were filtered out
    
    Raises:
        SystemExit: If the resulting dataset has fewer than 150 rows.
    """
    logger.info("Validating traceability of merged data...")
    
    # Check for required columns
    if 'source_name' not in df.columns or 'source_id' not in df.columns:
        missing_cols = []
        if 'source_name' not in df.columns:
            missing_cols.append('source_name')
        if 'source_id' not in df.columns:
            missing_cols.append('source_id')
        raise InsufficientDataError(f"Missing required traceability columns: {missing_cols}")
    
    # Filter out rows with missing source_name or source_id
    initial_count = len(df)
    valid_mask = df['source_name'].notna() & df['source_id'].notna()
    filtered_df = df[valid_mask].copy()
    filtered_count = len(filtered_df)
    removed_count = initial_count - filtered_count
    
    if removed_count > 0:
        logger.warning(f"Filtered out {removed_count} rows missing traceability metadata (source_name or source_id).")
    
    if filtered_count < 150:
        error_msg = f"Merged dataset size {filtered_count} < 150 experiments (minimum viable) per spec SC-004"
        logger.error(error_msg)
        raise SystemExit(1)
    
    logger.info(f"Traceability validation complete. {filtered_count} valid rows retained.")
    return filtered_df, removed_count

def process_flagged_entries(df: pd.DataFrame, flagged_entries: List[Dict]) -> pd.DataFrame:
    """
    Process flagged entries and update the merged dataframe.
    
    Args:
        df: The merged dataframe.
        flagged_entries: List of flagged entries to process.
        
    Returns:
        The updated dataframe.
    """
    logger.info(f"Processing {len(flagged_entries)} flagged entries...")
    # Implementation would go here to process flagged entries
    # For now, we just return the dataframe as is
    return df

def run_merge_pipeline(raw_data_paths: List[str], flagged_data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Run the full merge pipeline: load, merge, validate traceability, and process flagged entries.
    
    Args:
        raw_data_paths: List of paths to raw data files (JSON/Parquet).
        flagged_data_path: Optional path to flagged entries file.
        
    Returns:
        The final merged and validated dataframe.
    """
    dataframes = []
    for path in raw_data_paths:
        logger.info(f"Loading data from {path}...")
        if path.endswith('.json'):
            df = pd.read_json(path)
        elif path.endswith('.parquet'):
            df = pd.read_parquet(path)
        else:
            raise ValueError(f"Unsupported file format: {path}")
        dataframes.append(df)
    
    # Merge datasets
    merged_df = merge_datasets(dataframes)
    
    # Validate traceability
    validated_df, removed_count = validate_traceability(merged_df)
    
    # Process flagged entries if provided
    if flagged_data_path and Path(flagged_data_path).exists():
        with open(flagged_data_path, 'r') as f:
            flagged_entries = json.load(f)
        validated_df = process_flagged_entries(validated_df, flagged_entries)
    
    return validated_df