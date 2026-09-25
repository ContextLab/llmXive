import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from datasets import load_dataset
import pyarrow.parquet as pq
import json
from datetime import datetime

from config import ProjectConfig

logger = logging.getLogger(__name__)

class DataSchemaError(Exception):
    """Exception raised when the dataset schema does not match requirements."""
    pass

class DataAvailabilityError(Exception):
    """Exception raised when real data is not found or inaccessible."""
    pass

def validate_schema(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> None:
    """
    Validates that the DataFrame contains the required columns.
    
    Args:
        df: The DataFrame to validate.
        required_columns: List of required column names. Defaults to standard requirements.
        
    Raises:
        DataSchemaError: If required columns are missing.
    """
    if required_columns is None:
        required_columns = ['recommended_categories', 'enrolled_categories']
        
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise DataSchemaError(
            f"Required columns {list(missing)} missing. Dataset does not support the specified experimental design."
        )
    logger.info(f"Schema validation passed. Found columns: {list(df.columns)}")

def load_data_from_hf(dataset_id: str, split: str = 'train') -> pd.DataFrame:
    """
    Loads a dataset from Hugging Face Hub.
    
    Args:
        dataset_id: The Hugging Face dataset ID.
        split: The split to load.
        
    Returns:
        The loaded DataFrame.
    """
    logger.info(f"Loading dataset {dataset_id} from Hugging Face...")
    try:
        dataset = load_dataset(dataset_id, split=split)
        df = dataset.to_pandas()
        logger.info(f"Loaded {len(df)} rows from {dataset_id}")
        return df
    except Exception as e:
        raise DataAvailabilityError(f"Failed to load dataset {dataset_id}: {e}")

def load_project_data(config: ProjectConfig) -> pd.DataFrame:
    """
    Loads data from the project's raw data directory.
    
    Args:
        config: The project configuration.
        
    Returns:
        The loaded DataFrame.
    """
    raw_path = config.paths['data_raw']
    verified_path = raw_path / 'verified_dataset.csv'
    
    if not verified_path.exists():
        raise FileNotFoundError(f"Verified dataset not found at {verified_path}. Run T015 first.")
        
    logger.info(f"Loading data from {verified_path}")
    df = pd.read_csv(verified_path)
    return df

def ingest_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs ingestion and cleaning logic:
    1. Validates schema.
    2. Parses category lists (handles string representations of lists).
    3. Excludes rows with empty enrollments.
    4. Adds 'is_valid' flag.
    
    Args:
        df: The raw DataFrame.
        
    Returns:
        The cleaned DataFrame.
    """
    # Validate schema first
    validate_schema(df)
    
    # Ensure categories are parsed as lists if they are strings
    # Handle cases where the CSV might have stored lists as strings like "['A', 'B']"
    def safe_parse_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            val = val.strip()
            if val.startswith('[') and val.endswith(']'):
                # Simple parsing for stringified lists, removing quotes
                try:
                    # Replace single quotes with double for JSON compatibility if needed
                    # Or use ast.literal_eval if available, but standard eval is risky
                    # Let's try a simple split if it looks like a simple CSV inside brackets
                    if "'" in val:
                        inner = val[1:-1].replace("'", "").strip()
                    elif '"' in val:
                        inner = val[1:-1].replace('"', "").strip()
                    else:
                        inner = val[1:-1]
                        
                    if not inner:
                        return []
                    return [x.strip() for x in inner.split(',') if x.strip()]
                except Exception:
                    return []
            return [val] if val else []
        return []

    # Apply parsing if necessary (check if first row is string or list)
    if df['recommended_categories'].iloc[0] is not None and isinstance(df['recommended_categories'].iloc[0], str):
        logger.info("Parsing stringified category lists...")
        df['recommended_categories'] = df['recommended_categories'].apply(safe_parse_list)
        df['enrolled_categories'] = df['enrolled_categories'].apply(safe_parse_list)
    
    # Identify rows with empty enrollments
    empty_enrollment_mask = df['enrolled_categories'].apply(lambda x: len(x) == 0)
    count_empty = empty_enrollment_mask.sum()
    
    if count_empty > 0:
        logger.warning(f"Excluding {count_empty} rows with empty enrolled_categories.")
    
    # Create is_valid flag
    df['is_valid'] = ~empty_enrollment_mask
    
    # Filter out invalid rows
    cleaned_df = df[df['is_valid']].copy()
    
    # Ensure user_id and session_id exist, create defaults if missing
    if 'user_id' not in cleaned_df.columns:
        cleaned_df['user_id'] = range(len(cleaned_df))
    if 'session_id' not in cleaned_df.columns:
        cleaned_df['session_id'] = range(len(cleaned_df))
        
    # Select and order final schema
    final_columns = ['user_id', 'session_id', 'recommended_categories', 'enrolled_categories', 'is_valid']
    # Ensure all exist before selecting
    available_columns = [c for c in final_columns if c in cleaned_df.columns]
    cleaned_df = cleaned_df[available_columns]
    
    logger.info(f"Ingestion complete. {len(cleaned_df)} valid rows remaining.")
    return cleaned_df

def ingest_and_save(config: ProjectConfig, input_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Main entry point for the ingestion pipeline.
    Loads data, validates, cleans, and saves to Parquet.
    
    Args:
        config: Project configuration.
        input_path: Optional path to input file. If None, uses config's raw data path.
        
    Returns:
        Path to the output Parquet file.
    """
    processed_dir = Path(config.paths['data_processed'])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = processed_dir / 'cleaned_data.parquet'
    
    # Load data
    if input_path:
        input_path = Path(input_path)
        if input_path.suffix == '.csv':
            df = pd.read_csv(input_path)
        elif input_path.suffix == '.parquet':
            df = pd.read_parquet(input_path)
        else:
            raise ValueError(f"Unsupported input format: {input_path.suffix}")
    else:
        df = load_project_data(config)
    
    # Process
    cleaned_df = ingest_and_clean(df)
    
    # Save to Parquet
    cleaned_df.to_parquet(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")
    
    return output_path