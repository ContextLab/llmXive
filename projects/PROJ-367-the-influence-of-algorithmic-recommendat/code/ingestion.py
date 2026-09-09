import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Union
from datasets import load_dataset
import json

logger = logging.getLogger(__name__)

class DataSchemaError(Exception):
    """Custom exception for data schema validation failures."""
    pass

def load_data_from_hf(dataset_name: str, split: str = "train") -> pd.DataFrame:
    """
    Load data from Hugging Face datasets.
    
    Args:
        dataset_name: Name of the dataset on Hugging Face
        split: Which split to load (default: "train")
        
    Returns:
        pd.DataFrame: Loaded dataset as a DataFrame
    """
    try:
        dataset = load_dataset(dataset_name, split=split)
        df = dataset.to_pandas()
        logger.info(f"Loaded {len(df)} rows from {dataset_name}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise

def validate_schema(df: pd.DataFrame, required_columns: list = None) -> None:
    """
    Validate that the DataFrame has the required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Raises:
        DataSchemaError: If required columns are missing
    """
    if required_columns is None:
        required_columns = ["recommended_categories", "enrolled_categories"]
        
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise DataSchemaError(
            f"Required columns {missing} missing. Dataset does not support the specified experimental design."
        )

def ingest_and_clean(
    df: pd.DataFrame,
    exclude_empty_enrollments: bool = True,
    log_warnings: bool = True
) -> pd.DataFrame:
    """
    Ingest and clean data, handling missing values and empty enrollments.
    
    Args:
        df: Raw DataFrame with recommended_categories and enrolled_categories
        exclude_empty_enrollments: If True, exclude rows with empty enrolled_categories
        log_warnings: If True, log warnings about excluded rows
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with appropriate handling of missing data
        
    Raises:
        DataSchemaError: If schema validation fails
    """
    # Validate schema first
    validate_schema(df)
    
    cleaned_df = df.copy()
    excluded_count = 0
    
    # Handle empty enrolled_categories
    if exclude_empty_enrollments:
        # Identify rows with empty or NaN enrolled_categories
        if 'enrolled_categories' in cleaned_df.columns:
            # Convert to string and check for empty/NaN
            empty_mask = cleaned_df['enrolled_categories'].isna() | (
                cleaned_df['enrolled_categories'].astype(str).str.strip() == ''
            )
            
            excluded_count = empty_mask.sum()
            
            if excluded_count > 0:
                if log_warnings:
                    logger.warning(
                        f"Excluded {excluded_count} sessions with empty enrolled_categories. "
                        f"These rows will be dropped from analysis."
                    )
                
                # Drop rows with empty enrollments
                cleaned_df = cleaned_df[~empty_mask].reset_index(drop=True)
    else:
        # If not excluding, we need to handle empty values for metric calculation
        # Mark them appropriately for downstream processing
        if 'enrolled_categories' in cleaned_df.columns:
            empty_mask = cleaned_df['enrolled_categories'].isna() | (
                cleaned_df['enrolled_categories'].astype(str).str.strip() == ''
            )
            excluded_count = empty_mask.sum()
            
            if excluded_count > 0 and log_warnings:
                logger.warning(
                    f"Found {excluded_count} sessions with empty enrolled_categories. "
                    f"learner_diversity_score will be set to null for these rows."
                )
    
    # Clean recommended_categories (handle NaN)
    if 'recommended_categories' in cleaned_df.columns:
        cleaned_df['recommended_categories'] = cleaned_df['recommended_categories'].fillna('')
        
    # Clean enrolled_categories (handle NaN)
    if 'enrolled_categories' in cleaned_df.columns:
        cleaned_df['enrolled_categories'] = cleaned_df['enrolled_categories'].fillna('')
    
    logger.info(f"Ingestion complete. Original rows: {len(df)}, Cleaned rows: {len(cleaned_df)}")
    logger.info(f"Excluded sessions count: {excluded_count}")
    
    return cleaned_df

def load_project_data(
    data_path: Optional[Union[str, Path]] = None,
    dataset_name: Optional[str] = None,
    exclude_empty_enrollments: bool = True
) -> pd.DataFrame:
    """
    Load project data from either a local file or Hugging Face dataset.
    
    Args:
        data_path: Path to local CSV/Parquet file
        dataset_name: Name of Hugging Face dataset to load
        exclude_empty_enrollments: Whether to exclude rows with empty enrollments
        
    Returns:
        pd.DataFrame: Cleaned and validated DataFrame
    """
    df = None
    
    if data_path:
        path = Path(data_path)
        if path.suffix == '.csv':
            df = pd.read_csv(path)
        elif path.suffix == '.parquet':
            df = pd.read_parquet(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        logger.info(f"Loaded data from {data_path}")
    elif dataset_name:
        df = load_data_from_hf(dataset_name)
    else:
        raise ValueError("Either data_path or dataset_name must be provided")
    
    # Clean the data
    cleaned_df = ingest_and_clean(
        df,
        exclude_empty_enrollments=exclude_empty_enrollments,
        log_warnings=True
    )
    
    return cleaned_df
