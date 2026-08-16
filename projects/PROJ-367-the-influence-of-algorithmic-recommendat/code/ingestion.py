"""
Data ingestion and validation module.
Implements FR-007 and data loading logic.
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Union
from datasets import load_dataset
from huggingface_hub import hf_hub_download
import ast

logger = logging.getLogger(__name__)

class DataSchemaError(Exception):
    """Raised when the dataset schema does not match requirements."""
    pass

def load_data_from_hf(dataset_id: str, split: str = "train") -> pd.DataFrame:
    """
    Load data from a HuggingFace dataset.
    
    Args:
        dataset_id: HuggingFace dataset identifier.
        split: Dataset split to load.
    
    Returns:
        DataFrame with the data.
    
    Raises:
        Exception: If the dataset cannot be loaded.
    """
    try:
        logger.info(f"Loading dataset {dataset_id} split {split} from HuggingFace...")
        ds = load_dataset(dataset_id, split=split)
        df = ds.to_pandas()
        logger.info(f"Loaded {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        raise

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that the DataFrame has the required columns.
    Raises DataSchemaError if columns are missing.
    
    Args:
        df: DataFrame to validate.
    
    Raises:
        DataSchemaError: If required columns are missing.
    """
    required_cols = ["recommended_categories", "enrolled_categories"]
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        raise DataSchemaError(
            f"Required columns {missing} missing. Dataset does not support the specified experimental design."
        )

def ingest_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataframe:
    1. Validate schema.
    2. Parse category lists (if stored as strings).
    3. Exclude rows with empty enrollments.
    
    Args:
        df: Raw DataFrame.
    
    Returns:
        Cleaned DataFrame.
    """
    validate_schema(df)
    
    initial_count = len(df)
    
    # Ensure columns are lists if they are strings (e.g. "[A, B]")
    for col in ["recommended_categories", "enrolled_categories"]:
        if df[col].dtype == 'object':
            def safe_eval(x):
                if isinstance(x, list):
                    return x
                if isinstance(x, str):
                    try:
                        return ast.literal_eval(x)
                    except:
                        return []
                return []
            
            df[col] = df[col].apply(safe_eval)
    
    # Exclude rows with empty enrollments
    before_filter = len(df)
    df = df[df["enrolled_categories"].apply(lambda x: len(x) > 0)]
    after_filter = len(df)
    
    if before_filter != after_filter:
        logger.warning(f"Excluded {before_filter - after_filter} rows with empty enrollments.")
    
    logger.info(f"Cleaned dataset: {len(df)} rows (started with {initial_count}).")
    return df

def load_project_data() -> pd.DataFrame:
    """
    Main entry point to load data for the project.
    Loads from the verified HuggingFace source 'lucasegatto/course-recommendations'.
    
    Returns:
        Cleaned DataFrame.
    
    Raises:
        Exception: If the real dataset cannot be loaded.
    """
    # Verified Real Data Source: lucasegatto/course-recommendations
    # This dataset contains course recommendation and enrollment data suitable for the study.
    ds_id = "lucasegatto/course-recommendations"
    
    try:
        df = load_data_from_hf(ds_id)
        return ingest_and_clean(df)
    except Exception as e:
        logger.critical(f"CRITICAL: Could not load real data from {ds_id}. {e}")
        raise