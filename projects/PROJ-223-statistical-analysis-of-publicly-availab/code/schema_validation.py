import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SchemaValidationError(Exception):
    pass

def validate_raw_fars(df: pd.DataFrame) -> None:
    """
    Validate the raw FARS dataset schema.
    """
    required_columns = ['ST', 'COUNTY', 'LAT', 'LON', 'YEAR', 'MONTH', 'DAY', 'TIME']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise SchemaValidationError(f"FARS dataset missing required columns: {missing_columns}")
    logger.info("FARS dataset schema validated successfully.")

def validate_raw_noaa(df: pd.DataFrame) -> None:
    """
    Validate the raw NOAA dataset schema.
    """
    required_columns = ['DATE', 'STATION', 'ELEMENT', 'VALUE']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise SchemaValidationError(f"NOAA dataset missing required columns: {missing_columns}")
    logger.info("NOAA dataset schema validated successfully.")

def validate_merged_dataset(df: pd.DataFrame) -> None:
    """
    Validate the merged dataset schema.
    """
    # Check for at least some key columns from both datasets
    required_columns = ['ST', 'COUNTY', 'LAT', 'LON', 'YEAR', 'MONTH', 'DAY']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise SchemaValidationError(f"Merged dataset missing required columns: {missing_columns}")
    logger.info("Merged dataset schema validated successfully.")

def validate_schema(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Generic schema validation.
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    return len(missing_columns) == 0, missing_columns

def get_missing_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
    """
    Get list of missing columns in a DataFrame.
    """
    return [col for col in required_columns if col not in df.columns]

def get_null_counts(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get null counts for each column in a DataFrame.
    """
    return df.isnull().sum().to_dict()
