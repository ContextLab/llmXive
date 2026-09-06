import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Union
from datasets import load_dataset

logger = logging.getLogger(__name__)

class DataSchemaError(Exception):
    """Raised when required data columns are missing or schema is invalid."""
    pass

def load_data_from_hf(dataset_id: str, split: str = "train") -> pd.DataFrame:
    """
    Load data from Hugging Face datasets.
    
    Args:
        dataset_id: Hugging Face dataset identifier
        split: Dataset split to load (default: "train")
        
    Returns:
        DataFrame containing the dataset
        
    Raises:
        DataSchemaError: If dataset cannot be loaded or is empty
    """
    try:
        logger.info(f"Loading dataset {dataset_id} from Hugging Face...")
        dataset = load_dataset(dataset_id, split=split)
        df = dataset.to_pandas()
        
        if df.empty:
            raise DataSchemaError("Dataset loaded from Hugging Face is empty.")
        
        logger.info(f"Successfully loaded {len(df)} rows from {dataset_id}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {str(e)}")
        raise DataSchemaError(f"Failed to load dataset {dataset_id}: {str(e)}")

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that the DataFrame contains required columns for the analysis.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        DataSchemaError: If required columns are missing
    """
    required_columns = ["recommended_categories", "enrolled_categories"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_msg = f"Required columns {missing_columns} missing. Dataset does not support the specified experimental design."
        logger.error(error_msg)
        raise DataSchemaError(error_msg)
    
    logger.info("Schema validation passed: all required columns present.")

def ingest_and_clean(
    df: pd.DataFrame, 
    min_categories: int = 1,
    max_missing_threshold: float = 0.5
) -> pd.DataFrame:
    """
    Ingest and clean data by handling missing values and filtering invalid rows.
    
    This function implements robust error handling for missing data:
    1. Validates schema
    2. Handles missing values in critical columns
    3. Filters out rows with empty enrollments
    4. Logs detailed statistics about excluded sessions
    
    Args:
        df: Raw DataFrame to process
        min_categories: Minimum number of categories required in a list
        max_missing_threshold: Maximum proportion of missing values allowed
        
    Returns:
        Cleaned DataFrame with valid sessions only
        
    Raises:
        DataSchemaError: If schema validation fails or data quality is too poor
    """
    logger.info("Starting data ingestion and cleaning process...")
    
    # Validate schema first
    validate_schema(df)
    
    initial_count = len(df)
    logger.info(f"Initial dataset size: {initial_count} rows")
    
    # Track exclusion reasons
    exclusion_stats = {
        "empty_enrollments": 0,
        "missing_recommended": 0,
        "missing_enrolled": 0,
        "invalid_category_lists": 0,
        "total_excluded": 0
    }
    
    # Handle missing values in critical columns
    # Check for missing recommended_categories
    if df["recommended_categories"].isna().any():
        missing_rec = df["recommended_categories"].isna().sum()
        logger.warning(f"Found {missing_rec} rows with missing 'recommended_categories'")
        exclusion_stats["missing_recommended"] = missing_rec
    
    # Check for missing enrolled_categories
    if df["enrolled_categories"].isna().any():
        missing_enr = df["enrolled_categories"].isna().sum()
        logger.warning(f"Found {missing_enr} rows with missing 'enrolled_categories'")
        exclusion_stats["missing_enrolled"] = missing_enr
    
    # Drop rows with any missing critical values
    df_clean = df.dropna(subset=["recommended_categories", "enrolled_categories"])
    dropped_na = initial_count - len(df_clean)
    if dropped_na > 0:
        logger.info(f"Dropped {dropped_na} rows due to missing critical values")
    
    # Filter out rows with empty category lists
    # Convert to string if necessary and check for empty lists/strings
    def is_valid_category_list(val):
        """Check if a value is a valid non-empty category list."""
        if pd.isna(val):
            return False
        
        # Handle string representations of lists
        if isinstance(val, str):
            val = val.strip()
            if val == "" or val == "[]" or val == "nan":
                return False
            # Try to parse as list if it looks like one
            if val.startswith("[") and val.endswith("]"):
                try:
                    # Simple check: contains at least one non-whitespace character
                    inner = val[1:-1].strip()
                    return len(inner) > 0 and inner != "nan"
                except:
                    return False
            return len(val) > 0
        
        # Handle actual list objects
        if isinstance(val, list):
            return len(val) >= min_categories and all(
                isinstance(item, str) and len(item.strip()) > 0 
                for item in val if item is not None
            )
        
        # Handle numpy arrays
        if isinstance(val, np.ndarray):
            return len(val) >= min_categories and all(
                isinstance(item, str) and len(item.strip()) > 0 
                for item in val if item is not None
            )
        
        return False
    
    # Apply validation
    valid_mask = df_clean["enrolled_categories"].apply(is_valid_category_list)
    invalid_count = (~valid_mask).sum()
    exclusion_stats["invalid_category_lists"] = invalid_count
    
    if invalid_count > 0:
        logger.warning(f"Found {invalid_count} rows with invalid or empty category lists")
    
    # Filter to valid rows
    df_clean = df_clean[valid_mask]
    
    # Additional check for empty enrollments (explicit requirement)
    empty_enrollment_mask = df_clean["enrolled_categories"].apply(
        lambda x: len(x) == 0 if isinstance(x, (list, np.ndarray)) else (
            isinstance(x, str) and (x.strip() == "" or x.strip() == "[]")
        )
    )
    empty_count = empty_enrollment_mask.sum()
    exclusion_stats["empty_enrollments"] = empty_count
    
    if empty_count > 0:
        logger.warning(f"Found {empty_count} rows with empty enrollments - excluding these sessions")
    
    # Final filter
    df_final = df_clean[~empty_enrollment_mask]
    
    # Calculate final statistics
    total_excluded = initial_count - len(df_final)
    exclusion_stats["total_excluded"] = total_excluded
    
    # Log comprehensive summary
    logger.info("=" * 60)
    logger.info("DATA INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Initial rows: {initial_count}")
    logger.info(f"Final valid rows: {len(df_final)}")
    logger.info(f"Total excluded sessions: {total_excluded}")
    logger.info(f"Exclusion breakdown:")
    logger.info(f"  - Missing recommended_categories: {exclusion_stats['missing_recommended']}")
    logger.info(f"  - Missing enrolled_categories: {exclusion_stats['missing_enrolled']}")
    logger.info(f"  - Invalid/empty category lists: {exclusion_stats['invalid_category_lists']}")
    logger.info(f"  - Empty enrollments: {exclusion_stats['empty_enrollments']}")
    logger.info("=" * 60)
    
    if len(df_final) == 0:
        raise DataSchemaError(
            "No valid rows remaining after cleaning. Check data quality and filtering criteria."
        )
    
    if total_excluded > 0:
        logger.info(f"Successfully excluded {total_excluded} invalid sessions. "
                   f"Proceeding with {len(df_final)} valid sessions.")
    
    return df_final.reset_index(drop=True)

def load_project_data(
    dataset_id: str,
    split: str = "train",
    min_categories: int = 1,
    max_missing_threshold: float = 0.5
) -> pd.DataFrame:
    """
    End-to-end data loading and cleaning pipeline.
    
    Combines loading from Hugging Face with validation and cleaning.
    
    Args:
        dataset_id: Hugging Face dataset identifier
        split: Dataset split to load
        min_categories: Minimum categories per list
        max_missing_threshold: Maximum allowed missing value proportion
        
    Returns:
        Cleaned DataFrame ready for analysis
    """
    logger.info(f"Starting full data pipeline for {dataset_id}...")
    
    # Load raw data
    df_raw = load_data_from_hf(dataset_id, split)
    
    # Clean and validate
    df_clean = ingest_and_clean(
        df_raw, 
        min_categories=min_categories,
        max_missing_threshold=max_missing_threshold
    )
    
    logger.info(f"Data pipeline complete. Output shape: {df_clean.shape}")
    return df_clean