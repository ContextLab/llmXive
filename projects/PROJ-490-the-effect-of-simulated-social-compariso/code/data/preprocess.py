import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Union
import pandas as pd
import numpy as np

from utils.logger import get_logger, log_execution_start, log_execution_end
from utils.validators import validate_dataframe_schema, load_schema
from data.config import get_config

logger = get_logger(__name__)

def calculate_missing_ratio(df: pd.DataFrame, column: str) -> float:
    """
    Calculate the ratio of missing values for a specific column.

    Args:
        df: Input DataFrame
        column: Column name to check

    Returns:
        Float between 0.0 and 1.0 representing missing ratio
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    return df[column].isna().sum() / len(df)

def _normalize_binary_column(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """
    Normalize a binary column to 0/1 integer representation.
    
    Handles various binary encodings:
    - Strings: 'yes'/'no', 'true'/'false', 'high'/'low', 'treatment'/'control'
    - Mixed case strings
    - Numeric 0/1 or 1/0 (already normalized)
    
    Args:
        df: Input DataFrame
        col_name: Name of the column to normalize
        
    Returns:
        DataFrame with normalized column
    """
    df = df.copy()
    
    if col_name not in df.columns:
        logger.warning(f"Column '{col_name}' not found in DataFrame, skipping normalization")
        return df
    
    series = df[col_name]
    
    # Check if already numeric 0/1
    if pd.api.types.is_numeric_dtype(series):
        unique_vals = series.unique()
        if set(unique_vals).issubset({0, 1, np.nan}):
            logger.info(f"Column '{col_name}' already normalized to 0/1")
            return df
        elif set(unique_vals).issubset({0, 1, 2, np.nan}):
            # Might be multi-class, check if it's actually binary encoded oddly
            logger.warning(f"Column '{col_name}' has numeric values {unique_vals}, not strictly 0/1")
            return df
    
    # Convert to string for uniform processing
    str_series = series.astype(str).str.lower().str.strip()
    
    # Define mapping for common binary representations
    # Format: (positive_value, negative_value)
    binary_mappings = [
        (['yes', 'true', 't', '1', 'high', 'treatment', 'high_avatar', 'social'], 
         ['no', 'false', 'f', '0', 'low', 'control', 'low_avatar', 'non_social']),
        (['high', 'treatment'], ['low', 'control']),
        (['1', 'true', 'yes'], ['0', 'false', 'no']),
    ]
    
    # Try to find a mapping that fits the data
    unique_lower = set(str_series.dropna().unique())
    
    normalized_map = {}
    found_mapping = False
    
    for pos_vals, neg_vals in binary_mappings:
        pos_set = set(pos_vals)
        neg_set = set(neg_vals)
        
        # Check if all unique values (excluding nan) are in either pos or neg sets
        if unique_lower.issubset(pos_set | neg_set):
            # Found a valid mapping
            for val in pos_vals:
                if val in unique_lower:
                    normalized_map[val] = 1
            for val in neg_vals:
                if val in unique_lower:
                    normalized_map[val] = 0
            found_mapping = True
            logger.info(f"Applied binary mapping to '{col_name}': {unique_lower} -> 0/1")
            break
    
    if not found_mapping:
        # If we can't map it, check if it's already 0/1 numerically (handled above)
        # or if it has exactly 2 unique non-null values that we can map arbitrarily
        if len(unique_lower) == 2:
            vals = sorted(list(unique_lower))
            normalized_map[vals[0]] = 0
            normalized_map[vals[1]] = 1
            logger.info(f"Arbitrarily mapped binary values for '{col_name}': {vals} -> 0/1")
            found_mapping = True
        else:
            logger.error(f"Cannot normalize column '{col_name}' to binary. Unique values: {unique_lower}")
            raise ValueError(f"Column '{col_name}' cannot be normalized to binary 0/1. "
                           f"Unique values found: {unique_lower}")
    
    # Apply mapping
    def map_val(x):
        if pd.isna(x):
            return np.nan
        s = str(x).lower().strip()
        return normalized_map.get(s, np.nan)
    
    df[col_name] = str_series.map(map_val).astype('Int64')
    
    return df

def preprocess_data(
    df: pd.DataFrame, 
    config: Optional[dict] = None,
    schema_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Main preprocessing pipeline for the analysis.
    
    Steps:
    1. Validate required columns exist
    2. Handle missing data (delegation to T016 logic if needed)
    3. Normalize binary variables (avatar_condition)
    4. Ensure numeric types for analysis variables
    
    Args:
        df: Input DataFrame from raw data
        config: Configuration dictionary (optional, uses global config if None)
        schema_path: Path to validation schema (optional)
        
    Returns:
        Preprocessed DataFrame ready for ANCOVA
    """
    if config is None:
        config = get_config()
    
    logger.info("Starting data preprocessing")
    
    # 1. Validate required columns
    required_cols = [
        'avatar_condition', 
        'pre_self_esteem', 
        'post_self_esteem', 
        'comparison_tendency'
    ]
    
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # 2. Normalize binary variables
    # Specifically normalize avatar_condition to 0/1
    df = _normalize_binary_column(df, 'avatar_condition')
    
    # 3. Ensure numeric types for analysis variables
    numeric_cols = ['pre_self_esteem', 'post_self_esteem', 'comparison_tendency']
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.info(f"Converting '{col}' to numeric")
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 4. Validate schema if provided
    if schema_path:
        schema = load_schema(schema_path)
        validate_dataframe_schema(df, schema)
        logger.info("Schema validation passed")
    
    logger.info(f"Preprocessing complete. Shape: {df.shape}")
    return df

def run_preprocess(
    input_path: Union[str, Path], 
    output_path: Union[str, Path],
    schema_path: Optional[Union[str, Path]] = None
) -> None:
    """
    CLI-style entry point for preprocessing.
    
    Loads data from input_path, preprocesses it, and saves to output_path.
    
    Args:
        input_path: Path to input CSV/Parquet file
        output_path: Path to save preprocessed CSV
        schema_path: Optional path to schema for validation
    """
    log_execution_start("run_preprocess", {"input": str(input_path), "output": str(output_path)})
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    if input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    elif input_path.suffix in ['.parquet', '.pq']:
        df = pd.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")
    
    logger.info(f"Loaded {len(df)} rows")
    
    # Preprocess
    config = get_config()
    df_clean = preprocess_data(df, config=config, schema_path=schema_path)
    
    # Save
    logger.info(f"Saving preprocessed data to {output_path}")
    df_clean.to_csv(output_path, index=False)
    
    log_execution_end("run_preprocess", {"rows_processed": len(df_clean)})
    
    logger.info("Preprocessing pipeline completed successfully")